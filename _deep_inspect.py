html = open('demo/static/index.html', encoding='utf-8').read()

# 1. Find ALL occurrences of search-related content
print("=== SEARCH BAR AUDIT ===")
for needle in ['topbar-search', 'Search topics', 'magnifying', 'search icon', 'placeholder="Search']:
    idx = html.find(needle)
    if idx >= 0:
        print(f"FOUND '{needle}' at {idx}: ...{html[idx:idx+80]}...")
    else:
        print(f"NOT FOUND: '{needle}' -- GOOD")

# 2. Find the complete topbar HTML
print("\n=== TOPBAR HTML ===")
tb_start = html.find('<div id="topbar">')
if tb_start >= 0:
    i = tb_start + 4
    depth = 1
    while i < len(html) and depth > 0:
        no = html.find('<div', i)
        nc = html.find('</div>', i)
        if 0 <= no < nc:
            depth += 1; i = no + 4
        elif nc >= 0:
            depth -= 1; i = nc + 6
        else:
            break
    print(html[tb_start:i])
else:
    print("NO TOPBAR FOUND!")

# 3. Check CSS for white-space-causing rules
print("\n=== WHITE SPACE CSS AUDIT ===")
style_start = html.find('<style>')
style_end   = html.find('</style>')
css = html[style_start:style_end]

checks = [
    ('html, body reset', 'html, body'),
    ('margin:0 on body', 'margin:0'),
    ('overflow-x hidden', 'overflow-x'),
    ('background on html/body', 'background:var(--bg)'),
    ('min-height 100vh', 'min-height:100vh'),
    ('body::before z-index:-1', 'z-index: -1'),
    ('duplicate body rule', css.count('body {')  ),
]
for label, check in checks:
    if isinstance(check, int):
        print(f"  {label}: count={check}")
    else:
        present = check in css
        print(f"  {label}: {'YES' if present else 'MISSING'}"),

# 4. Check for any remaining old headers or duplicate topbar
print(f"\n=== DUPLICATE TOPBAR CHECK ===")
count = html.count('id="topbar"')
print(f"  topbar occurrences: {count} (should be 1)")

# 5. Check the HTML doctype and <html> tag
print(f"\n=== HTML ROOT ===")
print(html[:200])

# 6. Find body tag and its classes/styles
body_idx = html.find('<body')
print(f"\n=== BODY TAG ===")
print(html[body_idx:body_idx+100])
