import json,pathlib,sys,requests
root=pathlib.Path(__file__).resolve().parents[1]
record=json.loads((root/'artifacts/scratch-upload.json').read_text())
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0','X-CSRFToken':'a','X-Requested-With':'XMLHttpRequest','Referer':'https://scratch.mit.edu/'})
s.cookies.set('scratchcsrftoken','a',domain='.scratch.mit.edu');s.cookies.set('scratchlanguage','en',domain='.scratch.mit.edu')
password=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').strip()
r=s.post('https://scratch.mit.edu/login/',json={'username':record['owner'],'password':password},timeout=30);del password;r.raise_for_status()
r=s.get('https://scratch.mit.edu/session/',timeout=30);r.raise_for_status();user=r.json().get('user') or {}
assert user.get('username','').lower()==record['owner'].lower(),'Signed-in account mismatch'
s.headers['X-Token']=user['token'];url='https://api.scratch.mit.edu/projects/'+record['id']
r=s.get(url,timeout=30);r.raise_for_status();before=r.json();assert before['author']['username'].lower()==record['owner'].lower()
expected=json.loads((root/'artifacts/scratch-published-first-repair.json').read_text())
fixed=json.loads((root/'artifacts/scratch-repaired-project.json').read_text())
project_url='https://projects.scratch.mit.edu/'+record['id']
r=s.get(project_url,params={'token':before['project_token']},timeout=40);r.raise_for_status()
assert r.json()==expected,'Online project changed since diagnosis; refusing to overwrite newer edits'
r=s.put(project_url,json=fixed,timeout=60);r.raise_for_status()
r=s.get(url,timeout=30);r.raise_for_status();after=r.json()
assert after['description']==before['description'] and after['instructions']==before['instructions'] and after['title']==before['title']
r=s.get(project_url,params={'token':after['project_token']},timeout=40);r.raise_for_status();assert r.json()==fixed,'Uploaded project does not match repaired file'
print('Verified repaired project online; Notes and Credits, instructions, title, and published track preserved: '+record['url'])
