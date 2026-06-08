import os

html_files = []
for root, dirs, files in os.walk('public_html'):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

issues = []
for f in html_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    has_toggle = 'function toggleChat()' in content
    has_greeting_func = 'function getPageSpecificGreeting()' in content
    
    if has_toggle and not has_greeting_func:
        # Check if toggleChat actually calls it
        if 'getPageSpecificGreeting()' in content:
            issues.append(f"{f}: calls getPageSpecificGreeting() but it is missing!")

if issues:
    print("\n".join(issues))
else:
    print("All good.")
