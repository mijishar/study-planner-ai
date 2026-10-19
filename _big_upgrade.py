#!/usr/bin/env python3
"""
_big_upgrade.py — StudyMate AI Frontend Premium Upgrade

Features added:
  1. Resources + Settings nav items in sidebar
  2. Resources page
  3. Settings page (Appearance / Profile / Learning tabs)
  4. Focus Timer card on Home page
  5. Top bar on every page
  6. Welcome banner replacing the Home page-header

Usage: python _big_upgrade.py
"""
import re
import sys
from pathlib import Path

HTML_PATH = Path(__file__).parent / "demo" / "static" / "index.html"

# ── Read ──────────────────────────────────────────────────────────────────
print("Reading", HTML_PATH, "…")
content = HTML_PATH.read_text(encoding="utf-8")
original_size = len(content)
print(f"  Original size: {original_size:,} bytes / {content.count(chr(10))+1} lines")

changes = []

# ─────────────────────────────────────────────────────────────────────────────
# Helper: safe replace (assert exactly one occurrence)
# ─────────────────────────────────────────────────────────────────────────────
def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        print(f"  ERROR [{label}]: expected 1 occurrence of marker, found {count}")
        sys.exit(1)
    result = text.replace(old, new, 1)
    changes.append(label)
    print(f"  ✓ {label}")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — Add Resources + Settings nav items to sidebar
# ═══════════════════════════════════════════════════════════════════════════
NAV_RESOURCES_SETTINGS = """\
    <button class="nav-item" data-page="resources">
      <span class="nav-icon-wrap"><span class="icon">📖</span></span>
      <span class="nav-label">Resources</span>
    </button>
    <button class="nav-item" data-page="settings">
      <span class="nav-icon-wrap"><span class="icon">⚙️</span></span>
      <span class="nav-label">Settings</span>
    </button>
    </div>
    <div class="sb-meta" id="sb-meta" style="padding:10px 16px 16px;border-top:1px solid var(--line)">Loading&hellip;</div>"""

# The existing closing of the second sb-nav group ends with the quiz button then </div>
OLD_NAV_CLOSE = """\
    <button class="nav-item" data-page="quiz">
      <span class="nav-icon-wrap"><span class="icon">✏️</span></span>
      <span class="nav-label">Practice Quiz</span>
    </button>
    </div>
    <div class="sb-meta" id="sb-meta" style="padding:10px 16px 16px;border-top:1px solid var(--line)">Loading&hellip;</div>"""

NEW_NAV_CLOSE = """\
    <button class="nav-item" data-page="quiz">
      <span class="nav-icon-wrap"><span class="icon">✏️</span></span>
      <span class="nav-label">Practice Quiz</span>
    </button>
    <button class="nav-item" data-page="resources">
      <span class="nav-icon-wrap"><span class="icon">📖</span></span>
      <span class="nav-label">Resources</span>
    </button>
    <button class="nav-item" data-page="settings">
      <span class="nav-icon-wrap"><span class="icon">⚙️</span></span>
      <span class="nav-label">Settings</span>
    </button>
    </div>
    <div class="sb-meta" id="sb-meta" style="padding:10px 16px 16px;border-top:1px solid var(--line)">Loading&hellip;</div>"""

