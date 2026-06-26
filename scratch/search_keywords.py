import re

with open("scratch/saved_resource.html", "r", encoding="utf-8") as f:
    html = f.read()

keywords = ["webhook", "callback", "request", "post", "get", "timeout"]
for kw in keywords:
    found = re.findall(rf'[^"\'>]*{kw}[^"\'<]*', html, re.IGNORECASE)
    print(f"Keyword '{kw}' matches: {len(found)}")
    for f in found[:3]:
        cleaned = re.sub(r'\s+', ' ', f).strip()
        print("  ->", cleaned[:150])
