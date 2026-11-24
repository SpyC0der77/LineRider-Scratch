import json, math, hashlib, zipfile, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
B={}; variables={}; lists={}; n=0
class Expr:
 def __init__(self,op,inputs={},fields={}):self.op,self.inputs,self.fields=op,inputs,fields
 def __add__(a,b):return op('add',a,b)
 def __sub__(a,b):return op('subtract',a,b)
 def __mul__(a,b):return op('multiply',a,b)
 def __truediv__(a,b):return op('divide',a,b)
Expr.__rsub__=lambda a,b:op('subtract',b,a)
Expr.__radd__=lambda a,b:op('add',b,a)
Expr.__rmul__=lambda a,b:op('multiply',b,a)
Expr.__rtruediv__=lambda a,b:op('divide',b,a)
def op(o,a,b):return Expr('operator_'+o,{'NUM1':a,'NUM2':b})
def cmp(o,a,b):return Expr('operator_'+o,{'OPERAND1':a,'OPERAND2':b})
def AND(a,b):return Expr('operator_and',{'OPERAND1':a,'OPERAND2':b})
def OR(a,b):return Expr('operator_or',{'OPERAND1':a,'OPERAND2':b})
def mathop(o,a):return Expr('operator_round',{'NUM':a}) if o=='round' else Expr('operator_mathop',{'NUM':a},{'OPERATOR':[o,None]})
def V(k):variables.setdefault(k,[k,0]);return Expr('data_variable',{}, {'VARIABLE':[k,k]})
def L(k,i):return Expr('data_itemoflist',{'INDEX':i},{'LIST':[k,k]})
def length(k):return Expr('data_lengthoflist',{}, {'LIST':[k,k]})
def emit(o,inputs={},fields={},parent=None,**extra):
 global n
 if o=='CALL':return emit('procedures_call',{}, {},parent,mutation={'tagName':'mutation','children':[],'proccode':inputs,'argumentids':'[]','warp':'true'})
 n+=1;id='b'+str(n);B[id]={'opcode':o,'next':None,'parent':parent,'inputs':{},'fields':fields,'shadow':False,'topLevel':False,**extra}
 for k,v in inputs.items():
  if isinstance(v,Expr):r=emit(v.op,v.inputs,v.fields,id);B[id]['inputs'][k]=[2,r]
  else:B[id]['inputs'][k]=[1,[10,str(v)]]
 return id
def stmt(o,inputs={},fields={}):return (o,inputs,fields)
def setv(k,v):V(k);return stmt('data_setvariableto',{'VALUE':v},{'VARIABLE':[k,k]})
def change(k,v):V(k);return stmt('data_changevariableby',{'VALUE':v},{'VARIABLE':[k,k]})
def replace(k,i,v):return stmt('data_replaceitemoflist',{'INDEX':i,'ITEM':v},{'LIST':[k,k]})
def add(k,v):return stmt('data_addtolist',{'ITEM':v},{'LIST':[k,k]})
def clear(k):return stmt('data_deletealloflist',{}, {'LIST':[k,k]})
def loop(times,body):return ('repeat',times,body)
def iff(c,body,other=None):return ('if',c,body,other)
def chain(seq,parent):
 first=None;prev=None
 for s in seq:
  if s[0] in ('repeat','if','forever'):
   typ=s[0];id=emit({'repeat':'control_repeat','if':'control_if_else' if typ=='if' and s[3] else 'control_if','forever':'control_forever'}[typ],{'TIMES':s[1]} if typ=='repeat' else {'CONDITION':s[1]} if typ=='if' else {},parent=prev or parent)
   body=s[2] if typ!='forever' else s[1];sub=chain(body,id)
   if sub:B[id]['inputs']['SUBSTACK']=[2,sub]
   if typ=='if' and s[3]:B[id]['inputs']['SUBSTACK2']=[2,chain(s[3],id)]
  else:id=emit(*s,parent=prev or parent)
  if prev:B[prev]['next']=id
  else:first=id
  prev=id
 return first
