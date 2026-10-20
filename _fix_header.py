"""
Fix: remove search bar from topbar, fix white space issues.
"""
import sys

html = open('demo/static/index.html', encoding='utf-8').read()
original = len(html)

changes = []

# ── 1. Remove search bar from topbar HTML ────────────────────────────────
# Replace the full topbar with a slimmer version (only right-side controls)
old_topbar = '''<div id="topbar">
  <div class="topbar-search">
    <span class="topbar-search-icon">🔍</span>
    <input id="topbar-search" type="text" placeholder="Search topics or ask AI…"
           autocomplete="off" onkeydown="if(event.key==='Enter'){nav('tutor');prefill(this.value);this.value='';}">
  </div>
  <div class="topbar-right">
    <button class="topbar-btn" onclick="nav('settings')" title="Settings">⚙️</button>
    <div class="topbar-avatar" onclick="nav('settings')" title="Profile" id="topbar-avatar-display">🎓</div>
  </div>
</div>'''

new_topbar = '''<div id="topbar">
  <div class="topbar-left">
    <span class="topbar-brand">StudyMate AI</span>
  </div>
  <div class="topbar-right">
    <button class="topbar-btn" onclick="nav('settings')" title="Settings">⚙️</button>
    <div class="topbar-avatar" onclick="nav('settings')" title="Profile" id="topbar-avatar-display">🎓</div>
  </div>
</div>'''

if old_topbar in html:
    html = html.replace(old_topbar, new_topbar, 1)
    changes.append('Removed search bar from topbar')
else:
    # Try partial match — find topbar div and replace its content
    tb_start = html.find('<div id="topbar">')
    tb_end   = html.find('</div>', tb_start)
    # find the matching closing div (depth counting)
    i = tb_start + len('<div id="topbar">')
    depth = 1
    while i < len(html) and depth > 0:
        no = html.find('<div', i)
        nc = html.find('</div>', i)
        if no >= 0 and no < nc:
            depth += 1; i = no + 4
        elif nc >= 0:
            depth -= 1; i = nc + 6
        else:
            break
    html = html[:tb_start] + new_topbar + html[i:]
    changes.append('Replaced topbar (fallback method)')

# ── 2. Fix topbar CSS ─────────────────────────────────────────────────────
old_topbar_css = '''/* ── Top bar ── */
#topbar {
  height:56px; display:flex; align-items:center; gap:12px; padding:0 24px;
  background:rgba(13,18,32,.8); backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line); flex-shrink:0;
  position:sticky; top:0; z-index:50;
}
.topbar-search { flex:1; max-width:400px; display:flex; align-items:center; gap:8px;
  background:rgba(31,45,71,.5); border:1px solid var(--line); border-radius:10px; padding:0 12px; }
.topbar-search-icon { color:var(--mute); }
.topbar-search input { background:none; border:none; color:var(--ink); font:inherit; flex:1; padding:10px 0; outline:none; }
.topbar-right { display:flex; align-items:center; gap:8px; margin-left:auto; }
.topbar-btn { background:none; border:none; font-size:18px; cursor:pointer; padding:6px 8px; border-radius:8px; transition:background .15s; }
.topbar-btn:hover { background:var(--raised); }
.topbar-avatar { width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,var(--violet),var(--blue));
  display:flex; align-items:center; justify-content:center; font-size:18px; cursor:pointer;
  transition:transform .15s; border:2px solid rgba(124,58,237,.4); }
.topbar-avatar:hover { transform:scale(1.08); }
#app { margin-left:var(--sidebar-w); flex:1; display:flex; flex-direction:column; min-height:100vh; }
.page { display:none; flex:1; flex-direction:column; padding:20px 24px; gap:16px; overflow-y:auto; }
[data-theme="bright"] #topbar { background:rgba(255,255,255,.9); border-color:#e2e8f0; }
[data-theme="bright"] .topbar-search { background:#f8fafc; border-color:#e2e8f0; }'''

