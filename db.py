import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

with open("companies_detail.json", "r", encoding="utf-8") as file:
    rawjson = json.load(file)

with open("companies.json", "r", encoding="utf-8") as file:
    algolia_companies = json.load(file)

slug_to_algolia = {c["slug"]: c for c in algolia_companies if c.get("slug")}

load_dotenv()

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
supabase: Client = create_client(url, key)

companies = []
company_founders_raw = []
name_history = []
founders_by_key: dict[str, dict] = {}
founder_yc_id = 1
name_history_id = 1
skipped = 0

CHUNK_SIZE = 100


def founder_key(founder: dict) -> str:
    linkedin = (founder.get("linkedin") or "").strip().rstrip("/").lower()
    if linkedin:
        return f"linkedin:{linkedin}"
    return f"name:{(founder.get('name') or '').strip().lower()}"


def empty_to_none(value):
    return value if value else None


def dedupe_company_founders(links: list[dict]) -> list[dict]:
    """One row per (company_id, founder_id); prefer a non-empty title."""
    by_pair: dict[tuple[int, int], dict] = {}
    for link in links:
        key = (link["company_id"], link["founder_id"])
        existing = by_pair.get(key)
        if existing is None or (link.get("title") and not existing.get("title")):
            by_pair[key] = link
    return list(by_pair.values())


def dedupe_name_history(rows: list[dict]) -> list[dict]:
    """One row per (company_id, name)."""
    by_pair: dict[tuple[int, str], dict] = {}
    for row in rows:
        key = (row["company_id"], row["name"])
        by_pair[key] = row
    return list(by_pair.values())


def chunked_upsert(table: str, rows: list[dict], on_conflict: str) -> None:
    total = len(rows)
    for i in range(0, total, CHUNK_SIZE):
        chunk = rows[i : i + CHUNK_SIZE]
        supabase.table(table).upsert(chunk, on_conflict=on_conflict).execute()
        done = min(i + CHUNK_SIZE, total)
        print(f"  {table}: {done}/{total}")


for startup in rawjson:
    company = startup["props"]["company"]
    company_slug = company["slug"]
    algolia = slug_to_algolia.get(company_slug)

    if algolia is None or algolia.get("id") is None:
        skipped += 1
        continue

    yc_id = algolia["id"]
    facts = company.get("facts") or {}

    companies.append({
        "yc_id": yc_id,
        "slug": company_slug,
        "batch_code": company["yc"].get("batch_code"),
        "batch_name": company["yc"].get("batch_name"),
        "name": company["name"],
        "one_liner": company["one_liner"],
        "description": company["description"],
        "website": company["website"],
        "tags": company.get("tags") or [],
        "linkedin": empty_to_none(company["social"].get("linkedin")),
        "crunchbase": empty_to_none(company["social"].get("crunchbase")),
        "twitter": empty_to_none(company["social"].get("twitter")),
        "facebook": empty_to_none(company["social"].get("facebook")),
        "github": empty_to_none(company["social"].get("github")),
        "founded_year": facts.get("founded_year"),
        "team_size": facts.get("team_size"),
        "partner_name": (company.get("partner") or {}).get("name"),
        "status": company["yc"].get("status") or algolia.get("status"),
        "location": facts.get("location"),
        "country": facts.get("country"),
    })

    for former_name in algolia.get("former_names") or []:
        if former_name:
            name_history.append({
                "id": name_history_id,
                "company_id": yc_id,
                "name": former_name,
            })
            name_history_id += 1

    for founder in company.get("founders", []):
        key = founder_key(founder)
        if key not in founders_by_key:
            founders_by_key[key] = {
                "yc_id": founder_yc_id,
                "name": founder["name"],
                "bio": empty_to_none(founder.get("bio")),
                "linkedin": empty_to_none(founder.get("linkedin")),
                "twitter": empty_to_none(founder.get("twitter")),
            }
            founder_yc_id += 1

        company_founders_raw.append({
            "company_id": yc_id,
            "founder_id": founders_by_key[key]["yc_id"],
            "title": founder.get("title"),
            "is_current": True,
        })

founder_rows = list(founders_by_key.values())
company_founders = dedupe_company_founders(company_founders_raw)
name_history = dedupe_name_history(name_history)

if skipped:
    print(f"Skipped {skipped} companies with no Algolia match in companies.json")

dup_links = len(company_founders_raw) - len(company_founders)
if dup_links:
    print(f"Deduped {dup_links} duplicate company-founder links")

if companies:
    print(f"Uploading {len(companies)} companies...")
    chunked_upsert("companies", companies, "yc_id")
    print(f"Successfully processed {len(companies)} companies.")

if founder_rows:
    print(f"Uploading {len(founder_rows)} founders...")
    chunked_upsert("founders", founder_rows, "yc_id")
    print(f"Successfully processed {len(founder_rows)} founders.")

if company_founders:
    print(f"Uploading {len(company_founders)} company-founder links...")
    chunked_upsert("company_founders", company_founders, "company_id,founder_id")
    print(f"Successfully processed {len(company_founders)} company-founder links.")

if name_history:
    print(f"Uploading {len(name_history)} name history rows...")
    chunked_upsert("company_name_history", name_history, "id")
    print(f"Successfully processed {len(name_history)} name history rows.")

print("Done.")
