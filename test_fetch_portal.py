"""Fetch the portal page and show what a user sees."""
import urllib.request
import re

try:
    r = urllib.request.urlopen('http://localhost:5000/')
    html = r.read().decode()
    
    # Extract headings
    headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html, re.DOTALL)
    print("=== HEADINGS ===")
    for h in headings[:20]:
        clean = re.sub(r'<[^>]+>', '', h).strip()
        if clean:
            print(f"  {clean[:80]}")
    
    # Extract links
    links = re.findall(r'href=["\']([^"\']*)["\']', html)
    print(f"\n=== LINKS ({len(links)} total) ===")
    for l in links[:40]:
        print(f"  {l}")
    
    # Extract nav items
    nav = re.findall(r'<nav[^>]*>(.*?)</nav>', html, re.DOTALL)
    if nav:
        nav_links = re.findall(r'href=["\']([^"\']*)["\'].*?>(.*?)<', nav[0])
        print(f"\n=== NAVIGATION ===")
        for href, text in nav_links:
            print(f"  {text.strip()} -> {href}")
    
    # Show page size
    print(f"\n=== PAGE SIZE: {len(html)} bytes ===")
    
except Exception as e:
    print(f"Error: {e}")