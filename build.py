import hashlib
import re
import os

def get_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()[:8] # Short 8-character hash is standard

def main():
    # Paths
    root = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(root, "style.css")
    js_path = os.path.join(root, "assets", "js", "common.js")
    
    css_hash = get_md5(css_path)
    js_hash = get_md5(js_path)
    
    print(f"Computed style.css hash: {css_hash}")
    print(f"Computed common.js hash: {js_hash}")
    
    html_files = ["index.html", "links.html", "profiles.html", "404.html"]
    
    # Combined hash of all files to version the Service Worker cache
    combined_hash_obj = hashlib.md5()
    combined_hash_obj.update(css_hash.encode())
    combined_hash_obj.update(js_hash.encode())
    
    # First update HTML files so their updated content is hashed
    for html_file in html_files:
        path = os.path.join(root, html_file)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace hashes in HTML
            content = re.sub(r'style\.css\?v=[a-zA-Z0-9_-]+', f'style.css?v={css_hash}', content)
            content = re.sub(r'common\.js\?v=[a-zA-Z0-9_-]+', f'common.js?v={js_hash}', content)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Re-read to hash the final file state
            with open(path, "rb") as f:
                combined_hash_obj.update(f.read())
            print(f"Updated hashes in {html_file}")
    
    combined_hash = combined_hash_obj.hexdigest()[:8]
    print(f"Combined PWA Cache Version: static-v{combined_hash}")
    
    # Update sw.js
    sw_path = os.path.join(root, "sw.js")
    if os.path.exists(sw_path):
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace cache version
        content = re.sub(r"const STATIC_CACHE = 'static-v[a-zA-Z0-9._-]+';", f"const STATIC_CACHE = 'static-v{combined_hash}';", content)
        # Replace asset hashes
        content = re.sub(r"'/style\.css\?v=[a-zA-Z0-9_-]+'", f"'/style.css?v={css_hash}'", content)
        content = re.sub(r"'/assets/js/common\.js\?v=[a-zA-Z0-9_-]+'", f"'/assets/js/common.js?v={js_hash}'", content)
        
        with open(sw_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated sw.js")

if __name__ == "__main__":
    main()
