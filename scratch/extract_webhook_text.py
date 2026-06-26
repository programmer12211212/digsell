import re

with open("scratch/saved_resource.html", "r", encoding="utf-8") as f:
    html = f.read()

strings = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'', html)
flat_strings = []
for s in strings:
    val = s[0] or s[1]
    if val and len(val) > 3:
        flat_strings.append(val)

with open("scratch/webhook_texts.txt", "w", encoding="utf-8") as out:
    out.write("--- Webhook/status/karta related texts ---\n")
    for s in flat_strings:
        if any(kw in s.lower() for kw in ["webhook", "karta", "status", "confirm", "timeout"]):
            if len(s) < 300:
                out.write(s + "\n")
                
print("Extracted to scratch/webhook_texts.txt")
