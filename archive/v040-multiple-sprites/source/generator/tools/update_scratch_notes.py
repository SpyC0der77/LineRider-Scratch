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
(root/'artifacts/scratch-notes-before.txt').write_text(before.get('description',''),encoding='utf-8')
notes=(root/'docs/scratch-notes.txt').read_text(encoding='utf-8-sig').rstrip('\r\n')
r=s.put(url,json={'description':notes},timeout=30);r.raise_for_status()
r=s.get(url,timeout=30);r.raise_for_status();after=r.json();assert after['description']==notes;assert after.get('instructions')==before.get('instructions');assert after['title']==before['title']
print('Verified Notes and Credits updated: '+record['url'])
