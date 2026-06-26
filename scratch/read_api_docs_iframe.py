import urllib.request
import re

try:
    url = "https://hamyon-api.uz/src_files/saved_resource.html"
    print("Fetching", url)
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    print("HTML length:", len(html))
    
    with open("scratch/saved_resource.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Saved iframe HTML to scratch/saved_resource.html")
    
    # Strip HTML tags
    text = re.sub('<[^<]+?>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    print("Cleaned text (first 2000 chars):")
    print(text[:2000])
except Exception as e:
    print("Error:", e)
