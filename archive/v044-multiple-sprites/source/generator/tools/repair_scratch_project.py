"""Repair Scratch GUI's dropped scalar reporters in boolean sockets, without changing content."""
import copy,json,pathlib,zipfile
root=pathlib.Path(__file__).resolve().parents[1]
p=json.loads((root/'artifacts/scratch-online-raw.json').read_text())
with zipfile.ZipFile(root/'archive/v030-multiple-sprites/Line Rider.sb3') as z:original=json.loads(z.read('project.json'))
count=0
for target in p['targets']:
 blocks=target['blocks'];source=next(t for t in original['targets'] if t['name']==target['name'])['blocks']
 for key,b in list(blocks.items()):
  if not isinstance(b,dict):continue
  for name,value in list(b['inputs'].items()):
   boolean = name == 'CONDITION' or b['opcode'] in ['operator_and','operator_or','operator_not']
   missing = len(value)>1 and isinstance(value[1],str) and value[1] not in blocks
   inline = boolean and len(value)>1 and isinstance(value[1],list) and value[1][0]==12
   if not (missing or inline):continue
   old=source[key]['inputs'][name] if missing else value
   assert old[0]==2 and old[1][0]==12,(key,name,old)
   reporter='repair-boolean-'+str(count)
   blocks[reporter]={'opcode':'operator_equals','next':None,'parent':key,'inputs':{'OPERAND1':[3,copy.deepcopy(old[1]),[10,'0']],'OPERAND2':[1,[10,'1']]},'fields':{},'shadow':False,'topLevel':False}
   b['inputs'][name]=[2,reporter];count+=1
 for key,b in blocks.items():
  if not isinstance(b,dict):continue
  for value in b['inputs'].values():
   for child in value[1:]:
    if isinstance(child,str):assert child in blocks,(target['name'],key,child)
assert count>=5,count
(root/'artifacts/scratch-repaired-project.json').write_text(json.dumps(p))
with zipfile.ZipFile(root/'artifacts/online-repro.sb3') as src,zipfile.ZipFile(root/'artifacts/Line Rider repaired.sb3','w',zipfile.ZIP_DEFLATED) as out:
 for n in src.namelist():out.writestr(n,json.dumps(p) if n=='project.json' else src.read(n))
print(f'Repaired {count} boolean sockets; preserved published track, assets, notes, and code layout.')
