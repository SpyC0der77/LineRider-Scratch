"""Compile the generator's physics procedures for fast course tuning."""
import math, pathlib, json
root=pathlib.Path(__file__).resolve().parent
src=(root/'core.py').read_text();a=src.index('def proc(');b=src.index('\ndef call(',a)
src=src[:a]+"procedures={}\ndef proc(name,seq): procedures[name]=seq\n"+src[b:]
ns={'__file__':str(root/'core.py')};exec(src,ns)
build=(root/'build.py').read_text();build=build[build.index('def join('):build.index('# Whole-stroke')];build=build[:build.index('basechain=')]+build[build.index("for k in ['Grid keys'"):];ns['FIELDS']=['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY'];ns['META']=[];ns['DEFAULT_GOAL']=(700,200);exec(build,ns)
E=ns['Expr']; v={k:a[1] for k,a in ns['variables'].items()}; l={k:a[1][:] for k,a in ns['lists'].items()}
def ex(e):
 if not isinstance(e,E):return repr(e)
 o=e.op.removeprefix('operator_');i=e.inputs;f=e.fields
 if o=='data_variable':return 'v['+repr(f['VARIABLE'][0])+']'
 if o=='data_itemoflist':return 'l['+repr(f['LIST'][0])+'][int('+ex(i['INDEX'])+')-1]'
 if o=='data_lengthoflist':return 'len(l['+repr(f['LIST'][0])+'])'
 if o in ['add','subtract','multiply','divide','equals','lt','gt','and','or']:
  keys=list(i);return '('+ex(i[keys[0]])+{'add':'+','subtract':'-','multiply':'*','divide':'/','equals':'==','lt':'<','gt':'>','and':' and ','or':' or '}[o]+ex(i[keys[1]])+')'
 if o=='not':return '(not '+ex(i['OPERAND'])+')'
 if o=='mathop':return {'abs':'abs','sqrt':'math.sqrt','floor':'math.floor','ceiling':'math.ceil'}[f['OPERATOR'][0]]+'('+ex(i['NUM'])+')'
 if o=='round':return 'round('+ex(i['NUM'])+')'
 raise ValueError(o)
def compile_seq(seq,depth=1):
 out=[];indent=' '*depth
 for s in seq:
  o=s[0]
  if o in ['repeat','if']:
   out.append(indent+('for _'+str(depth)+' in range(round('+ex(s[1])+')):' if o=='repeat' else 'if '+ex(s[1])+':'));out+=compile_seq(s[2],depth+1) or [indent+' pass']
   if o=='if' and s[3]:out.append(indent+'else:');out+=compile_seq(s[3],depth+1)
  elif o=='CALL':out.append(indent+'p['+repr(s[1])+']()')
  else:
   i,f=s[1:];key=repr(f.get('VARIABLE',f.get('LIST',['']))[0])
   if o=='data_setvariableto':line='v['+key+']='+ex(i['VALUE'])
   elif o=='data_changevariableby':line='v['+key+']+='+ex(i['VALUE'])
   elif o=='data_replaceitemoflist':line='l['+key+'][int('+ex(i['INDEX'])+')-1]='+ex(i['ITEM'])
   elif o=='data_deletealloflist':line='l['+key+'].clear()'
   elif o=='data_addtolist':line='l['+key+'].append('+ex(i['ITEM'])+')'
   else:raise ValueError(o)
   out.append(indent+line)
 return out
p={};env=dict(v=v,l=l,p=p,math=math)
for name,seq in ns['procedures'].items():
 if name in ['build spatial grid','nearby lines']:continue
 try:exec('def run():\n'+'\n'.join(compile_seq(seq)),env);p[name]=env['run']
 except ValueError:pass
def nearby():
 x,y=l['X'][int(v['i'])-1],l['Y'][int(v['i'])-1];l['Candidates']=[i+1 for i in range(len(l['LX'])) if l['MinX'][i]<=x<=l['MaxX'][i] and l['MinY'][i]<=y<=l['MaxY'][i]]
p['nearby lines']=nearby
fields=['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']
def track(lines):
 for k in fields:l[k]=[]
 for x,y,xx,yy,m in lines:
  dx,dy=xx-x,yy-y;le=math.hypot(dx,dy)
  for k,z in zip(fields,[x,y,dx,dy,-dy/le,dx/le,1/le**2,m,min(x,xx)-10,max(x,xx)+10,min(y,yy)-10,max(y,yy)+10]):l[k].append(z)
def run(lines,frames=300):
 track(lines);v.update({'Spawn X':0,'Spawn Y':0,'State':1,'Crash frames':0});p['reset rider']();rows=[]
 for f in range(frames):
  p['physics frame']();x,y=l['X'],l['Y'];sx,sy=(x[2]-x[1])/15,(y[2]-y[1])/15;rx,ry=x[4]-x[0]-(x[3]-x[0])*5/17.5,y[4]-y[0]-(y[3]-y[0])*5/17.5
  rows.append(dict(f=f+1,m=v['Mounted'],h=-rx*sy+ry*sx,a=rx*sx+ry*sy,contact=max(l['R contact depth'][4:10]+l['R contact depth'][17:]),x=x[:],y=y[:]))
  if not v['Mounted']:v['Crash frames']+=1
 return rows
if __name__=='__main__':
 from course import default_track
 rows=run(default_track(),125);print([(r['f'],r['m'],round(r['h'],2),round(r['contact'],2)) for r in rows[93:113]])
