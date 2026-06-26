import urllib.request
import re

try:
    url = "https://hamyon-api.uz"
    print("Fetching", url)
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    print("HTML length:", len(html))
    
    # Save raw html to a file to examine
    with open("scratch/hamyon_home.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Saved HTML to scratch/hamyon_home.html")
    
    # Strip HTML tags using regex
    text = re.sub('<[^<]+?>', '', html)
    # Collapse multiple whitespaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    print("Cleaned text (first 1000 chars):")
    print(text[:1500])
except Exception as e:
    print("Error:", e)
