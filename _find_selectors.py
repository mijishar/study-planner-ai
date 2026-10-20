html = open('demo/static/index.html', encoding='utf-8').read()
import re

# Find the actual chat input and form
for needle in ['id="m"', 'id="tutor-m"', 'tutor-form', 'tutor-img', 'dataset.turns', '#m']:
    idx = html.find(needle)
    if idx >= 0:
        print(f'FOUND {needle!r}: ...{html[idx:idx+80]}')
    else:
        print(f'NOT FOUND: {needle!r}')

print()
# Find all input ids
import re
input_ids = re.findall(r'<input[^>]+id="([^"]+)"', html)
print('All input ids:', input_ids[:20])

form_ids = re.findall(r'<form[^>]+id="([^"]+)"', html)
print('All form ids:', form_ids)

# Find what the tutor form submit does
tutor_form_idx = html.find('id="tutor-form"')
if tutor_form_idx >= 0:
    print('\nTutor form context:')
    print(html[tutor_form_idx:tutor_form_idx+200])

# Find the tutor message input
tutor_m_idx = html.find('id="tutor-m"')
if tutor_m_idx >= 0:
    print('\nTutor message input:')
    print(html[tutor_m_idx:tutor_m_idx+100])
