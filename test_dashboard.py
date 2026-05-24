import urllib.request
import re

try:
    resp = urllib.request.urlopen('http://127.0.0.1:8420/', timeout=3)
    html = resp.read().decode('utf-8')
    
    print(f'Status: {resp.status}')
    print(f'Content length: {len(html)} bytes')
    
    title = re.search(r'<title>(.*?)</title>', html)
    if title:
        print(f'Title: {title.group(1)}')
    
    links = re.findall(r'href=["\x27](/?[a-zA-Z0-9_/]+)["\x27]', html)
    print(f'Links found: {links}')
    
    # Show structure
    print('--- PREVIEW (first 2000 chars) ---')
    print(html[:2000])
except Exception as e:
    print(f'Error: {e}')