content = replace_once(content, OLD_NAV_CLOSE, NEW_NAV_CLOSE, "Add Resources+Settings nav items")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — Light-theme CSS + Top-bar CSS + Welcome-banner CSS + Timer CSS
# ═══════════════════════════════════════════════════════════════════════════
EXTRA_CSS = """\
/* ── Light theme ── */
[data-theme="bright"] {
  --bg: #f0f4f8;
  --surface: #ffffff;
  --panel: #ffffff;
  --raised: #f8fafc;
  --line: #e2e8f0;
  --line2: #cbd5e1;
  --ink: #1e293b;
  --mute: #64748b;
  --dim: #94a3b8;
}
[data-theme="bright"] body { background: #f0f4f8; }
[data-theme="bright"] .card { background: rgba(255,255,255,.95); border-color: #e2e8f0; }
[data-theme="bright"] #sidebar { background: rgba(255,255,255,.98); border-color: #e2e8f0; }
[data-theme="bright"] .nav-item:hover { background: #f1f5f9; }
[data-theme="bright"] .nav-item.active { background: rgba(124,58,237,.08); }
[data-theme="bright"] input:not([type="checkbox"]):not([type="file"]):not([type="radio"]) {
  background: #f8fafc; border-color: #e2e8f0; color: #1e293b;
}
[data-theme="bright"] .msg.bot { background: rgba(248,250,252,.95); border-color: #e2e8f0; }
[data-theme="bright"] .msg.user { background: linear-gradient(135deg, rgba(124,58,237,.12) 0%, rgba(59,130,246,.08) 100%); }
[data-theme="bright"] body::before { opacity: .3; }

/* ── Top bar ── */
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
[data-theme="bright"] .topbar-search { background:#f8fafc; border-color:#e2e8f0; }

/* ── Welcome banner ── */
.welcome-banner {
  background:linear-gradient(135deg,rgba(124,58,237,.2) 0%,rgba(6,182,212,.1) 50%,rgba(255,153,0,.08) 100%);
  border:1px solid rgba(124,58,237,.2); border-radius:20px; padding:28px 32px;
  display:flex; align-items:center; justify-content:space-between; gap:20px;
  position:relative; overflow:hidden; min-height:140px;
}
.wb-content { flex:1; z-index:1; }
.wb-greeting { font-size:24px; font-weight:800; margin-bottom:4px; }
.wb-date { font-size:13px; color:var(--mute); margin-bottom:10px; }
.wb-quote { font-size:14px; font-style:italic; color:var(--violet2); margin-bottom:4px; max-width:480px; line-height:1.5; }
.wb-author { font-size:12px; color:var(--mute); margin-bottom:14px; }
.wb-actions { display:flex; gap:8px; flex-wrap:wrap; }
.wb-illustration { position:relative; width:120px; height:120px; flex-shrink:0; }
.wb-orb { position:absolute; border-radius:50%; filter:blur(24px); opacity:.5; }
.wb-orb1 { width:80px;height:80px; background:var(--violet); top:-10px; right:-10px; animation:orbFloat1 6s ease-in-out infinite; }
.wb-orb2 { width:60px;height:60px; background:var(--cyan); bottom:0; right:20px; animation:orbFloat2 8s ease-in-out infinite; }
.wb-orb3 { width:50px;height:50px; background:var(--orange); top:20px; left:-10px; animation:orbFloat1 7s ease-in-out infinite reverse; }
@keyframes floatUpDown { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
@keyframes orbFloat1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(6px,-8px)} }
@keyframes orbFloat2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-5px,6px)} }
[data-theme="bright"] .welcome-banner { background:linear-gradient(135deg,rgba(124,58,237,.08) 0%,rgba(6,182,212,.05) 100%); border-color:rgba(124,58,237,.15); }
[data-theme="bright"] .wb-quote { color:var(--violet); }

/* ── Focus Timer ── */
.focus-timer-card { border-color: rgba(124,58,237,.25); }
.focus-timer-layout { display:flex; align-items:center; gap:20px; flex-wrap:wrap; }
.timer-ring-wrap { position:relative; width:120px; height:120px; flex-shrink:0; }
.timer-svg { width:120px; height:120px; }
.timer-display { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.timer-time { font-size:22px; font-weight:800; color:var(--violet2); line-height:1; }
.timer-label { font-size:10px; color:var(--mute); margin-top:2px; text-transform:uppercase; letter-spacing:.06em; }
.timer-controls { flex:1; display:flex; flex-direction:column; gap:10px; min-width:140px; }
.timer-duration-row { display:flex; align-items:center; gap:6px; }

/* ── Settings page ── */
.settings-tabs { display:flex; gap:4px; border-bottom:1px solid var(--line); margin-bottom:16px; }
.settings-tab {
  padding:8px 18px; border:none; background:none; color:var(--mute); font:inherit;
  font-size:13px; font-weight:600; cursor:pointer; border-bottom:2px solid transparent;
  transition:all .15s; margin-bottom:-1px;
}
.settings-tab.active { color:var(--violet2); border-bottom-color:var(--violet2); }
.settings-tab:hover:not(.active) { color:var(--ink); }
.settings-panel { display:none; flex-direction:column; gap:18px; }
.settings-panel.active { display:flex; }
.settings-section-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--mute); margin-bottom:4px; }
.theme-options { display:flex; gap:10px; flex-wrap:wrap; }
.theme-option {
  display:flex; flex-direction:column; align-items:center; gap:6px; padding:12px 18px;
  border:1px solid var(--line); border-radius:12px; cursor:pointer; transition:all .15s;
  background:var(--raised); font-size:13px; font-weight:600; min-width:80px;
}
.theme-option:hover { border-color:var(--violet2); }
.theme-option.selected { border-color:var(--violet2); background:rgba(124,58,237,.1); color:var(--violet2); }
.avatar-options { display:flex; gap:8px; flex-wrap:wrap; }
.avatar-option {
  width:44px; height:44px; border-radius:50%; border:2px solid var(--line); font-size:22px;
  display:flex; align-items:center; justify-content:center; cursor:pointer; transition:all .15s;
  background:var(--raised);
}
.avatar-option:hover { border-color:var(--violet2); transform:scale(1.1); }
.avatar-option.selected { border-color:var(--violet2); background:rgba(124,58,237,.15); }
.settings-field { display:flex; flex-direction:column; gap:6px; }
.settings-field label { font-size:13px; font-weight:600; color:var(--ink); }
.settings-field input, .settings-field select {
  background:var(--raised); border:1px solid var(--line); border-radius:10px;
  padding:10px 14px; color:var(--ink); font:inherit; transition:border-color .2s;
}
.settings-field input:focus, .settings-field select:focus { outline:none; border-color:var(--violet2); }
.settings-radio-group { display:flex; gap:10px; flex-wrap:wrap; }
.settings-radio-opt { display:flex; align-items:center; gap:6px; cursor:pointer; font-size:13px; }
.settings-radio-opt input[type="radio"] { accent-color:var(--violet2); cursor:pointer; }
.settings-actions { display:flex; gap:10px; margin-top:4px; }
.settings-note { font-size:12px; color:var(--mute); line-height:1.5; padding:10px 12px; background:rgba(124,58,237,.06); border:1px solid rgba(124,58,237,.15); border-radius:8px; }
.setting-slider { width:100%; accent-color:var(--violet2); cursor:pointer; }
.setting-slider-row { display:flex; align-items:center; gap:12px; }
.setting-slider-val { font-size:14px; font-weight:700; color:var(--violet2); min-width:60px; }

/* ── Resources page ── */
.resource-section-title { font-size:16px; font-weight:800; margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.resource-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:12px; }
.resource-card {
  background:var(--raised); border:1px solid var(--line); border-radius:12px;
  padding:14px 16px; display:flex; flex-direction:column; gap:6px;
  transition:border-color .15s, transform .15s;
}
.resource-card:hover { border-color:var(--violet2); transform:translateY(-2px); }
.resource-card a { color:var(--violet2); text-decoration:none; font-weight:700; font-size:14px; }
.resource-card a:hover { text-decoration:underline; }
.resource-card .rc-desc { font-size:12px; color:var(--mute); line-height:1.5; }
.resource-card .rc-icon { font-size:24px; }
.resource-disclaimer { font-size:12px; color:var(--mute); padding:10px 14px; background:rgba(251,191,36,.06); border:1px solid rgba(251,191,36,.2); border-radius:8px; }
</style>"""