def script(hat,seq,fields={}):
 id=emit(hat,fields=fields,topLevel=True,x=20,y=n*2);B[id]['next']=chain(seq,id);return id
def proc(name,seq):
 d=emit('procedures_definition',topLevel=True,x=500,y=n*2);p=emit('procedures_prototype',parent=d,shadow=True,mutation={'tagName':'mutation','children':[],'proccode':name,'argumentids':'[]','argumentnames':'[]','argumentdefaults':'[]','warp':'true'});B[d]['inputs']['custom_block']=[1,p];B[d]['next']=chain(seq,d)
def call(name):return ('CALL',name,{})
def goto(x,y):return stmt('motion_gotoxy',{'X':x,'Y':y})
def color(c):return stmt('pen_setPenColorToColor',{'COLOR':c})
def size(s):return stmt('pen_setPenSizeTo',{'SIZE':s})
def key(k):return Expr('sensing_keypressed',{'KEY_OPTION':k})
body=json.loads((ROOT/'reference/lr-core/src/line-rider-engine/rider-data/index.json').read_text())
from ragdoll import extend_rider
body=extend_rider(body)
pts=[p for p in body['states'] if p['type']!='Binding'];idx={p['id']:i+1 for i,p in enumerate(pts)}
for k in ['X','Y','PX','PY','VX','VY','Friction','Air','Initial X','Initial Y']:lists[k]=[k,[]]
for p in pts:
 for k,val in [('X',p['x']),('Y',p['y']),('PX',p['x']-.4),('PY',p['y']),('VX',.4),('VY',0),('Friction',p.get('friction',0)),('Air',p.get('airFriction',0)),('Initial X',p['x']),('Initial Y',p['y'])]:lists[k][1].append(val)
cons=[c for c in body['constraints'] if c['type'] in ['Stick','BindStick','RepelStick']]
for k in ['CA','CB','Rest','Kind','Endurance']:lists[k]=[k,[]]
for c in cons:
 a,b=idx[c['p1']],idx[c['p2']];r=math.hypot(pts[a-1]['x']-pts[b-1]['x'],pts[a-1]['y']-pts[b-1]['y'])*c.get('lengthFactor',1)
 for k,v in [('CA',a),('CB',b),('Rest',r),('Kind',{'Stick':0,'BindStick':1,'RepelStick':2}[c['type']]),('Endurance',c.get('endurance',0)*r*.5)]:lists[k][1].append(v)
from course import default_track
tracks=default_track()
for k in ['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']:lists[k]=[k,[]]
for x,y,xx,yy,m in tracks:
 dx,dy=xx-x,yy-y;le=math.hypot(dx,dy)
 for k,v in [('LX',x),('LY',y),('DX',dx),('DY',dy),('NX',-dy/le),('NY',dx/le),('InvSq',1/le**2),('Material',m),('MinX',min(x,xx)-10),('MaxX',max(x,xx)+10),('MinY',min(y,yy)-10),('MaxY',max(y,yy)+10)]:lists[k][1].append(v)
