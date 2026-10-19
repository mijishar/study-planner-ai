"""
StudyMate AI Premium Upgrade Script
Performs all changes using safe Python string operations.
"""
import re, sys

src = 'demo/static/index.html'
html = open(src, encoding='utf-8').read()
original_size = len(html)

changes = []

# ═══════════════════════════════════════════════════════════════════════════
# 1. REMOVE PROGRESS PAGE HTML
# ═══════════════════════════════════════════════════════════════════════════
# Find page-progress div and remove it entirely
prog_start = html.find('<div id="page-progress"')
# Find the end by counting div depth
if prog_start >= 0:
    i = prog_start + len('<div id="page-progress"')
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
    html = html[:prog_start] + html[i:]
    changes.append('Removed page-progress HTML block')

# ═══════════════════════════════════════════════════════════════════════════
# 2. REMOVE PROGRESS NAV ITEM
# ═══════════════════════════════════════════════════════════════════════════
# Remove the button with data-page="progress"
for pat in [
    r'<button[^>]+data-page="progress"[^>]*>[\s\S]*?</button>\s*',
]:
    m = re.search(pat, html)
    if m:
        html = html[:m.start()] + html[m.end():]
        changes.append('Removed progress nav button')

# ═══════════════════════════════════════════════════════════════════════════
# 3. REMOVE PROGRESS JS (refreshProgress, DEMO_MASTERY, prog- elements)
# ═══════════════════════════════════════════════════════════════════════════
# Remove refreshProgress function
rp_idx = html.find('function refreshProgress()')
if rp_idx >= 0:
    # Find the closing brace
    end = html.find('\n}', rp_idx) + 2
    html = html[:rp_idx] + html[end:]
    changes.append('Removed refreshProgress() function')

# Remove DEMO_MASTERY const
dm_idx = html.find('const DEMO_MASTERY')
if dm_idx >= 0:
    end = html.find(';', dm_idx) + 1
    html = html[:dm_idx] + html[end:]
    changes.append('Removed DEMO_MASTERY const')

# Remove refreshProgress() call from nav()
html = html.replace('  if (id === "progress") refreshProgress();\n', '')
html = html.replace('if (id === "progress") refreshProgress();', '')

# ═══════════════════════════════════════════════════════════════════════════
# 4. UPGRADE CSS DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════
old_root_start = html.find(':root {')
old_root_end   = html.find('}', old_root_start) + 1
if old_root_start >= 0:
    new_root = """:root {
  --bg:       #080B14;
  --surface:  #0D1220;
  --panel:    #111827;
  --raised:   #1a2235;
  --line:     #1f2d47;
  --line2:    #2a3d5c;
  --ink:      #e8edf8;
  --mute:     #6b7fa0;
  --dim:      #3d4f6b;
  --orange:   #FF9900;
  --orange2:  #FFB833;
  --violet:   #7c3aed;
  --violet2:  #a78bfa;
  --blue:     #3b82f6;
  --blue2:    #60a5fa;
  --cyan:     #06b6d4;
  --green:    #10b981;
  --green2:   #34d399;
  --red:      #f87171;
  --amber:    #fbbf24;
  --sidebar-w: 240px;
}"""
    html = html[:old_root_start] + new_root + html[old_root_end:]
    changes.append('Upgraded CSS design tokens')