content = replace_once(content, "</style>", EXTRA_CSS, "Add CSS (light theme, topbar, welcome banner, timer, settings, resources)")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — Insert Top Bar as first child of <div id="app">
# ═══════════════════════════════════════════════════════════════════════════
TOPBAR_HTML = """\
<div id="topbar">
  <div class="topbar-search">
    <span class="topbar-search-icon">🔍</span>
    <input id="topbar-search" type="text" placeholder="Search topics or ask AI…"
           autocomplete="off" onkeydown="if(event.key==='Enter'){nav('tutor');prefill(this.value);this.value='';}">
  </div>
  <div class="topbar-right">
    <button class="topbar-btn" onclick="nav('settings')" title="Settings">⚙️</button>
    <div class="topbar-avatar" onclick="nav('settings')" title="Profile" id="topbar-avatar-display">🎓</div>
  </div>
</div>"""

OLD_APP_OPEN = """\
<div id="app">

  <!-- ── HOME ─────────────────────────────────────────────────────────── -->"""
NEW_APP_OPEN = """\
<div id="app">

""" + TOPBAR_HTML + """

  <!-- ── HOME ─────────────────────────────────────────────────────────── -->"""

content = replace_once(content, OLD_APP_OPEN, NEW_APP_OPEN, "Insert top bar as first child of #app")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — Replace Home page-header with welcome banner
# ═══════════════════════════════════════════════════════════════════════════
# The current home page has a top-stats-bar but no separate page-header with h1.
# Looking at the HTML, the home page begins with the top-stats-bar directly.
# We'll insert the welcome banner BEFORE the top-stats-bar.

WELCOME_BANNER_HTML = """\
    <!-- ── Welcome banner ─────────────────────────────────────────────────── -->
    <div class="welcome-banner" style="animation:fadeSlideDown .5s ease both">
      <div class="wb-content">
        <div class="wb-greeting" id="wb-greeting">Good morning 👋</div>
        <div class="wb-date" id="wb-date"></div>
        <div class="wb-quote" id="wb-quote">Loading quote…</div>
        <div class="wb-author" id="wb-author-text"></div>
        <div class="wb-actions">
          <button class="btn-primary" onclick="nav('tutor')" style="padding:8px 20px">Ask AI Now</button>
          <button class="btn-sm" onclick="nav('planner')">📅 Study Plan</button>
        </div>
      </div>
      <div class="wb-illustration" aria-hidden="true">
        <div class="wb-orb wb-orb1"></div>
        <div class="wb-orb wb-orb2"></div>
        <div class="wb-orb wb-orb3"></div>
        <div style="font-size:72px;position:relative;z-index:1;animation:floatUpDown 4s ease-in-out infinite">🎓</div>
      </div>
    </div>

"""

OLD_HOME_STATS_START = """\
    <!-- ── Top stats bar ───────────────────────────────────────────────── -->"""
NEW_HOME_STATS_START = WELCOME_BANNER_HTML + """\
    <!-- ── Top stats bar ───────────────────────────────────────────────── -->"""

