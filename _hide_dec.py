"""
Hide the Strands Decider 2B visible panel from the AI Tutor page.
- Removes the right-column panel div (width:320px) from HTML
- Changes page style from flex-direction:row to column (default)
- Adds a hidden #dec div so JS handleDecisions() still works without errors
- Backend decision-making and all data are fully preserved
"""

html = open('demo/static/index.html', encoding='utf-8').read()

# ── 1. Change AI Tutor page from row layout to column layout ─────────────
old_style = 'id="page-tutor" class="page" style="flex-direction:row;gap:18px;overflow:hidden"'
new_style = 'id="page-tutor" class="page"'
html = html.replace(old_style, new_style)
print("Row layout removed:", old_style not in html)

# ── 2. Find and remove the right-column Decider panel div ────────────────
# The panel starts with:
# <!-- Right: Decider panel -->
# <div style="width:320px;...">

# Find the comment marker
marker = '<!-- Right: Decider panel -->'
marker_idx = html.find(marker)
print(f"Decider panel marker at: {marker_idx}")

if marker_idx >= 0:
    # Find the opening <div after the comment
    div_start = html.find('<div', marker_idx)
    print(f"Panel div starts at: {div_start}")
    print(f"Context: [{html[div_start:div_start+80]}]")
    
    # Count depth to find the matching </div>
    i = div_start + 4
    depth = 1
    while i < len(html) and depth > 0:
        next_open  = html.find('<div', i)
        next_close = html.find('</div>', i)
        if next_open >= 0 and next_open < next_close:
            depth += 1
            i = next_open + 4
        elif next_close >= 0:
            depth -= 1
            i = next_close + 6
        else:
            break
    panel_end = i
    removed_block = html[marker_idx:panel_end]
    print(f"\nRemoving block ({len(removed_block)} chars):")
    print(removed_block[:200])
    print("...")
    
    # Replace with a hidden #dec div so JS still works
    hidden_dec = '\n    <!-- Decider panel hidden from UI; decisions still logged for backend -->\n    <div id="dec" style="display:none" aria-hidden="true"></div>\n'
    html = html[:marker_idx] + hidden_dec + html[panel_end:]
    print("\nPanel removed and hidden #dec inserted")
else:
    print("ERROR: Decider panel marker not found!")

# ── 3. Also remove the wrapping left-column div (the flex:1.1 wrapper) ───
# After removing the right column, the left wrapper is no longer needed
# Change: <div style="flex:1.1;display:flex;flex-direction:column;min-width:0;gap:14px">
# To just: the contents directly (unwrap it)
old_wrap_open  = '<div style="flex:1.1;display:flex;flex-direction:column;min-width:0;gap:14px">'
new_wrap_open  = '<div style="display:flex;flex-direction:column;gap:14px">'
if old_wrap_open in html:
    html = html.replace(old_wrap_open, new_wrap_open, 1)
    print("Left column wrapper updated")
else:
    print("Left column wrapper not found (may already be updated)")

# ── 4. Save ──────────────────────────────────────────────────────────────
open('demo/static/index.html', 'w', encoding='utf-8').write(html)
print(f"\nSaved. File size: {len(html)} chars")

# ── 5. Verify ────────────────────────────────────────────────────────────
print("\n=== Verification ===")
html2 = open('demo/static/index.html', encoding='utf-8').read()
print("Strands Decider 2B heading visible:", 'Strands Decider 2B</h1>' in html2 or ('<h1 style="font-size:16px">Strands Decider 2B' in html2))
print("Tool Routing card present in HTML:", 'Tool Routing' in html2)
print("AWS attribution visible:", 'AWS User Group Madurai' in html2)
print("#dec in DOM (hidden):  ", 'id="dec"' in html2)
print("handleDecisions in JS: ", 'handleDecisions' in html2)
print("flex-direction:row gone:", 'flex-direction:row' not in html2)
