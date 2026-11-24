"""Run the generated Scratch physics numerically for course tuning."""

import pathlib, math
from course import DEFAULT_GOAL, DEFAULT_SPAWN

root=pathlib.Path(__file__).resolve().parent

src=(root/'core.py').read_text(encoding='utf-8-sig');a=src.index('def proc(');b=src.index('\ndef call(',a);src=src[:a]+"procedures={}\ndef proc(name,seq):procedures[name]=seq\n"+src[b:]

ns={'__file__':str(root/'core.py')};exec(src,ns)

b=(root/'build.py').read_text(encoding='utf-8-sig');b=b[b.index('def join('):b.index('# Whole-stroke')];b=b[:b.index('basechain=')]+b[b.index("for k in ['Grid keys'"):]

ns.update(FIELDS=['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY'],META=[],DEFAULT_GOAL=DEFAULT_GOAL,DEFAULT_SPAWN=DEFAULT_SPAWN);exec(b,ns)

exec(next(line for line in (root/'build.py').read_text().splitlines() if line.startswith("proc('check result'")),ns)

E=ns['Expr'];v={k:a[1] for k,a in ns['variables'].items()};l={k:a[1][:] for k,a in ns['lists'].items()}

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

def compile_seq(seq,d=1):

 out=[];indent=' '*d

 for s in seq:

  o=s[0]

  if o in ['repeat','if']:

   out.append(indent+('for _'+str(d)+' in range(round('+ex(s[1])+')):' if o=='repeat' else 'if '+ex(s[1])+':'));out+=compile_seq(s[2],d+1) or [indent+' pass']

   if o=='if' and s[3]:out.append(indent+'else:');out+=compile_seq(s[3],d+1)

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

fields=ns['FIELDS']

def run(lines,frames=300):

 for k in fields:l[k]=[]

 for x,y,xx,yy,m in lines:

  dx,dy=xx-x,yy-y;le=math.hypot(dx,dy)

  for k,z in zip(fields,[x,y,dx,dy,-dy/le,dx/le,1/le**2,m,min(x,xx)-10,max(x,xx)+10,min(y,yy)-10,max(y,yy)+10]):l[k].append(z)

 v.update({'Spawn X':DEFAULT_SPAWN[0],'Spawn Y':DEFAULT_SPAWN[1],'State':1,'Crash frames':0,'Lowest track':max(l['MaxY'])+80,'Goal X':1050,'Goal Y':next((y+(yy-y)*(1050-x)/(xx-x) for x,y,xx,yy,mat in lines if x<=1050<=xx),448),'Goal enabled':1});p['reset rider']();rows=[]

 for f in range(frames):

  p['physics frame']();p['check result']();x,y=l['X'],l['Y'];sx,sy=(x[2]-x[1])/15,(y[2]-y[1])/15;rx,ry=x[4]-x[0]-(x[3]-x[0])*5/17.5,y[4]-y[0]-(y[3]-y[0])*5/17.5

  rows.append(dict(frame=f+1,m=v['Mounted'],load=v['Support load'],seat=v['Seat load'],grips=[l['Grip force'][6],l['Grip force'][7]],ground=l['Ground contact'][:],contacts=l['Sled contact'][:],state=v['State'],failed=v['Flight failed'],h=-rx*sy+ry*sx,a=rx*sx+ry*sy,x=x[:],y=y[:]))

  if v['State'] in [3,4]:break

 return rows

if __name__=='__main__':

 from course import default_track

 r=run(default_track());print([(a['frame'],a['state'],round(a['h'],2),round(a['a'],2)) for a in r if a['frame']%5==0 or a['state']>2])