content = replace_once(content, OLD_HOME_STATS_START, NEW_HOME_STATS_START, "Insert welcome banner on Home page")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — Add Focus Timer card to Home page (before closing </div> of page-home)
# ═══════════════════════════════════════════════════════════════════════════
FOCUS_TIMER_HTML = """\

    <!-- ── Focus Timer ──────────────────────────────────────────────────── -->
    <div class="card focus-timer-card" style="animation:fadeSlideUp .9s ease both">
      <div class="card-title">Focus Timer</div>
      <div class="focus-timer-layout">
        <div class="timer-ring-wrap">
          <svg class="timer-svg" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(124,58,237,.15)" stroke-width="8"/>
            <circle cx="60" cy="60" r="52" fill="none" stroke="var(--violet2)" stroke-width="8"
                    stroke-linecap="round" stroke-dasharray="326.7"
                    id="timer-ring" style="stroke-dashoffset:0;transform:rotate(-90deg);transform-origin:50% 50%;transition:stroke-dashoffset .5s linear"/>
          </svg>
          <div class="timer-display">
            <div class="timer-time" id="focus-timer-display">25:00</div>
            <div class="timer-label" id="timer-status-label">Ready</div>
          </div>
        </div>
        <div class="timer-controls">
          <div class="timer-duration-row">
            <label style="font-size:12px;color:var(--mute)">Focus</label>
            <input type="number" id="timer-duration-input" min="1" max="120" value="25"
                   style="width:60px;text-align:center">
            <label style="font-size:12px;color:var(--mute)">min</label>
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn-primary" id="timer-start-btn" onclick="timerToggle()" style="flex:1">▶ Start</button>
            <button class="btn-sm" onclick="timerReset()">↺ Reset</button>
          </div>
          <div id="timer-complete-msg" style="display:none;color:var(--green2);font-size:13px;font-weight:600;text-align:center">
            🎉 Session complete! Take a break.
          </div>
        </div>
      </div>
    </div>

  </div>
  <div id="page-tutor" class="page">"""

OLD_HOME_END = """\
  </div>
  <div id="page-tutor" class="page">"""