# ═══════════════════════════════════════════════════════════════════════════
# 5. ADD PREMIUM CSS BEFORE </style>
# ═══════════════════════════════════════════════════════════════════════════
premium_css = """
/* ═══════════════════════════════════════════════════════════
   PREMIUM DESIGN SYSTEM
═══════════════════════════════════════════════════════════ */

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--line2); border-radius:99px; }
::-webkit-scrollbar-thumb:hover { background:var(--mute); }

/* Body gradient */
body {
  background: linear-gradient(135deg, #080B14 0%, #0a0f1e 50%, #080B14 100%);
  background-attachment: fixed;
}

/* Glassmorphism cards */
.card {
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(31, 45, 71, 0.7);
  border-radius: 16px;
  padding: 20px 22px;
  display: flex; flex-direction: column; gap: 12px;
  transition: box-shadow .25s ease, border-color .25s ease, transform .2s ease;
}
.card:hover { box-shadow: 0 8px 32px rgba(0,0,0,.5); border-color: var(--line2); }

/* Premium buttons */
.btn-primary {
  background: linear-gradient(135deg, var(--orange) 0%, var(--orange2) 100%);
  color: #111; border: 0; border-radius: 10px;
  padding: 0 20px; font-weight: 700; cursor: pointer; font: inherit;
  transition: transform .15s ease, box-shadow .2s ease, filter .2s ease;
  white-space: nowrap; height: 42px;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255,153,0,.4);
  filter: brightness(1.08);
}
.btn-primary:active { transform: translateY(0); box-shadow: none; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; filter: none; }

/* Premium input */
input[type="text"], input[type="number"], input[type="date"],
input:not([type="checkbox"]):not([type="file"]):not([type="radio"]) {
  background: rgba(13,18,32,.9);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 14px;
  font: inherit;
  transition: border-color .2s, box-shadow .2s;
}
input:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px rgba(255,153,0,.15); }

/* Chat bubbles */
.msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, rgba(124,58,237,.3) 0%, rgba(59,130,246,.2) 100%);
  border: 1px solid rgba(124,58,237,.3);
  border-radius: 18px 18px 4px 18px;
  padding: 12px 16px;
  max-width: 82%;
  line-height: 1.55;
  animation: msgSlideUp .25s ease both;
}
.msg.bot {
  align-self: flex-start;
  background: rgba(17,24,39,.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--line);
  border-radius: 18px 18px 18px 4px;
  padding: 12px 16px;
  max-width: 88%;
  line-height: 1.6;
  animation: msgSlideUp .25s ease both;
}
.msg.bot pre, .msg.bot code {
  background: rgba(0,0,0,.4);
  border: 1px solid var(--line2);
  border-radius: 8px;
  padding: 3px 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--cyan);
}
.msg.bot pre { display: block; padding: 12px 14px; margin: 8px 0; overflow-x: auto; }
.msg .t { color: var(--mute); font-size: 11px; margin-top: 6px; }

/* Typing indicator */
#typing-indicator {
  display: none; align-items: center; gap: 5px;
  padding: 10px 14px; align-self: flex-start;
}
#typing-indicator.visible { display: flex; }
.typing-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--mute); animation: typingBounce 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: .2s; }
.typing-dot:nth-child(3) { animation-delay: .4s; }

/* Quick action cards (premium) */
.qa-card {
  background: rgba(17,24,39,.85);
  backdrop-filter: blur(10px);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 20px 16px;
  cursor: pointer; text-align: center;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  font: inherit; color: var(--ink); width: 100%;
}
.qa-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 32px rgba(0,0,0,.5);
  border-color: rgba(255,153,0,.4);
}
.qa-card:active { transform: translateY(-2px); }
.qa-card-icon {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; box-shadow: 0 4px 14px rgba(0,0,0,.35);
  transition: transform .2s ease;
}
.qa-card:hover .qa-card-icon { transform: scale(1.1) rotate(-4deg); }
.qa-card-label { font-size: 14px; font-weight: 700; }
.qa-card-desc  { font-size: 12px; color: var(--mute); }

/* Sidebar premium */
#sidebar {
  background: rgba(13,18,32,.95);
  backdrop-filter: blur(16px);
  border-right: 1px solid rgba(31,45,71,.6);
}
.sb-logo-icon {
  background: linear-gradient(135deg, var(--orange) 0%, var(--violet) 100%);
  box-shadow: 0 0 20px rgba(255,153,0,.3);
}
.nav-item.active {
  background: linear-gradient(135deg, rgba(124,58,237,.15) 0%, rgba(255,153,0,.1) 100%);
  color: var(--orange2);
  border: 1px solid rgba(255,153,0,.2);
}
.nav-item:hover { background: rgba(30,45,70,.6); }

/* Top stats bar */
.top-stats-bar {
  background: rgba(17,24,39,.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(31,45,71,.6);
}
.ts-val { color: var(--orange); text-shadow: 0 0 12px rgba(255,153,0,.4); }

/* Quote banner */
.qb-left { background: linear-gradient(135deg, #120a2a 0%, rgba(13,18,32,.9) 100%); }
.qb-right { background: linear-gradient(135deg, rgba(255,153,0,.06) 0%, rgba(13,18,32,.9) 100%); }

/* Streak card */
.streak-card {
  background: linear-gradient(135deg, rgba(17,24,39,.9) 0%, rgba(124,58,237,.08) 100%);
  border-color: rgba(124,58,237,.2);
}

/* Study planner timetable */
.sp-table tr.task-row.done td { opacity: .5; }
.sp-table tr.task-row.done .task-topic { text-decoration: line-through; color: var(--mute); }
.sp-table tr.task-row { transition: background .15s; }
.sp-table tr.task-row:hover td { background: rgba(255,153,0,.03); }

/* Quiz cards */
.quiz-option {
  display: block; width: 100%; text-align: left;
  padding: 12px 16px; margin: 6px 0;
  background: rgba(26,34,53,.7); border: 1px solid var(--line);
  border-radius: 10px; color: var(--ink); font: inherit;
  cursor: pointer; transition: all .15s ease;
}
.quiz-option:hover { border-color: var(--blue2); background: rgba(59,130,246,.08); transform: translateX(3px); }
.quiz-option.selected { border-color: var(--orange); background: rgba(255,153,0,.1); }
.quiz-option.correct  { border-color: var(--green2); background: rgba(16,185,129,.12); animation: correctFlash .4s ease; }
.quiz-option.wrong    { border-color: var(--red); background: rgba(248,113,113,.12); animation: wrongShake .4s ease; }

/* Upload zone */
.upload-zone {
  border: 2px dashed var(--line2); border-radius: 14px;
  padding: 24px; text-align: center; transition: all .2s ease;
  background: rgba(17,24,39,.5);
}
.upload-zone:hover, .upload-zone.drag-over {
  border-color: var(--orange); border-style: solid;
  background: rgba(255,153,0,.04);
  box-shadow: 0 0 0 4px rgba(255,153,0,.1);
}

/* Progress bar */
.prog-fill { transition: width .6s cubic-bezier(.4,0,.2,1); }
.prog-wrap { background: rgba(31,45,71,.5); border-radius: 99px; height: 6px; overflow: hidden; }

/* Subtle animated background mesh (very low perf cost) */
body::before {
  content: '';
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(ellipse 60% 40% at 20% 20%, rgba(124,58,237,.05) 0%, transparent 60%),
    radial-gradient(ellipse 50% 35% at 80% 80%, rgba(6,182,212,.04) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%, rgba(255,153,0,.03) 0%, transparent 60%);
  animation: bgPulse 20s ease-in-out infinite alternate;
}

/* ═══ Keyframes ═══ */
@keyframes msgSlideUp {
  from { opacity:0; transform:translateY(10px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes typingBounce {
  0%,60%,100% { transform:translateY(0); }
  30% { transform:translateY(-6px); }
}
@keyframes correctFlash {
  0%  { background:rgba(16,185,129,.4); }
  100%{ background:rgba(16,185,129,.12); }
}
@keyframes wrongShake {
  0%,100%{ transform:translateX(0); }
  20%    { transform:translateX(-5px); }
  40%    { transform:translateX(5px); }
  60%    { transform:translateX(-3px); }
  80%    { transform:translateX(3px); }
}
@keyframes bgPulse {
  from { opacity:.6; }
  to   { opacity:1; }
}

/* ═══ Reduced motion ═══ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .001ms !important;
    transition-duration: .001ms !important;
  }
  body::before { animation: none; }
}

/* ═══ Responsive ═══ */
@media (max-width: 1024px) { .qa-grid { grid-template-columns: repeat(3,1fr); } }
@media (max-width: 768px)  { .qa-grid { grid-template-columns: repeat(2,1fr); } .quote-banner { grid-template-columns:1fr; } }
@media (max-width: 640px)  {
  :root { --sidebar-w:0px; }
  #sidebar { display:none; }
  #app { margin-left:0; }
  .top-stats-bar { flex-wrap:wrap; gap:8px; }
  .ts-divider { display:none; }
}
"""

