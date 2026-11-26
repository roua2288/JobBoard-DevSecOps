"""Authenticated dynamic regression checks against a disposable live target you own."""
import io
import os
import re
import time
import requests
from pypdf import PdfWriter
BASE=os.environ.get('TARGET_URL','http://127.0.0.1:8000')
assert BASE.startswith(('http://127.0.0.1:','http://localhost:')), 'Only localhost targets are allowed by this script.'
for _ in range(40):
    try:
        if requests.get(BASE+'/health',timeout=2).status_code==200:break
    except requests.RequestException:pass
    time.sleep(.25)
else:raise RuntimeError('Target did not become ready')
def post(s,path,data=None,files=None):
    html=s.get(BASE+'/login',timeout=5).text
    token=re.search(r'name="csrf" value="([^"]+)"',html).group(1)
    return s.post(BASE+path,data={'csrf':token,**(data or {})},files=files,timeout=5,allow_redirects=False)
def login(email):
    s=requests.Session()
    assert post(s,'/login',dict(email=email,password=os.environ['DEMO_PASSWORD'])).status_code==302
    return s
candidate=login('roua@example.test');recruiter=login('ahmed@example.test');other=login('other@example.test')
b=io.BytesIO();w=PdfWriter();w.add_blank_page(width=200,height=200);w.write(b)
assert post(candidate,'/cv/upload',files={'cv':('cv.pdf',b.getvalue(),'application/pdf')}).status_code==302
html=candidate.get(BASE+'/dashboard',timeout=5).text
cv=int(re.findall(r'href="/cv/(\d+)"',html)[-1])
assert other.get(BASE+f'/cv/{cv}',timeout=5).status_code==403
assert recruiter.get(BASE+f'/cv/{cv}',timeout=5).status_code==403
assert post(candidate,'/jobs/1/apply',{'cv':str(cv)}).status_code==302
assert recruiter.get(BASE+f'/cv/{cv}',timeout=5).status_code==200
assert other.get(BASE+f'/cv/{cv}',timeout=5).status_code==403
assert post(candidate,'/cv/upload',files={'cv':('bad.pdf',b'<script>bad</script>','application/pdf')}).status_code==400
assert candidate.get(BASE+'/',params={'q':"' OR 1=1 --"},timeout=5).status_code==200
assert post(candidate,'/admin/jobs/1',{'status':'active'}).status_code==403
print('PASS: authenticated CV isolation, application flow, invalid upload, SQL query, role checks')