content = replace_once(content, OLD_HOME_END, FOCUS_TIMER_HTML, "Add Focus Timer card to Home page")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6 — Add Resources page and Settings page before </div><!-- #app -->
# ═══════════════════════════════════════════════════════════════════════════
RESOURCES_PAGE = """\
<div id="page-resources" class="page">
  <div class="page-header">
    <div><h1>Resources</h1><div class="sub">Curated learning materials and tools</div></div>
  </div>

  <div class="resource-disclaimer">
    📌 External links open in a new tab. StudyMate AI is not affiliated with these resources.
  </div>

  <!-- Programming -->
  <div>
    <div class="resource-section-title">💻 Programming</div>
    <div class="resource-grid">
      <div class="resource-card">
        <div class="rc-icon">🌐</div>
        <a href="https://developer.mozilla.org" target="_blank" rel="noopener noreferrer">MDN Web Docs</a>
        <div class="rc-desc">Comprehensive reference for HTML, CSS, and JavaScript by Mozilla. The go-to resource for web developers.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🆓</div>
        <a href="https://www.freecodecamp.org" target="_blank" rel="noopener noreferrer">freeCodeCamp</a>
        <div class="rc-desc">Free interactive coding lessons and certifications covering web development, Python, data science, and more.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🎓</div>
        <a href="https://cs50.harvard.edu" target="_blank" rel="noopener noreferrer">CS50 (Harvard)</a>
        <div class="rc-desc">Harvard's introduction to computer science — one of the most popular online CS courses in the world.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🐍</div>
        <a href="https://docs.python.org/3/" target="_blank" rel="noopener noreferrer">Python Official Docs</a>
        <div class="rc-desc">The official Python 3 documentation with tutorials, library references, and language specification.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">⚔️</div>
        <a href="https://leetcode.com" target="_blank" rel="noopener noreferrer">LeetCode</a>
        <div class="rc-desc">Practice coding interview problems with hundreds of algorithm and data structure challenges, ranked by difficulty.</div>
      </div>
    </div>
  </div>

  <!-- Mathematics -->
  <div>
    <div class="resource-section-title">📐 Mathematics</div>
    <div class="resource-grid">
      <div class="resource-card">
        <div class="rc-icon">🏫</div>
        <a href="https://www.khanacademy.org" target="_blank" rel="noopener noreferrer">Khan Academy</a>
        <div class="rc-desc">Free math lessons from arithmetic to calculus, statistics, linear algebra, and beyond — with practice exercises.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🔢</div>
        <a href="https://www.wolframalpha.com" target="_blank" rel="noopener noreferrer">Wolfram Alpha</a>
        <div class="rc-desc">Computational knowledge engine. Solve equations, plot graphs, and explore mathematical concepts step-by-step.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🎥</div>
        <a href="https://www.youtube.com/@3blue1brown" target="_blank" rel="noopener noreferrer">3Blue1Brown (YouTube)</a>
        <div class="rc-desc">Visual, intuitive explanations of linear algebra, calculus, neural networks, and more by Grant Sanderson.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🏛️</div>
        <a href="https://ocw.mit.edu/courses/mathematics/" target="_blank" rel="noopener noreferrer">MIT OpenCourseWare — Math</a>
        <div class="rc-desc">Free course materials from MIT's mathematics department, including lecture notes, exams, and problem sets.</div>
      </div>
    </div>
  </div>

  <!-- AI / ML -->
  <div>
    <div class="resource-section-title">🤖 AI &amp; Machine Learning</div>
    <div class="resource-grid">
      <div class="resource-card">
        <div class="rc-icon">🚀</div>
        <a href="https://www.fast.ai" target="_blank" rel="noopener noreferrer">fast.ai</a>
        <div class="rc-desc">Practical deep learning courses taught top-down — start coding real models on day one, learn theory as you go.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">📊</div>
        <a href="https://www.coursera.org/specializations/machine-learning-introduction" target="_blank" rel="noopener noreferrer">Coursera ML Specialization</a>
        <div class="rc-desc">Andrew Ng's Machine Learning Specialization — the foundational ML course taken by millions of learners worldwide.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🤗</div>
        <a href="https://huggingface.co/learn" target="_blank" rel="noopener noreferrer">Hugging Face Learn</a>
        <div class="rc-desc">Free NLP and transformers courses from the creators of the Hugging Face ecosystem and BERT, GPT tooling.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">📄</div>
        <a href="https://paperswithcode.com" target="_blank" rel="noopener noreferrer">Papers with Code</a>
        <div class="rc-desc">Latest ML research papers paired with open-source implementations — track state-of-the-art results by task.</div>
      </div>
    </div>
  </div>

  <!-- Study Tools -->
  <div>
    <div class="resource-section-title">🛠 Study Tools &amp; Techniques</div>
    <div class="resource-grid">
      <div class="resource-card">
        <div class="rc-icon">🗂️</div>
        <a href="https://apps.ankiweb.net" target="_blank" rel="noopener noreferrer">Anki</a>
        <div class="rc-desc">Spaced-repetition flashcard app. Use it to memorize vocabulary, formulas, concepts, or anything else long-term.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">📓</div>
        <a href="https://www.notion.so" target="_blank" rel="noopener noreferrer">Notion</a>
        <div class="rc-desc">All-in-one workspace for notes, databases, kanban boards, and study wikis. Great for organising course material.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">🍅</div>
        <a href="https://francescocirillo.com/pages/pomodoro-technique" target="_blank" rel="noopener noreferrer">Pomodoro Technique</a>
        <div class="rc-desc">Work in 25-minute focused sprints with 5-minute breaks. Developed by Francesco Cirillo to reduce mental fatigue.</div>
      </div>
      <div class="resource-card">
        <div class="rc-icon">💡</div>
        <a href="https://fs.blog/feynman-learning-technique/" target="_blank" rel="noopener noreferrer">Feynman Technique</a>
        <div class="rc-desc">Learn anything deeply by explaining it in simple terms. Identify gaps in your understanding by teaching the concept aloud.</div>
      </div>
    </div>
  </div>
</div>"""