style_end = html.rfind('</style>')
if style_end >= 0:
    html = html[:style_end] + premium_css + html[style_end:]
    changes.append('Added premium CSS design system')

# ═══════════════════════════════════════════════════════════════════════════
# 6. ADD TYPING INDICATOR TO AI TUTOR PAGE
# ═══════════════════════════════════════════════════════════════════════════
# Add typing indicator div after tutor-log
old_att = '<div class="att-preview" id="tutor-att"></div>'
new_att = '''<div id="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        <div class="att-preview" id="tutor-att"></div>'''
if old_att in html:
    html = html.replace(old_att, new_att, 1)
    changes.append('Added typing indicator to AI Tutor')

# ═══════════════════════════════════════════════════════════════════════════
# 7. ADD TYPING INDICATOR JS + UPDATE TUTOR SUBMIT
# ═══════════════════════════════════════════════════════════════════════════
# Add helper functions before </script>
script_end = html.rfind('</script>')
typing_js = """
// ── Typing indicator ─────────────────────────────────────────────────────
function showTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) { el.classList.add('visible'); el.scrollIntoView({block:'nearest'}); }
}
function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.classList.remove('visible');
}

// ── Disable/enable submit button ─────────────────────────────────────────
function setTutorBusy(busy) {
  const btn = document.querySelector('#tutor-form button');
  if (btn) btn.disabled = busy;
}

"""
if script_end >= 0:
    html = html[:script_end] + typing_js + html[script_end:]
    changes.append('Added typing indicator JS functions')

