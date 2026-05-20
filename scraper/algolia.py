import requests
import json

url = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries"

params = {
    "x-algolia-application-id": "45BWZJ1SGC",
    "x-algolia-api-key": "NzllNTY5MzJiZGM2OTY2ZTQwMDEzOTNhYWZiZGRjODlhYzVkNjBmOGRjNzJiMWM4ZTU0ZDlhYTZjOTJiMjlhMWFuYWx5dGljc1RhZ3M9eWNkYyZyZXN0cmljdEluZGljZXM9WUNDb21wYW55X3Byb2R1Y3Rpb24lMkNZQ0NvbXBhbnlfQnlfTGF1bmNoX0RhdGVfcHJvZHVjdGlvbiZ0YWdGaWx0ZXJzPSU1QiUyMnljZGNfcHVibGljJTIyJTVE",  # paste yours here
}


all_companies = []
slugs = []
seen_slugs = set()
page = 0
batches = {
    "Fall 2026": 1,
    "Summer 2026": 3,
    "Spring 2026": 149,
    "Winter 2026": 199,

    "Fall 2025": 148,
    "Summer 2025": 167,
    "Spring 2025": 144,
    "Winter 2025": 168,

    "Fall 2024": 4,
    "Summer 2024": 248,
    "Winter 2024": 294,

    "Summer 2023": 220,
    "Winter 2023": 275,

    "Summer 2022": 234,
    "Winter 2022": 399,

    "Summer 2021": 391,
    "Winter 2021": 336,

    "Summer 2020": 208,
    "Winter 2020": 229,

    "Summer 2019": 176,
    "Winter 2019": 195,

    "Summer 2018": 131,
    "Winter 2018": 146,

    "Summer 2017": 125,
    "Winter 2017": 116,

    "Summer 2016": 102,
    "Winter 2016": 122,

    "Summer 2015": 104,
    "Winter 2015": 111,

    "Summer 2014": 78,
    "Winter 2014": 74,

    "Summer 2013": 52,
    "Winter 2013": 48,

    "Summer 2012": 66,
    "Winter 2012": 60,

    "Summer 2011": 45,
    "Summer 2010": 36,
    "Winter 2010": 27,

    "Summer 2009": 26,
    "Winter 2009": 16,

    "Summer 2008": 22,
    "Winter 2008": 21,

    "Summer 2007": 19,
    "Winter 2007": 13,

    "Summer 2006": 11,
    "Winter 2006": 7,

    "Summer 2005": 9
}

for batch in batches.keys():
    
    payload = {
        "requests": [
            {
                "indexName": "YCCompany_production",
               "params": f'query=&hitsPerPage=1000&page=0&facetFilters=[["batch:{batch}"]]'
            }
        ]
    }
    print("REQUEST:", payload["requests"][0]["params"])

    response = requests.post(url, params=params, json=payload, timeout=20)
    data = response.json()

    hits = data["results"][0]["hits"]

    print("FIRST SLUG:", hits[0].get("slug") if hits else None)

    new_count = 0

    for company in hits:
        slug = company.get("slug")

        if slug and slug not in seen_slugs:
            seen_slugs.add(slug)
            slugs.append(slug)
            all_companies.append(company)
            new_count += 1

    print(f"Batch: {batch} done — new: {new_count} — total: {len(all_companies)}")

    if new_count == 0:
        print("No new companies. Stopping.")
        break

with open("slugs.json", "w", encoding="utf-8") as file:
    json.dump(slugs, file, indent=2)

print(f"Saved {len(all_companies)} companies.")
print("Is Replit there?", "replit" in slugs)