SETTINGS_PAGE = """\
<div id="page-settings" class="page">
  <div class="page-header">
    <div><h1>Settings</h1><div class="sub">Customise your StudyMate AI experience</div></div>
  </div>

  <div class="card">
    <!-- Tab bar -->
    <div class="settings-tabs">
      <button class="settings-tab active" onclick="openSettingsTab('appearance',this)">🎨 Appearance</button>
      <button class="settings-tab" onclick="openSettingsTab('profile',this)">👤 Profile</button>
      <button class="settings-tab" onclick="openSettingsTab('learning',this)">📚 Learning</button>
    </div>

    <!-- ── Appearance ── -->
    <div id="settings-appearance" class="settings-panel active">
      <div>
        <div class="settings-section-title">Theme</div>
        <div class="theme-options" id="theme-options">
          <div class="theme-option" data-theme-val="dark" onclick="selectTheme('dark')" id="theme-opt-dark">
            <span style="font-size:24px">🌙</span>
            <span>Dark</span>
          </div>
          <div class="theme-option" data-theme-val="bright" onclick="selectTheme('bright')" id="theme-opt-bright">
            <span style="font-size:24px">☀️</span>
            <span>Bright</span>
          </div>
          <div class="theme-option" data-theme-val="system" onclick="selectTheme('system')" id="theme-opt-system">
            <span style="font-size:24px">💻</span>
            <span>System</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Profile ── -->
    <div id="settings-profile" class="settings-panel">
      <div class="settings-note">
        🔒 Profile data is stored in this browser only. This is not an authenticated account.
      </div>

      <div class="settings-field">
        <label for="prof-name">Display name</label>
        <input id="prof-name" type="text" placeholder="e.g. Alex">
      </div>

      <div>
        <div class="settings-section-title">Avatar</div>
        <div class="avatar-options" id="avatar-options">
          <div class="avatar-option" data-avatar="🎓" onclick="selectAvatar('🎓',this)">🎓</div>
          <div class="avatar-option" data-avatar="📚" onclick="selectAvatar('📚',this)">📚</div>
          <div class="avatar-option" data-avatar="🧠" onclick="selectAvatar('🧠',this)">🧠</div>
          <div class="avatar-option" data-avatar="💡" onclick="selectAvatar('💡',this)">💡</div>
          <div class="avatar-option" data-avatar="🔬" onclick="selectAvatar('🔬',this)">🔬</div>
          <div class="avatar-option" data-avatar="🎯" onclick="selectAvatar('🎯',this)">🎯</div>
        </div>
      </div>

      <div class="settings-field">
        <label for="prof-course">Course / Programme</label>
        <input id="prof-course" type="text" placeholder="e.g. Computer Science BSc">
      </div>

      <div class="settings-field">
        <label for="prof-year">Year of study</label>
        <select id="prof-year">
          <option value="">— select —</option>
          <option value="1">Year 1</option>
          <option value="2">Year 2</option>
          <option value="3">Year 3</option>
          <option value="4">Year 4</option>
          <option value="5">Year 5</option>
          <option value="6">Year 6 / Postgraduate</option>
        </select>
      </div>

      <div>
        <div class="settings-section-title">Learning style</div>
        <div class="settings-radio-group" id="prof-style">
          <label class="settings-radio-opt"><input type="radio" name="learn_style" value="visual"> Visual</label>
          <label class="settings-radio-opt"><input type="radio" name="learn_style" value="auditory"> Auditory</label>
          <label class="settings-radio-opt"><input type="radio" name="learn_style" value="reading_writing"> Reading / Writing</label>
          <label class="settings-radio-opt"><input type="radio" name="learn_style" value="kinesthetic"> Kinesthetic</label>
        </div>
      </div>

      <div class="settings-actions">
        <button class="btn-primary" onclick="saveProfile()" style="padding:8px 24px">Save Profile</button>
        <button class="btn-sm" onclick="loadProfileForm()">Cancel</button>
      </div>
    </div>

    <!-- ── Learning ── -->
    <div id="settings-learning" class="settings-panel">
      <div>
        <div class="settings-section-title">Daily study goal</div>
        <div class="setting-slider-row">
          <input type="range" class="setting-slider" id="learn-goal" min="15" max="240" step="15" value="60"
                 oninput="document.getElementById('learn-goal-val').textContent=this.value+' min'">
          <span class="setting-slider-val" id="learn-goal-val">60 min</span>
        </div>
      </div>

      <div>
        <div class="settings-section-title">Preferred session length</div>
        <div class="settings-radio-group">
          <label class="settings-radio-opt"><input type="radio" name="sess_len" value="25"> 25 min</label>
          <label class="settings-radio-opt"><input type="radio" name="sess_len" value="45" checked> 45 min</label>
          <label class="settings-radio-opt"><input type="radio" name="sess_len" value="90"> 90 min</label>
        </div>
      </div>

      <div>
        <div class="settings-section-title">Reminder preference</div>
        <div class="settings-radio-group">
          <label class="settings-radio-opt"><input type="radio" name="reminder" value="none" checked> None</label>
          <label class="settings-radio-opt"><input type="radio" name="reminder" value="morning"> Morning</label>
          <label class="settings-radio-opt"><input type="radio" name="reminder" value="evening"> Evening</label>
        </div>
      </div>

      <div class="settings-actions">
        <button class="btn-primary" onclick="saveLearningPrefs()" style="padding:8px 24px">Save Preferences</button>
      </div>
    </div>
  </div>
</div>"""

APP_CLOSE_MARKER = """\
</div><!-- #app -->"""

NEW_APP_CLOSE = RESOURCES_PAGE + "\n\n" + SETTINGS_PAGE + "\n\n" + APP_CLOSE_MARKER

