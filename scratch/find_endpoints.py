import re

with open("scratch/saved_resource.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for actual text in the Vite React bundle.
# All messages/text in a built react bundle are typically inside strings.
# Let's write all sentences or strings of characters that look like text to a file.
# We want to find sentences containing "Hamyon", "API", "/payment", "/merchant", "status", etc.

text_lines = []

# Find all double/single quoted strings that might contain text
strings = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'', html)
flat_strings = []
for s in strings:
    val = s[0] or s[1]
    if val and len(val) > 3:
        flat_strings.append(val)

# Filter for interesting ones
for s in flat_strings:
    s_lower = s.lower()
    if any(keyword in s_lower for keyword in ["hamyon", "merchant", "payment", "status", "shop", "api", "create"]):
        if len(s) < 500: # skip huge minified js code
            text_lines.append(s)

with open("scratch/extracted_docs.txt", "w", encoding="utf-8") as out:
    for idx, line in enumerate(text_lines):
        out.write(f"{idx}: {line}\n")

print(f"Extracted {len(text_lines)} interesting strings to scratch/extracted_docs.txt")
