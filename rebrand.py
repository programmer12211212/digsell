import os
import re

def replace_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Site Name and Domain
        content = re.sub(r'Sotdim\.uz', 'Digsell.uz', content, flags=re.IGNORECASE)
        content = re.sub(r'DIGSELL', 'DIGSELL', content)
        content = re.sub(r'digsell', 'digsell', content)
        
        # Contacts (Generic placeholders or specific ones found)
        content = re.sub(r'@Digsell_Help', '@Digsell_Help', content)
        # Note: I'll also add a general contact update in templates manually if needed
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error in {file_path}: {e}")
        return False

root_dir = r"c:\Users\User\Desktop\digsell\platforma (2) (2)\platforma (2)\platforma"
exclude_dirs = {'.venv', '.git', '__pycache__', 'staticfiles', 'media', 'node_modules'}

count = 0
for root, dirs, files in os.walk(root_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith(('.html', '.py', '.js', '.css', '.md', '.txt')):
            path = os.path.join(root, file)
            if replace_in_file(path):
                count += 1

print(f"Processed {count} files.")
