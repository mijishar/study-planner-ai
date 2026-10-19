html = open('demo/static/index.html', encoding='utf-8').read()
print(f"File size: {len(html)} chars")

# Page presence
pages = ['page-home','page-tutor','page-planner','page-myplans','page-quiz','page-progress']
for pg in pages:
    idx = html.find(f'id="{pg}"')
    before = html[idx-5:idx] if idx >= 5 else '?'
    print(f"  {pg}: {'PRESENT' if idx>=0 else 'ABSENT'} [{before}]")

# Nav items
nav_items = ['home','tutor','planner','myplans','quiz','progress']
for n in nav_items:
    present = f'data-page="{n}"' in html
    print(f"  nav {n}: {'YES' if present else 'NO'}")

# Key functions
fns = ['refreshProgress','DEMO_MASTERY','handleDecisions','generatePlan','sendQuiz']
for fn in fns:
    print(f"  {fn}: {'YES' if fn in html else 'NO'}")