content = replace_once(content, APP_CLOSE_MARKER, NEW_APP_CLOSE, "Add Resources and Settings pages before #app close")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7 — Add JS (Theme, Timer, Settings) before </script>
# ═══════════════════════════════════════════════════════════════════════════
EXTRA_JS = """\
// ── Theme management ──────────────────────────────────────────────────────
function applyTheme(theme) {
  const html = document.documentElement;
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    html.setAttribute('data-theme', prefersDark ? 'dark' : 'bright');
  } else {
    html.setAttribute('data-theme', theme);
  }
  localStorage.setItem('sm_theme', theme);
}
function selectTheme(theme) {
  applyTheme(theme);
  document.querySelectorAll('.theme-option').forEach(el => {
    el.classList.toggle('selected', el.dataset.themeVal === theme);
  });
}
// Init theme on load
(function() {
  const saved = localStorage.getItem('sm_theme') || 'dark';
  applyTheme(saved);
  // Highlight correct option when already rendered
  document.querySelectorAll('.theme-option').forEach(el => {
    el.classList.toggle('selected', el.dataset.themeVal === saved);
  });
})();

// ── Focus Timer ────────────────────────────────────────────────────────────
let _timerInterval  = null;
let _timerRunning   = false;
let _timerRemaining = 25 * 60;
let _timerTotal     = 25 * 60;

function timerToggle() {
  if (_timerRunning) {
    clearInterval(_timerInterval); _timerInterval = null; _timerRunning = false;
    document.getElementById('timer-start-btn').textContent = '▶ Resume';
  } else {
    if (_timerInterval) clearInterval(_timerInterval);
    const inp = document.getElementById('timer-duration-input');
    if (!_timerRunning && _timerRemaining === _timerTotal) {
      _timerTotal = (parseInt(inp.value) || 25) * 60;
      _timerRemaining = _timerTotal;
    }
    _timerRunning = true;
    document.getElementById('timer-start-btn').textContent = '⏸ Pause';
    document.getElementById('timer-complete-msg').style.display = 'none';
    _timerInterval = setInterval(() => {
      if (_timerRemaining <= 0) {
        clearInterval(_timerInterval); _timerInterval = null; _timerRunning = false;
        document.getElementById('timer-start-btn').textContent = '▶ Start';
        document.getElementById('timer-status-label').textContent = 'Done!';
        document.getElementById('timer-complete-msg').style.display = 'block';
        timerUpdateDisplay(0);
        return;
      }
      _timerRemaining--;
      timerUpdateDisplay(_timerRemaining);
    }, 1000);
  }
  timerUpdateStatus();
}

function timerReset() {
  clearInterval(_timerInterval); _timerInterval = null; _timerRunning = false;
  const inp = document.getElementById('timer-duration-input');
  _timerTotal = (parseInt(inp.value) || 25) * 60;
  _timerRemaining = _timerTotal;
  timerUpdateDisplay(_timerRemaining);
  document.getElementById('timer-start-btn').textContent = '▶ Start';
  document.getElementById('timer-status-label').textContent = 'Ready';
  document.getElementById('timer-complete-msg').style.display = 'none';
}

function timerUpdateDisplay(seconds) {
  const m = Math.floor(seconds / 60), s = seconds % 60;
  const disp = document.getElementById('focus-timer-display');
  if (disp) disp.textContent = String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
  const ring = document.getElementById('timer-ring');
  if (ring) {
    const pct = _timerTotal > 0 ? seconds / _timerTotal : 1;
    ring.style.strokeDashoffset = 326.7 * (1 - pct);
  }
}

function timerUpdateStatus() {
  const lbl = document.getElementById('timer-status-label');
  if (lbl) lbl.textContent = _timerRunning ? 'Focusing' : 'Paused';
}

(function() {
  const inp = document.getElementById('timer-duration-input');
  if (inp) inp.addEventListener('change', function() { if (!_timerRunning) timerReset(); });
})();

// ── Settings page helpers ──────────────────────────────────────────────────
function openSettingsTab(tab, btn) {
  document.querySelectorAll('.settings-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.settings-panel').forEach(p => p.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const panel = document.getElementById('settings-' + tab);
  if (panel) panel.classList.add('active');
  if (tab === 'appearance') {
    const saved = localStorage.getItem('sm_theme') || 'dark';
    document.querySelectorAll('.theme-option').forEach(el => {
      el.classList.toggle('selected', el.dataset.themeVal === saved);
    });
  }
}

// Profile
let _selectedAvatar = '🎓';
function selectAvatar(emoji, el) {
  _selectedAvatar = emoji;
  document.querySelectorAll('.avatar-option').forEach(a => a.classList.remove('selected'));
  if (el) el.classList.add('selected');
  const ta = document.getElementById('topbar-avatar-display');
  if (ta) ta.textContent = emoji;
}

function loadProfileForm() {
  try {
    const p = JSON.parse(localStorage.getItem('sm_profile') || '{}');
    const fn = document.getElementById('prof-name'); if (fn) fn.value = p.name || '';
    const fc = document.getElementById('prof-course'); if (fc) fc.value = p.course || '';
    const fy = document.getElementById('prof-year'); if (fy) fy.value = p.year || '';
    const av = p.avatar || '🎓';
    _selectedAvatar = av;
    document.querySelectorAll('.avatar-option').forEach(a => {
      a.classList.toggle('selected', a.dataset.avatar === av);
    });
    const ta = document.getElementById('topbar-avatar-display');
    if (ta) ta.textContent = av;
    if (p.style) {
      const r = document.querySelector('input[name="learn_style"][value="'+p.style+'"]');
      if (r) r.checked = true;
    }
  } catch(_) {}
}

function saveProfile() {
  const style = (document.querySelector('input[name="learn_style"]:checked') || {}).value || '';
  const profile = {
    name:   (document.getElementById('prof-name') || {}).value || '',
    course: (document.getElementById('prof-course') || {}).value || '',
    year:   (document.getElementById('prof-year') || {}).value || '',
    avatar: _selectedAvatar,
    style,
  };
  localStorage.setItem('sm_profile', JSON.stringify(profile));
  const ta = document.getElementById('topbar-avatar-display');
  if (ta) ta.textContent = profile.avatar;
  alert('Profile saved!');
}

// Learning prefs
function loadLearningPrefs() {
  try {
    const p = JSON.parse(localStorage.getItem('sm_learning_prefs') || '{}');
    const g = document.getElementById('learn-goal');
    if (g && p.goal) { g.value = p.goal; document.getElementById('learn-goal-val').textContent = p.goal + ' min'; }
    if (p.session_len) {
      const r = document.querySelector('input[name="sess_len"][value="'+p.session_len+'"]');
      if (r) r.checked = true;
    }
    if (p.reminder) {
      const r = document.querySelector('input[name="reminder"][value="'+p.reminder+'"]');
      if (r) r.checked = true;
    }
  } catch(_) {}
}

function saveLearningPrefs() {
  const prefs = {
    goal:        (document.getElementById('learn-goal') || {}).value || '60',
    session_len: (document.querySelector('input[name="sess_len"]:checked') || {}).value || '45',
    reminder:    (document.querySelector('input[name="reminder"]:checked') || {}).value || 'none',
  };
  localStorage.setItem('sm_learning_prefs', JSON.stringify(prefs));
  alert('Learning preferences saved!');
}

// Init settings from localStorage on load
loadProfileForm();
loadLearningPrefs();

// ── Welcome banner init ────────────────────────────────────────────────────
(function initWelcomeBanner() {
  const now  = new Date();
  const hour = now.getHours();
  const greet = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const wbg = document.getElementById('wb-greeting');
  if (wbg) wbg.textContent = greet + ' 👋';
  const wbd = document.getElementById('wb-date');
  if (wbd) wbd.textContent = now.toLocaleDateString('en-GB', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
  // Populate from QUOTES array (already defined above)
  const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000);
  const q = QUOTES[dayOfYear % QUOTES.length];
  const wbq = document.getElementById('wb-quote');
  const wba = document.getElementById('wb-author-text');
  if (wbq) wbq.textContent = '\\u201C' + q.q + '\\u201D';
  if (wba) wba.textContent = '\\u2014 ' + q.a;
})();
"""

