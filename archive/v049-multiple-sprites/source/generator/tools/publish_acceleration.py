"""Update the existing Scratch project, preserving its title and sharing state."""
import concurrent.futures
import hashlib
import json
import os
import pathlib
import sys
import zipfile

import requests


def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    sb3 = root / 'dist' / 'Line Rider.sb3'
    record = root / 'artifacts' / 'scratch-upload.json'
    if not record.exists():
        raise RuntimeError('Create an ignored artifacts/scratch-upload.json with the existing project id before uploading')
    local_record = json.loads(record.read_text(encoding='utf-8'))
    username = os.environ.get('SCRATCH_USERNAME') or local_record.get('owner')
    if not isinstance(username, str) or not username.strip():
        raise RuntimeError('Set SCRATCH_USERNAME or add owner to the ignored artifacts/scratch-upload.json')
    username = username.strip()
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-CSRFToken': 'a', 'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://scratch.mit.edu/',
    })
    session.cookies.set('scratchcsrftoken', 'a', domain='.scratch.mit.edu')
    session.cookies.set('scratchlanguage', 'en', domain='.scratch.mit.edu')
    password = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').strip()
    response = session.post('https://scratch.mit.edu/login/', json={'username': username, 'password': password}, timeout=30)
    del password
    if response.status_code != 200 or not session.cookies.get_dict().get('scratchsessionsid'):
        raise RuntimeError(f'Scratch login failed, HTTP {response.status_code}')
    info = session.get('https://scratch.mit.edu/session/', timeout=30)
    info.raise_for_status()
    user = info.json().get('user') or {}
    if user.get('username', '').lower() != username.lower():
        raise RuntimeError('Could not verify signed-in account')
    session.headers['X-Token'] = user['token']
    print('Signed in as ' + user['username'], flush=True)
    project_id = str(local_record['id'])
    before_response = session.get(f'https://api.scratch.mit.edu/projects/{project_id}', timeout=30)
    before_response.raise_for_status()
    before = before_response.json()
    if before.get('author', {}).get('username', '').lower() != username.lower():
        raise RuntimeError('Project owner mismatch')
    was_shared = bool(before.get('history', {}).get('shared'))
    notes = (root/'docs'/'scratch-notes.txt').read_text(encoding='utf-8-sig').rstrip('\r\n')
    remote_response = session.get(f'https://projects.scratch.mit.edu/{project_id}', params={'token':before['project_token']}, timeout=40)
    remote_response.raise_for_status()
    try:
        remote_project = remote_response.json()
    except ValueError:
        import io
        with zipfile.ZipFile(io.BytesIO(remote_response.content)) as archive:
            remote_project = json.loads(archive.read('project.json'))
    snapshot=json.loads((root/'artifacts/pre-acceleration-project.json').read_text())
    snapshot_stage=next(t for t in snapshot['targets'] if t['isStage'])
    expected={'lists':{v[0]:v[1] for v in snapshot_stage['lists'].values()},'flags':{v[0]:v[1] for v in snapshot_stage['variables'].values() if v[0] in ['Spawn X','Spawn Y','Goal X','Goal Y','Goal enabled']}}
    remote_stage = next(t for t in remote_project['targets'] if t['isStage'])
    remote_lists = {v[0]:v[1] for v in remote_stage['lists'].values()}
    remote_variables = {v[0]:v[1] for v in remote_stage['variables'].values()}
    if any([float(v) for v in remote_lists[k]] != [float(v) for v in expected['lists'][k]] for k in ['LX','LY','DX','DY','Material']) or any(float(remote_variables[k]) != float(v) for k,v in expected['flags'].items()):
        raise RuntimeError('The online track changed during this task; refresh the preserved canvas before uploading')
    with zipfile.ZipFile(sb3) as archive:
        project = json.loads(archive.read('project.json'))
        assets = {name: archive.read(name) for name in archive.namelist() if name != 'project.json' and not name.endswith('/')}
    for name, data in assets.items():
        if hashlib.md5(data).hexdigest() != name.split('.')[0]:
            raise RuntimeError('Invalid asset checksum: ' + name)
    headers, cookies = dict(session.headers), session.cookies.get_dict()
    def upload(item):
        name, data = item
        result = requests.post('https://assets.scratch.mit.edu/' + name, headers=headers, cookies=cookies, data=data, timeout=45)
        if result.status_code not in (200, 201):
            raise RuntimeError(f'Asset upload failed, HTTP {result.status_code}')
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for index, _ in enumerate(pool.map(upload, assets.items()), 1):
            if index % 40 == 0 or index == len(assets):
                print(f'Uploaded {index}/{len(assets)} assets', flush=True)
    result = session.put(f'https://projects.scratch.mit.edu/{project_id}', json=project, timeout=60)
    result.raise_for_status()
    result = session.put(f'https://api.scratch.mit.edu/projects/{project_id}', json={'description':notes, 'instructions':''}, timeout=30)
    result.raise_for_status()
    metadata_response = session.get(f'https://api.scratch.mit.edu/projects/{project_id}', timeout=30)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    if metadata.get('author', {}).get('username', '').lower() != username.lower():
        raise RuntimeError('Project owner mismatch')
    if bool(metadata.get('history', {}).get('shared')) != was_shared:
        raise RuntimeError('Project sharing state changed unexpectedly')
    if metadata.get('description') != notes or metadata.get('instructions') != '':
        raise RuntimeError('Notes or instructions do not match the requested text')
    if metadata.get('title') != before.get('title'):
        raise RuntimeError('Project title changed unexpectedly')
    download = session.get(f'https://projects.scratch.mit.edu/{project_id}', params={'token': metadata['project_token']}, timeout=60)
    download.raise_for_status()
    try:
        stored_project = download.json()
    except ValueError:
        import io
        with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
            stored_project = json.loads(archive.read('project.json'))
    if stored_project != project:
        raise RuntimeError('Saved project does not match the local sb3')
    public = requests.get(f'https://api.scratch.mit.edu/projects/{project_id}', timeout=30)
    if was_shared and public.status_code != 200 or not was_shared and public.status_code not in (403,404):
        raise RuntimeError(f'Could not verify project visibility, anonymous API HTTP {public.status_code}')
    summary = {'id': str(project_id), 'url': f'https://scratch.mit.edu/projects/{project_id}/', 'title': metadata['title'], 'owner': metadata['author']['username'], 'shared': was_shared, 'verified': True, 'notes_verified':True, 'instructions_blank':True, 'source_sha256': hashlib.sha256(sb3.read_bytes()).hexdigest(), 'assets': len(assets), 'blocks': sum(len(t['blocks']) for t in project['targets'])}
    record.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)
    session.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error).split('?')[0], file=sys.stderr)
        sys.exit(1)