new_topbar_css = '''/* ── Top bar ── */
html, body {
  margin: 0; padding: 0; overflow-x: hidden;
  background: var(--bg);
  min-height: 100vh;
}
#topbar {
  height: 52px; display: flex; align-items: center;
  justify-content: space-between; padding: 0 20px;
  background: rgba(13,18,32,.95); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line); flex-shrink: 0;
  position: sticky; top: 0; z-index: 50;
  margin: 0;
}
.topbar-left { display: flex; align-items: center; }
.topbar-brand { font-size: 14px; font-weight: 700; color: var(--mute); letter-spacing: .02em; }
.topbar-right { display: flex; align-items: center; gap: 8px; }
.topbar-btn { background: none; border: none; font-size: 18px; cursor: pointer; padding: 6px 8px; border-radius: 8px; transition: background .15s; color: var(--mute); }
.topbar-btn:hover { background: var(--raised); color: var(--ink); }
.topbar-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, var(--violet), var(--blue));
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; cursor: pointer; transition: transform .15s;
  border: 2px solid rgba(124,58,237,.4);
}
.topbar-avatar:hover { transform: scale(1.08); }
#app {
  margin-left: var(--sidebar-w); flex: 1;
  display: flex; flex-direction: column;
  min-height: 100vh; background: var(--bg);
}
.page {
  display: none; flex: 1; flex-direction: column;
  padding: 20px 24px; gap: 16px; overflow-y: auto;
  background: transparent;
}
[data-theme="bright"] #topbar { background: rgba(255,255,255,.95); border-color: #e2e8f0; }
[data-theme="bright"] .topbar-brand { color: #64748b; }'''

if old_topbar_css in html:
    html = html.replace(old_topbar_css, new_topbar_css, 1)
    changes.append('Replaced topbar CSS (removed search styles, fixed white space)')
else:
    # Try to find #topbar CSS block and replace just the search parts
    # Add the html/body reset before existing #topbar rule
    html = html.replace(
        '#topbar {\n  height:56px;',
        'html, body { margin:0; padding:0; overflow-x:hidden; background:var(--bg); min-height:100vh; }\n#topbar {\n  height:52px;',
        1
    )
    # Remove the topbar-search CSS block
    search_css_start = html.find('.topbar-search {')
    if search_css_start >= 0:
        search_css_end = html.find('\n}', search_css_start) + 2
        html = html[:search_css_start] + html[search_css_end:]
    search_input_css = html.find('.topbar-search input {')
    if search_input_css >= 0:
        end = html.find('\n}', search_input_css) + 2
        html = html[:search_input_css] + html[end:]
    search_icon_css = html.find('.topbar-search-icon {')
    if search_icon_css >= 0:
        end = html.find('\n}', search_icon_css) + 2
        html = html[:search_icon_css] + html[end:]
    changes.append('Fixed topbar CSS (fallback method)')

# ── 3. Fix body/html CSS in :root block area ─────────────────────────────
# Ensure the body background doesn't show white
body_rule = 'body { background:var(--bg); color:var(--ink); font:15px/1.5 Inter,system-ui,sans-serif; display:flex; min-height:100vh; }'
fixed_body = 'html, body { margin:0; padding:0; }\nbody { background:var(--bg); color:var(--ink); font:15px/1.5 Inter,system-ui,sans-serif; display:flex; min-height:100vh; overflow-x:hidden; }'
if body_rule in html:
    html = html.replace(body_rule, fixed_body, 1)
    changes.append('Fixed body CSS to prevent white background')

# ── 4. Fix the gradient body::before so it doesn't create white space ────
# Make sure body::before is z-index:-1 and doesn't add height
old_before = """body::before {
  content: '';
  position: fixed; inset: 0; z-index: -1; pointer-events: none;"""
new_before = """body::before {
  content: '';
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  width: 100%; height: 100%;"""
if old_before in html and 'width: 100%; height: 100%;' not in html[html.find(old_before):html.find(old_before)+200]:
    html = html.replace(old_before, new_before, 1)
    changes.append('Fixed body::before to not cause white space')

# ── 5. Verify ─────────────────────────────────────────────────────────────
print('Verifying...')
pages = ['page-home','page-tutor','page-planner','page-myplans','page-quiz','page-resources','page-settings']
all_ok = True
for pg in pages:
    idx = html.find(f'id="{pg}"')
    if idx < 0: print(f'  NOT FOUND: {pg}'); all_ok=False; continue
    before = html[idx-5:idx]
    if before != '<div ': print(f'  BAD: {pg} [{before}]'); all_ok=False
    else: print(f'  OK: {pg}')

search_bar_gone = 'topbar-search' not in html[html.find('<div id="topbar"'):html.find('<div id="topbar">')+500]
print(f'  Search bar removed from HTML: {search_bar_gone}')
print(f'  Search CSS removed: {"topbar-search {" not in html}')
dec_check = 'id="dec"' in html
print(f'  id="dec" in DOM: {dec_check}')
print(f'  /api/chat preserved: {"/api/chat" in html}')

if not all_ok:
    print('ABORTING — boundary check failed')
    sys.exit(1)

open('demo/static/index.html', 'w', encoding='utf-8').write(html)
print(f'\nSaved. Size: {original} -> {len(html)} chars')
print('Changes:')
for c in changes: print(f'  - {c}')
