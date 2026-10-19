from pathlib import Path
html = Path('demo/static/index.html').read_text(encoding='utf-8')
pages = ['page-home','page-tutor','page-planner','page-myplans','page-quiz','page-resources','page-settings']
for p in pages:
    idx = html.find('id="%s"' % p)
    before = html[idx-5:idx]
    status = 'OK' if before == '<div ' else 'BAD: %r' % before
    print('  %s  %s' % (status, p))
print()
print('Resources page has links:', 'href="https://developer.mozilla.org"' in html)
print('Settings page has theme selector:', 'data-theme-val="dark"' in html)
print('Focus timer present:', 'focus-timer-card' in html)
print('Topbar present:', 'id="topbar"' in html)
print('Welcome banner present:', 'welcome-banner' in html)
print('Light theme CSS present:', '[data-theme="bright"]' in html)
print('Nav resources:', 'data-page="resources"' in html)
print('Nav settings:', 'data-page="settings"' in html)
print('Total size:', len(html), 'bytes')
