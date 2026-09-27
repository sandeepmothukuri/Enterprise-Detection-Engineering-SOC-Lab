import glob
import os

files = glob.glob('dashboards/*.html')
count = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if 'soc-copilot.js' not in content:
        content = content.replace('</body>', '  <script src="soc-copilot.js"></script>\n</body>')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)
        count += 1
        print(f"[+] Injected soc-copilot.js into {os.path.basename(f)}")

print(f"Total injected: {count}")