lists['Candidates']=['Candidates',[]]
proc('reset rider',[setv('i',1),loop(len(pts),[replace('X',V('i'),L('Initial X',V('i'))+V('Spawn X')),replace('Y',V('i'),L('Initial Y',V('i'))+V('Spawn Y')),replace('PX',V('i'),L('Initial X',V('i'))+V('Spawn X')-.4),replace('PY',V('i'),L('Initial Y',V('i'))+V('Spawn Y')),replace('VX',V('i'),.4),replace('VY',V('i'),0),replace('Air',V('i'),L('Initial air',V('i'))),change('i',1)]),setv('Ragdoll active',0),setv('Ragdoll sleep frames',0),setv('Ragdoll speed squared',0),setv('Crash complete',0),setv('Preserve contact velocity',0),setv('Mounted',1),setv('Sled intact',1),setv('Frame',0),setv('Camera X',0),setv('Camera Y',0),call('update ragdoll pose'),call('begin ragdoll contacts')])
proc('integrate points',[setv('i',1),loop(len(pts),[iff(OR(cmp('lt',V('i'),18),cmp('equals',V('Ragdoll active'),1)),[setv('vx',(L('X',V('i'))-L('PX',V('i')))*(1-L('Air',V('i')))),setv('vy',(L('Y',V('i'))-L('PY',V('i')))*(1-L('Air',V('i')))+.175),replace('VX',V('i'),V('vx')),replace('VY',V('i'),V('vy')),replace('PX',V('i'),L('X',V('i'))),replace('PY',V('i'),L('Y',V('i'))),replace('X',V('i'),L('X',V('i'))+V('vx')),replace('Y',V('i'),L('Y',V('i'))+V('vy'))]),change('i',1)])])
solve=[setv('a',L('CA',V('c'))),setv('b',L('CB',V('c'))),setv('dx',L('X',V('a'))-L('X',V('b'))),setv('dy',L('Y',V('a'))-L('Y',V('b'))),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),0),[setv('diff',(V('distance')-L('Rest',V('c')))/V('distance')*.5),iff(AND(cmp('equals',L('Kind',V('c')),1),cmp('gt',V('diff'),L('Endurance',V('c')))),[setv('Mounted',0)],[iff(OR(cmp('lt',L('Kind',V('c')),2),cmp('lt',V('distance'),L('Rest',V('c')))),[replace('X',V('a'),L('X',V('a'))-V('dx')*V('diff')),replace('Y',V('a'),L('Y',V('a'))-V('dy')*V('diff')),replace('X',V('b'),L('X',V('b'))+V('dx')*V('diff')),replace('Y',V('b'),L('Y',V('b'))+V('dy')*V('diff'))])])])]
proc('solve sticks',[setv('c',1),loop(len(cons),[iff(OR(cmp('equals',L('Kind',V('c')),0),OR(cmp('equals',L('Kind',V('c')),2),cmp('equals',V('Mounted'),1))),solve),change('c',1)])])
contact=[setv('ox',L('X',V('i'))-L('LX',V('j'))),setv('oy',L('Y',V('i'))-L('LY',V('j'))),setv('depth',V('ox')*L('NX',V('j'))+V('oy')*L('NY',V('j'))),setv('along',(V('ox')*L('DX',V('j'))+V('oy')*L('DY',V('j')))*L('InvSq',V('j'))),iff(AND(AND(cmp('gt',V('depth'),0),cmp('lt',V('depth'),10)),AND(AND(cmp('gt',V('along'),-.000001),cmp('lt',V('along'),1.000001)),cmp('gt',L('NX',V('j'))*L('VX',V('i'))+L('NY',V('j'))*L('VY',V('i')),0))),[replace('X',V('i'),L('X',V('i'))-L('NX',V('j'))*V('depth')),replace('Y',V('i'),L('Y',V('i'))-L('NY',V('j'))*V('depth')),setv('friction factor',1),iff(cmp('equals',L('Material',V('j')),2),[setv('friction factor',0)]),setv('fx',L('NY',V('j'))*L('Friction',V('i'))*V('friction factor')*V('depth')),setv('fy',0-L('NX',V('j'))*L('Friction',V('i'))*V('friction factor')*V('depth')),iff(cmp('gt',L('PX',V('i')),L('X',V('i'))-.0000001),[setv('fx',0-V('fx'))]),iff(cmp('lt',L('PY',V('i')),L('Y',V('i'))),[setv('fy',0-V('fy'))]),replace('PX',V('i'),L('PX',V('i'))+V('fx')),replace('PY',V('i'),L('PY',V('i'))+V('fy')),iff(cmp('equals',L('Material',V('j')),1),[setv('tangent speed',(L('X',V('i'))-L('PX',V('i')))*L('NY',V('j'))-(L('Y',V('i'))-L('PY',V('i')))*L('NX',V('j'))),replace('PX',V('i'),L('PX',V('i'))+L('NY',V('j'))*V('tangent speed')*.08),replace('PY',V('i'),L('PY',V('i'))-L('NX',V('j'))*V('tangent speed')*.08)])])]
# Match lr-core AccLine's 0.1 directed tangent applied to previous position.
for material,direction in [(4,1),(5,-1)]:
 contact[-1][2].append(iff(cmp('equals',L('Material',V('j')),material),[
  replace('PX',V('i'),L('PX',V('i'))-L('NY',V('j'))*.1*direction),
  replace('PY',V('i'),L('PY',V('i'))+L('NX',V('j'))*.1*direction)]))
