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
# Only the six rigid sled distances survive from the original bindings.
cons=[c for c in body['constraints'] if c['type']=='Stick' and idx[c['p1']]<=4 and idx[c['p2']]<=4]
from course import default_track
tracks=default_track()
for k in ['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']:lists[k]=[k,[]]
for x,y,xx,yy,m in tracks:
 dx,dy=xx-x,yy-y;le=math.hypot(dx,dy)
 for k,v in [('LX',x),('LY',y),('DX',dx),('DY',dy),('NX',-dy/le),('NY',dx/le),('InvSq',1/le**2),('Material',m),('MinX',min(x,xx)-10),('MaxX',max(x,xx)+10),('MinY',min(y,yy)-10),('MaxY',max(y,yy)+10)]:lists[k][1].append(v)
lists['Candidates']=['Candidates',[]]