OLD_SCRIPT_END = """\
</script>"""

NEW_SCRIPT_END = EXTRA_JS + "\n</script>"

content = replace_once(content, OLD_SCRIPT_END, NEW_SCRIPT_END, "Add Theme/Timer/Settings JS before </script>")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 8 — Verify page boundaries
# ═══════════════════════════════════════════════════════════════════════════
print("\nVerifying page boundaries…")
pages_to_check = [
    "page-home", "page-tutor", "page-planner",
    "page-myplans", "page-quiz", "page-resources", "page-settings"
]
all_ok = True
for pg in pages_to_check:
    idx = content.find(f'id="{pg}"')
    if idx < 0:
        print(f"  ✗ MISSING: {pg}")
        all_ok = False
        continue
    before = content[idx-5:idx]
    if before != "<div ":
        print(f"  ✗ BAD BOUNDARY [{pg}]: chars before id= are [{repr(before)}]")
        all_ok = False
    else:
        print(f"  ✓ {pg}")

if not all_ok:
    print("\nBoundary check failed — aborting without saving.")
    sys.exit(1)

# Check that progress page is still gone
if 'id="page-progress"' in content:
    print("  ✗ page-progress found — should be absent!")
    sys.exit(1)
print("  ✓ page-progress absent (correct)")

# Check nav items exist
print("\nVerifying nav items…")
for page in ["home", "tutor", "planner", "myplans", "quiz", "resources", "settings"]:
    marker = f'data-page="{page}"'
    count = content.count(marker)
    if count < 1:
        print(f"  ✗ Nav item missing for {page}")
        all_ok = False
    else:
        print(f"  ✓ {page} nav item present ({count}x)")

# Check key JS functions still present
print("\nVerifying JS functions…")
for fn in ["handleDecisions", "generatePlan", "sendQuiz", "showTyping", "hideTyping"]:
    if fn not in content:
        print(f"  ✗ Missing JS function: {fn}")
        all_ok = False
    else:
        print(f"  ✓ {fn}")

# Check dec element still in DOM
if 'id="dec"' not in content:
    print("  ✗ #dec element missing from DOM!")
    all_ok = False
else:
    print("  ✓ #dec element present")

if not all_ok:
    print("\nVerification failed — aborting without saving.")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# STEP 9 — Save
# ═══════════════════════════════════════════════════════════════════════════
HTML_PATH.write_text(content, encoding="utf-8")
new_size = len(content)
print(f"\n✅ Saved {HTML_PATH}")
print(f"   Size: {original_size:,} → {new_size:,} bytes (+{new_size - original_size:,})")
print(f"   Lines: {content.count(chr(10))+1:,}")
print(f"\nChanges applied ({len(changes)}):")
for i, c in enumerate(changes, 1):
    print(f"  {i}. {c}")
print("\nDone.")