# Noniterating bind joints and scarf chain.
end=[]
for c in body['constraints']:
 if c['type']=='BindJoint':
  a,b,q,r=[idx[c[k]] for k in ['p1','p2','q1','q2']]
  cross=(L('X',b)-L('X',a))*(L('Y',r)-L('Y',q))-(L('Y',b)-L('Y',a))*(L('X',r)-L('X',q))
  end+=[iff(cmp('lt',cross,0),[setv('Mounted' if c['binding']=='RIDER_MOUNTED' else 'Sled intact',0)])]
chainids=[idx[x] for x in body['parts']['SCARF']]
for a,b in zip(chainids,chainids[1:]):
 rest=math.hypot(pts[a-1]['x']-pts[b-1]['x'],pts[a-1]['y']-pts[b-1]['y'])
 end += [setv('dx',L('X',a)-L('X',b)),setv('dy',L('Y',a)-L('Y',b)),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),0),[setv('diff',(V('distance')-rest)/V('distance')),replace('X',b,L('X',b)+V('dx')*V('diff')),replace('Y',b,L('Y',b)+V('dy')*V('diff'))])]
proc('finish frame',end)
proc('physics frame',[iff(cmp('equals',V('Ragdoll active'),1),[call('begin ragdoll contacts')]),call('integrate points'),loop(6+V('Ragdoll active')*2,[call('solve sticks'),iff(cmp('equals',V('Ragdoll active'),1),[call('solve ragdoll')]),call('collide points with lines')]),iff(cmp('equals',V('Ragdoll active'),1),[call('resolve ragdoll velocities')]),call('finish frame'),call('try seat catch'),iff(cmp('equals',V('Ragdoll active'),0),[call('update ragdoll pose'),iff(cmp('equals',V('Mounted'),0),[call('activate ragdoll')])]),change('Frame',1)])

seatx=L('X',1)+(L('X',4)-L('X',1))*5/17.5
seaty=L('Y',1)+(L('Y',4)-L('Y',1))*5/17.5
sx=(L('X',3)-L('X',2))/15
sy=(L('Y',3)-L('Y',2))/15
rx=L('X',5)-seatx
ry=L('Y',5)-seaty
height=rx*(0-sy)+ry*sx
along=rx*sx+ry*sy
relative=(L('Y',5)-L('PY',5))-(L('Y',1)-L('PY',1))
catch=[setv('Mounted',1),setv('Ragdoll active',0),setv('Crash complete',0),setv('Crash frames',0),setv('State',1)]
for i in range(5,len(pts)+1):
 x=L('X',1)+L('Initial X',i)*sx-L('Initial Y',i)*sy
 y=L('Y',1)+L('Initial X',i)*sy+L('Initial Y',i)*sx
 catch += [replace('X',i,x),replace('Y',i,y),replace('PX',i,x-(L('X',1)-L('PX',1))),replace('PY',i,y-(L('Y',1)-L('PY',1))),replace('Air',i,L('Initial air',i))]
proc('try seat catch',[iff(AND(AND(cmp('equals',V('Ragdoll active'),1),cmp('equals',V('Sled intact'),1)),AND(cmp('gt',V('Crash frames'),10),AND(cmp('lt',mathop('abs',along),8),AND(cmp('gt',height,-3),AND(cmp('lt',height,3),cmp('gt',relative,0)))))),catch)])
