import re

with open("scratch/saved_resource.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for endpoints or simulation forms in the source code
# We look for POST/GET requests in the JS bundle.
# Let's find all URLs or paths
paths = re.findall(r'/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+', html)
interesting_paths = [p for p in set(paths) if any(k in p for k in ["pay", "merchant", "status", "test", "sim", "mock", "confirm"])]
print("Interesting paths found in Vite bundle:")
for p in interesting_paths:
    print("  ->", p)
    
# Let's search for text near 'Simulyator' or 'Tizim' or 'To'lov'
lines = html.split('\n')
for idx, line in enumerate(lines):
    if "simul" in line.lower() or "pay" in line.lower():
        if len(line) < 500:
            print(f"Line {idx}: {line.strip()}")
