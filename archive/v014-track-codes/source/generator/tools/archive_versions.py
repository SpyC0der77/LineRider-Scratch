"""Preserve builds, exact native source, and available generator snapshots."""
import argparse
import datetime
import hashlib
import json
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'archive'
REBUILD = '''"""Repack this version's exact native Scratch source and assets."""
import pathlib, zipfile
root = pathlib.Path(__file__).resolve().parent
with zipfile.ZipFile(root / 'rebuilt.sb3', 'w', zipfile.ZIP_DEFLATED) as z:
    for path in sorted((root / 'source' / 'native').rglob('*')):
        if path.is_file():
            z.write(path, path.relative_to(root / 'source' / 'native').as_posix())
print(root / 'rebuilt.sb3')
'''


def snapshot(path, label, generator=False):
    ARCHIVE.mkdir(exist_ok=True)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifests = sorted(ARCHIVE.glob('v*/manifest.json'))
    for existing in manifests:
        if json.loads(existing.read_text())['sha256'] == digest:
            return existing.parent
    folder = ARCHIVE / f'v{len(manifests):03d}-{label}'
    native = folder / 'source' / 'native'
    native.mkdir(parents=True)
    shutil.copy2(path, folder / 'Line Rider.sb3')
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            target = (native / name).resolve()
            if not target.is_relative_to(native.resolve()):
                raise ValueError('Unsafe zip member')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(name))
    (folder / 'rebuild.py').write_text(REBUILD)
    if generator:
        source = folder / 'source' / 'generator'
        shutil.copytree(ROOT / 'tools', source / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'reference', source / 'reference', ignore=shutil.ignore_patterns('node_modules', '.git'))
        for name in ['README.md', 'LICENSE.lr-core.txt']:
            shutil.copy2(ROOT / name, source / name)
        (source / 'dist').mkdir()
    elif label == 'original-demo':
        (folder / 'source' / 'historical-generator').mkdir()
        shutil.copy2(ROOT / 'tools' / 'build_v1.py', folder / 'source' / 'historical-generator' / 'build_v1.py')
    manifest = dict(version=folder.name, original_file=str(path.relative_to(ROOT)), sha256=digest,
                    original_modified=datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    archived=datetime.datetime.now().isoformat(), exact_native_source=True,
                    complete_python_generator=generator)
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    (folder / 'README.md').write_text(
        f'# {folder.name}\n\nOpen `Line Rider.sb3` in Scratch. `source/native/project.json` contains the exact executable Scratch blocks, variables, lists and costume metadata. All assets are beside it. Run `python rebuild.py` to repack them as `rebuilt.sb3`.\n\n' +
        ('The complete Python generator and its dependencies are preserved under `source/generator`. Run `python tools/build.py` from that directory to regenerate the project.\n' if generator else
         'The original complete Python generator for this older build was overwritten before archiving and cannot be recovered from this workspace. The exact native Scratch source and a working repacker are preserved. Any separately retained historical generator is identified as incomplete.\n'))
    print('Archived ' + folder.name)
    return folder


def index():
    rows = []
    for path in sorted(ARCHIVE.glob('v*/manifest.json')):
        m = json.loads(path.read_text())
        rows.append(f"| [{path.parent.name}]({path.parent.name}/README.md) | {m['original_file']} | {'Native + Python' if m['complete_python_generator'] else 'Exact native Scratch code'} |")
    (ARCHIVE / 'README.md').write_text('# Version archive\n\nEvery recovered `.sb3` is preserved unchanged, with its exact executable Scratch source, assets, SHA-256 checksum and a rebuild script. Historical test/save variants are included as separate snapshots. Earlier complete Python generators were not retained; those gaps are stated in each version. Current and future builds include the full Python generator.\n\n| Version | Original build | Preserved code |\n| --- | --- | --- |\n' + '\n'.join(rows) + '\n\n`python tools/build.py` archives each distinct new build automatically. Existing snapshots are never overwritten.\n')


def recover():
    names = {'before.sb3': 'blank-baseline', 'demo-v1.sb3': 'original-demo',
             'editor-buttons.sb3': 'editor-buttons', 'persistence.sb3': 'saved-slot-fixture',
             'before-step.sb3': 'dropdown-editor', 'before-mode-switch.sb3': 'single-frame-step',
             'before-course.sb3': 'mode-switch', 'before-edit-confirmation.sb3': 'normal-course',
             'before-connected-controls.sb3': 'edit-confirmation', 'before-smooth-course.sb3': 'connected-controls',
             'before-ragdoll.sb3': 'smooth-course'}
    for path in sorted((ROOT / 'artifacts').glob('*.sb3'), key=lambda p: p.stat().st_mtime):
        snapshot(path, names.get(path.name, path.stem.replace(' ', '-')))
    snapshot(ROOT / 'dist' / 'Line Rider.sb3', 'ragdoll', generator=True)
    recover_original_generator()
    index()


def recover_original_generator():
    """The retained standalone v1 script generated both the demo and baseline."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory(prefix='line-rider-generator-check-') as temp:
        source = pathlib.Path(temp)
        (source / 'tools').mkdir()
        (source / 'dist').mkdir()
        (source / 'artifacts').mkdir()
        shutil.copy2(ROOT / 'tools' / 'build_v1.py', source / 'tools' / 'build.py')
        shutil.copytree(ROOT / 'reference', source / 'reference', ignore=shutil.ignore_patterns('node_modules', '.git'))
        shutil.copy2(ROOT / 'LICENSE.lr-core.txt', source / 'LICENSE.lr-core.txt')
        subprocess.run(['python', str(source / 'tools' / 'build.py')], check=True, capture_output=True)
        for manifest_path in ARCHIVE.glob('v*/manifest.json'):
            manifest = json.loads(manifest_path.read_text())
            name = pathlib.Path(manifest['original_file']).name
            if name not in ['demo-v1.sb3', 'before.sb3']:
                continue
            output = 'dist/Line Rider.sb3' if name == 'demo-v1.sb3' else 'artifacts/before.sb3'
            with zipfile.ZipFile(source / output) as actual, zipfile.ZipFile(manifest_path.parent / 'Line Rider.sb3') as expected:
                assert set(actual.namelist()) == set(expected.namelist())
                for entry in actual.namelist():
                    if entry == 'project.json':
                        assert json.loads(actual.read(entry)) == json.loads(expected.read(entry))
                    else:
                        assert actual.read(entry) == expected.read(entry)
            generator = manifest_path.parent / 'source' / 'generator'
            if not generator.exists():
                shutil.copytree(source, generator, ignore=shutil.ignore_patterns('*.sb3', 'project.json', '__pycache__'))
            manifest.update(complete_python_generator=True, generator_verified_against_native=True, generator_output=output)
            manifest_path.write_text(json.dumps(manifest, indent=2))
            (manifest_path.parent / 'README.md').write_text(f"# {manifest_path.parent.name}\n\n`Line Rider.sb3` and `source/native` preserve this version exactly. Run `python rebuild.py` to repack it.\n\nThe original standalone Python generator is recovered under `source/generator` and has been verified to reproduce every native block and asset. Run `python tools/build.py` from that directory. This version is generated at `{output}`.\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--recover', action='store_true')
    parser.add_argument('--label', default='build')
    args = parser.parse_args()
    if args.recover:
        recover()
    else:
        snapshot(ROOT / 'dist' / 'Line Rider.sb3', args.label, generator=True)
        index()
