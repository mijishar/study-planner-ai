"""
Final layout fix — add a definitive CSS reset block at the very top of <style>
to override any browser defaults. This is the most robust way to prevent
the white gap regardless of CSS cascade order.
"""
html = open('demo/static/index.html', encoding='utf-8').read()

# Insert a comprehensive reset at the very top of the <style> block
# This will override browser defaults and any conflicting rules
RESET_CSS = """/* ═══════════════════════════════════════════════════
   LAYOUT RESET — prevents white gap above the app
═══════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html {
  margin: 0 !important;
  padding: 0 !important;
  background: #080B14 !important;
  min-height: 100%;
  overflow-x: hidden;
}

body {
  margin: 0 !important;
  padding: 0 !important;
  background: #080B14;
  color: var(--ink, #e8edf8);
  font: 15px/1.5 Inter, system-ui, sans-serif;
  display: flex;
  min-height: 100vh;
  overflow-x: hidden;
}

/* The [data-theme="bright"] background override */
[data-theme="bright"] html,
[data-theme="bright"] body {
  background: #f0f4f8 !important;
}
"""

style_start = html.find('<style>')
if style_start >= 0:
    insert_pos = style_start + len('<style>')
    html = html[:insert_pos] + '\n' + RESET_CSS + html[insert_pos:]
    print("Reset CSS injected at top of <style>")
else:
    print("ERROR: <style> not found!")
    import sys; sys.exit(1)

# Save
open('demo/static/index.html', 'w', encoding='utf-8').write(html)
print(f"Saved. File size: {len(html)}")

# Quick verification
html2 = open('demo/static/index.html', encoding='utf-8').read()
print("Search bar absent:", 'id="topbar-search"' not in html2)
print("HTML margin reset:", 'html {' in html2 and 'margin: 0 !important' in html2)
print("Body margin reset:", 'margin: 0 !important' in html2)
print("Background #080B14:", '#080B14' in html2)
print("Topbar present:", 'id="topbar"' in html2)
print("Settings btn present:", "nav('settings')" in html2)
