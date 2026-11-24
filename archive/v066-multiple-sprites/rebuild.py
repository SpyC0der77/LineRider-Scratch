"""Repack this version's exact native Scratch source and assets."""
import pathlib, zipfile
root = pathlib.Path(__file__).resolve().parent
with zipfile.ZipFile(root / 'rebuilt.sb3', 'w', zipfile.ZIP_DEFLATED) as z:
    for path in sorted((root / 'source' / 'native').rglob('*')):
        if path.is_file():
            z.write(path, path.relative_to(root / 'source' / 'native').as_posix())
print(root / 'rebuilt.sb3')
