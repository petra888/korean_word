from pathlib import Path
from datetime import datetime, timezone
import json, traceback
from playwright.sync_api import sync_playwright
root=Path('/workspace/korean_word/vocabulary-planning/qa/latest-commit-0d75986/mobile-print')
result={'utc':datetime.now(timezone.utc).isoformat(),'engine':'Chromium via Playwright','method':'one bounded headless launch, no HTTP server or network','launch_timeout_ms':10000,'status':'NOT RUN'}
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,timeout=10000,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':375,'height':812})
        page.goto('file:///tmp/vocabulary-full-qa-0d75986-n5h3m0i4/vocabulary-planning/prototype/pilot-flow.html',timeout=10000)
        result['status']='LAUNCH AVAILABLE'
        result['title']=page.title()
        browser.close()
except Exception as exc:
    result['status']='BLOCKED'
    result['error']=str(exc)
root.joinpath('browser-launch.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
