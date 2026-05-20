from playwright.async_api import async_playwright
import asyncio
import json

with open("slugs.json", "r", encoding="utf-8") as file:
    slugs = json.load(file)

all_companies = []


def normalize_company(raw: dict) -> dict:
    partner = raw.get("primary_group_partner") or {}

    return {
        "slug": raw.get("slug"),
        "name": raw.get("name"),
        "one_liner": raw.get("one_liner"),
        "description": raw.get("long_description"),
        "website": raw.get("website"),
        "yc": {
            "batch_code": raw.get("batch"),
            "batch_name": raw.get("batch_name"),
            "status": raw.get("ycdc_status"),
            "url": raw.get("ycdc_url"),
        },
        "facts": {
            "founded_year": raw.get("year_founded"),
            "team_size": raw.get("team_size"),
            "location": raw.get("location"),
            "country": raw.get("country"),
        },
        "tags": raw.get("tags") or [],
        "social": {
            "linkedin": raw.get("linkedin_url"),
            "twitter": raw.get("twitter_url"),
            "facebook": raw.get("fb_url"),
            "crunchbase": raw.get("cb_url"),
            "github": raw.get("github_url"),
        },
        "partner": {
            "name": partner.get("full_name"),
            "url": partner.get("url"),
        } if partner else None,
        "founders": [
            {
                "name": f.get("full_name"),
                "title": f.get("title"),
                "bio": f.get("founder_bio"),
                "twitter": f.get("twitter_url"),
                "linkedin": f.get("linkedin_url"),
            }
            for f in (raw.get("founders") or [])
        ],
        "news": [
            {
                "title": n.get("title"),
                "url": n.get("url"),
                "date": n.get("date"),
            }
            for n in (raw.get("newsItems") or [])
        ],
        "photos": [
            p.get("url")
            for p in (raw.get("company_photos") or [])
            if p.get("url")
        ],
        "logo": raw.get("small_logo_url"),
    }


def normalize_page(payload: dict) -> dict:
    return {
        "component": payload.get("component"),
        "props": {
            "company": normalize_company(payload["props"]["company"]),
        },
    }


async def scrape_company(page, slug: str) -> dict | None:
    url = f"https://www.ycombinator.com/companies/{slug}"
    await page.goto(url, wait_until="domcontentloaded", timeout=60_000)

    el = page.locator('[id*="ShowPage-react-component"]').first
    await el.wait_for(state="attached", timeout=60_000)

    datajson = await el.get_attribute("data-page")
    if not datajson:
        print(f"[{slug}] data-page not found")
        return None

    payload = json.loads(datajson)
    return normalize_page(payload)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        for i, slug in enumerate(slugs):
            try:
                record = await scrape_company(page, slug)
                if record:
                    all_companies.append(record)
                    name = record["props"]["company"]["name"]
                    print(f"[{i + 1}/{len(slugs)}] {slug} — {name}")
            except Exception as e:
                print(f"[{slug}] error: {e}")

        await browser.close()

    with open("companies_detail.json", "w", encoding="utf-8") as file:
        json.dump(all_companies, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_companies)} companies to companies_detail.json")


if __name__ == "__main__":
    asyncio.run(main())