# Update tutor form submit to use typing indicator
old_submit = "  const wait = addMsg(logEl, \"bot\", \"<span class='t'>Thinking\u2026</span>\");"
new_submit_inject = """  showTyping(); setTutorBusy(true);
  const wait = addMsg(logEl, "bot", "<span class='t'>Thinking\u2026</span>");"""
# Actually update inside the chat function that's called from tutor
old_chat_start = '  const wait = addMsg(logEl, "bot", "<span class=\'t\'>Thinking\u2026</span>");'
if old_chat_start in html:
    new_chat_start = '  showTyping(); setTutorBusy(true);\n  const wait = addMsg(logEl, "bot", "<span class=\'t\'>Thinking\u2026</span>");'
    html = html.replace(old_chat_start, new_chat_start, 1)

# Hide typing after response
old_handle = '    handleDecisions(out.decisions);'
new_handle = '    hideTyping(); setTutorBusy(false);\n    handleDecisions(out.decisions);'
if old_handle in html:
    html = html.replace(old_handle, new_handle, 1)

# Hide on error too
old_err = '      wait.innerHTML = `<span style="color:var(--red)">Network error:'
new_err = '      hideTyping(); setTutorBusy(false);\n      wait.innerHTML = `<span style="color:var(--red)">Network error:'
if old_err in html:
    html = html.replace(old_err, new_err, 1)
changes.append('Updated tutor form to use typing indicator')

# ═══════════════════════════════════════════════════════════════════════════
# 8. FIX PROGRESS REFERENCES IN nav() and updateStats()
# ═══════════════════════════════════════════════════════════════════════════
# Remove progress-related stat elements that might still be referenced
html = html.replace(
    'if (id === "progress") refreshProgress();', ''
)

# ═══════════════════════════════════════════════════════════════════════════
# 9. BOUNDARY CHECK
# ═══════════════════════════════════════════════════════════════════════════
pages = ['page-home','page-tutor','page-planner','page-myplans','page-quiz']
all_ok = True
for pg in pages:
    idx = html.find(f'id="{pg}"')
    if idx < 5:
        print(f"  ERROR: {pg} not found or at wrong position!")
        all_ok = False
        continue
    before = html[idx-5:idx]
    if before != '<div ':
        print(f"  ERROR: {pg} boundary broken: [{before}]")
        all_ok = False
    else:
        print(f"  OK: {pg}")

if 'id="page-progress"' in html:
    print("  ERROR: page-progress still present!")
    all_ok = False
else:
    print("  OK: page-progress removed")

if 'data-page="progress"' in html:
    print("  ERROR: progress nav item still present!")
    all_ok = False
else:
    print("  OK: progress nav item removed")

# ═══════════════════════════════════════════════════════════════════════════
# 10. SAVE
# ═══════════════════════════════════════════════════════════════════════════
if all_ok:
    open(src, 'w', encoding='utf-8').write(html)
    print(f"\nSaved. Size: {original_size} -> {len(html)} chars")
    print(f"Changes applied: {len(changes)}")
    for c in changes:
        print(f"  - {c}")
else:
    print("\nNOT SAVED due to boundary errors!")
    sys.exit(1)
