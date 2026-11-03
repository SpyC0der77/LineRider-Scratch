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
def mathop(o,a):return Expr('operator_mathop',{'NUM':a},{'OPERATOR':[o,None]})
def V(k):variables.setdefault(k,[k,0]);return Expr('data_variable',{}, {'VARIABLE':[k,k]})
def L(k,i):return Expr('data_itemoflist',{'INDEX':i},{'LIST':[k,k]})
def length(k):return Expr('data_lengthoflist',{}, {'LIST':[k,k]})
def emit(o,inputs={},fields={},parent=None,**extra):
 global n
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
def call(name):return ('procedures_call',{}, {})
def call(name):return ('CALL',name)
# Expand custom calls inside chain through a statement wrapper.
oldemit=emit
def emit(o,inputs={},fields={},parent=None,**extra):
 if o=='CALL':return oldemit('procedures_call',{}, {},parent,mutation={'tagName':'mutation','children':[],'proccode':inputs,'argumentids':'[]','warp':'true'})
 return oldemit(o,inputs,fields,parent,**extra)
# Calls must have the ordinary statement tuple shape.
def call(name):return ('CALL',name,{})
def goto(x,y):return stmt('motion_gotoxy',{'X':x,'Y':y})
def color(c):return stmt('pen_setPenColorToColor',{'COLOR':c})
def size(s):return stmt('pen_setPenSizeTo',{'SIZE':s})
def key(k):return Expr('sensing_keypressed',{'KEY_OPTION':k})
body=json.loads((ROOT/'reference/lr-core/src/line-rider-engine/rider-data/index.json').read_text())
pts=[p for p in body['states'] if p['type']!='Binding'];idx={p['id']:i+1 for i,p in enumerate(pts)}
for k in ['X','Y','PX','PY','VX','VY','Friction','Air','Initial X','Initial Y']:lists[k]=[k,[]]
for p in pts:
 for k,val in [('X',p['x']),('Y',p['y']),('PX',p['x']-.4),('PY',p['y']),('VX',.4),('VY',0),('Friction',p.get('friction',0)),('Air',p.get('airFriction',0)),('Initial X',p['x']),('Initial Y',p['y'])]:lists[k][1].append(val)
cons=[c for c in body['constraints'] if c['type'] in ['Stick','BindStick','RepelStick']]
for k in ['CA','CB','Rest','Kind','Endurance']:lists[k]=[k,[]]
for c in cons:
 a,b=idx[c['p1']],idx[c['p2']];r=math.hypot(pts[a-1]['x']-pts[b-1]['x'],pts[a-1]['y']-pts[b-1]['y'])*c.get('lengthFactor',1)
 for k,v in [('CA',a),('CB',b),('Rest',r),('Kind',{'Stick':0,'BindStick':1,'RepelStick':2}[c['type']]),('Endurance',c.get('endurance',0)*r*.5)]:lists[k][1].append(v)
tracks=[]
for x in range(-100,1700,20):
 def y(x):return 28+.18*x+35*math.sin(x/140)
 tracks.append((x,y(x),x+20,y(x+20),1 if 500<x<700 else 0))
# Gap and landing, followed by a crash obstacle.
tracks += [(1790,400,1900,425,0),(1900,425,2100,425,0),(2080,375,2080,425,0)]
for k in ['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']:lists[k]=[k,[]]
for x,y,xx,yy,m in tracks:
 dx,dy=xx-x,yy-y;le=math.hypot(dx,dy)
 for k,v in [('LX',x),('LY',y),('DX',dx),('DY',dy),('NX',-dy/le),('NY',dx/le),('InvSq',1/le**2),('Material',m),('MinX',min(x,xx)-10),('MaxX',max(x,xx)+10),('MinY',min(y,yy)-10),('MaxY',max(y,yy)+10)]:lists[k][1].append(v)
lists['Candidates']=['Candidates',[]]
proc('reset rider',[setv('i',1),loop(len(pts),[replace('X',V('i'),L('Initial X',V('i'))),replace('Y',V('i'),L('Initial Y',V('i'))),replace('PX',V('i'),L('Initial X',V('i'))-.4),replace('PY',V('i'),L('Initial Y',V('i'))),change('i',1)]),setv('Mounted',1),setv('Sled intact',1),setv('Frame',0),setv('Camera X',0),setv('Camera Y',0)])
proc('integrate points',[setv('i',1),loop(len(pts),[setv('vx',(L('X',V('i'))-L('PX',V('i')))*(1-L('Air',V('i')))),setv('vy',(L('Y',V('i'))-L('PY',V('i')))*(1-L('Air',V('i')))+.175),replace('VX',V('i'),V('vx')),replace('VY',V('i'),V('vy')),replace('PX',V('i'),L('X',V('i'))),replace('PY',V('i'),L('Y',V('i'))),replace('X',V('i'),L('X',V('i'))+V('vx')),replace('Y',V('i'),L('Y',V('i'))+V('vy')),change('i',1)])])
solve=[setv('a',L('CA',V('c'))),setv('b',L('CB',V('c'))),setv('dx',L('X',V('a'))-L('X',V('b'))),setv('dy',L('Y',V('a'))-L('Y',V('b'))),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),0),[setv('diff',(V('distance')-L('Rest',V('c')))/V('distance')*.5),iff(AND(cmp('equals',L('Kind',V('c')),1),cmp('gt',V('diff'),L('Endurance',V('c')))),[setv('Mounted',0)],[iff(OR(cmp('lt',L('Kind',V('c')),2),cmp('lt',V('distance'),L('Rest',V('c')))),[replace('X',V('a'),L('X',V('a'))-V('dx')*V('diff')),replace('Y',V('a'),L('Y',V('a'))-V('dy')*V('diff')),replace('X',V('b'),L('X',V('b'))+V('dx')*V('diff')),replace('Y',V('b'),L('Y',V('b'))+V('dy')*V('diff'))])])])]
proc('solve sticks',[setv('c',1),loop(len(cons),[iff(OR(cmp('equals',L('Kind',V('c')),1),False),[]) ] if False else [iff(OR(cmp('equals',L('Kind',V('c')),0),OR(cmp('equals',L('Kind',V('c')),2),cmp('equals',V('Mounted'),1))),solve),change('c',1)])])
# Conservative candidate set refreshed for each collision pass: all lines near any collidable point.
proc('nearby lines',[clear('Candidates'),setv('j',1),loop(length('LX'),[setv('near',0),setv('i',1),loop(10,[iff(AND(AND(cmp('gt',L('X',V('i')),L('MinX',V('j'))),cmp('lt',L('X',V('i')),L('MaxX',V('j')))),AND(cmp('gt',L('Y',V('i')),L('MinY',V('j'))),cmp('lt',L('Y',V('i')),L('MaxY',V('j'))))),[setv('near',1)]),change('i',1)]),iff(cmp('equals',V('near'),1),[add('Candidates',V('j'))]),change('j',1)])])
contact=[setv('ox',L('X',V('i'))-L('LX',V('j'))),setv('oy',L('Y',V('i'))-L('LY',V('j'))),setv('depth',V('ox')*L('NX',V('j'))+V('oy')*L('NY',V('j'))),setv('along',(V('ox')*L('DX',V('j'))+V('oy')*L('DY',V('j')))*L('InvSq',V('j'))),iff(AND(AND(cmp('gt',V('depth'),0),cmp('lt',V('depth'),10)),AND(AND(cmp('gt',V('along'),-.000001),cmp('lt',V('along'),1.000001)),cmp('gt',L('NX',V('j'))*L('VX',V('i'))+L('NY',V('j'))*L('VY',V('i')),0))),[replace('X',V('i'),L('X',V('i'))-L('NX',V('j'))*V('depth')),replace('Y',V('i'),L('Y',V('i'))-L('NY',V('j'))*V('depth')),setv('fx',L('NY',V('j'))*L('Friction',V('i'))*V('depth')),setv('fy',0-L('NX',V('j'))*L('Friction',V('i'))*V('depth')),iff(cmp('gt',L('PX',V('i')),L('X',V('i'))-.0000001),[setv('fx',0-V('fx'))]),iff(cmp('lt',L('PY',V('i')),L('Y',V('i'))),[setv('fy',0-V('fy'))]),replace('PX',V('i'),L('PX',V('i'))+V('fx')),replace('PY',V('i'),L('PY',V('i'))+V('fy')),iff(cmp('equals',L('Material',V('j')),1),[replace('PX',V('i'),L('PX',V('i'))+(L('X',V('i'))-L('PX',V('i')))*.08),replace('PY',V('i'),L('PY',V('i'))+(L('Y',V('i'))-L('PY',V('i')))*.08)])])]
proc('collide points with lines',[call('nearby lines'),setv('i',1),loop(10,[setv('k',1),loop(length('Candidates'),[setv('j',L('Candidates',V('k')))]+contact+[change('k',1)]),change('i',1)])])
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
proc('physics frame',[call('integrate points'),loop(6,[call('solve sticks'),call('collide points with lines')]),call('finish frame'),change('Frame',1)])
# Drawing uses a zoom of 3; camera translation never enters simulation.
def screenx(x):return (x-V('Camera X'))*3-80
def screeny(y):return 30-(y-V('Camera Y'))*3
def segment(a,b):return [stmt('pen_penUp'),goto(screenx(L('X',a)),screeny(L('Y',a))),stmt('pen_penDown'),goto(screenx(L('X',b)),screeny(L('Y',b))),stmt('pen_penUp')]
render=[stmt('pen_clear'),setv('j',1),size(2),loop(length('LX'),[iff(AND(AND(cmp('gt',L('MaxX',V('j')),V('Camera X')-60),cmp('lt',L('MinX',V('j')),V('Camera X')+110)),AND(cmp('gt',L('MaxY',V('j')),V('Camera Y')-45),cmp('lt',L('MinY',V('j')),V('Camera Y')+65))),[color('#30332f'),iff(cmp('equals',L('Material',V('j')),1),[color('#a66328')]),stmt('pen_penUp'),goto(screenx(L('LX',V('j'))),screeny(L('LY',V('j')))),stmt('pen_penDown'),goto(screenx(L('LX',V('j'))+L('DX',V('j'))),screeny(L('LY',V('j'))+L('DY',V('j')))),stmt('pen_penUp')]),change('j',1)]),color('#9a433b'),size(3)]
for a,b in zip(chainids,chainids[1:]):render+=segment(a,b)
render += [color('#252823'),size(3)]
for part in ['SLED','LEFT_ARM','RIGHT_ARM','LEFT_LEG','RIGHT_LEG']:
 ids=[idx[x] for x in body['parts'][part]]
 for a,b in zip(ids,ids[1:]):render+=segment(a,b)
render+=segment(idx['SHOULDER'],idx['BUTT'])
render += [size(10),stmt('pen_penUp'),goto(screenx(L('X',6)),screeny(L('Y',6))-8),stmt('pen_penDown'),goto(screenx(L('X',6))+.01,screeny(L('Y',6))-8),stmt('pen_penUp')]
proc('render',render)
# Drawing tool: short segments only, automatically oriented left to right.
proc('append drawn line',[setv('dx',V('Draw X')-V('Last X')),setv('dy',V('Draw Y')-V('Last Y')),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),2),[setv('ax',V('Last X')),setv('ay',V('Last Y')),iff(cmp('lt',V('dx'),0),[setv('ax',V('Draw X')),setv('ay',V('Draw Y')),setv('dx',0-V('dx')),setv('dy',0-V('dy'))])]+[add(k,v) for k,v in [('LX',V('ax')),('LY',V('ay')),('DX',V('dx')),('DY',V('dy')),('NX',(0-V('dy'))/V('distance')),('NY',V('dx')/V('distance')),('InvSq',1/(V('distance')*V('distance'))),('Material',V('Brush')),('MinX',V('ax')-10),('MaxX',V('ax')+V('dx')+10),('MinY',V('ay')+V('dy')*.5-mathop('abs',V('dy'))*.5-10),('MaxY',V('ay')+V('dy')*.5+mathop('abs',V('dy'))*.5+10)]]+[setv('Last X',V('Draw X')),setv('Last Y',V('Draw Y'))])])
main=[stmt('looks_hide'),setv('Playing',0),setv('Editing',0),setv('Brush',0),setv('Drawing',0),call('reset rider'),call('render'),('forever',[iff(cmp('equals',V('Playing'),1),[call('physics frame'),setv('Camera X',L('X',5)),setv('Camera Y',L('Y',5))]),iff(cmp('equals',V('Editing'),1),[iff(key('right arrow'),[change('Camera X',3)]),iff(key('left arrow'),[change('Camera X',-3)]),iff(key('up arrow'),[change('Camera Y',-3)]),iff(key('down arrow'),[change('Camera Y',3)]),iff(AND(Expr('sensing_mousedown'),cmp('lt',Expr('sensing_mousey'),140)),[setv('Draw X',(Expr('sensing_mousex')+80)/3+V('Camera X')),setv('Draw Y',(30-Expr('sensing_mousey'))/3+V('Camera Y')),iff(cmp('equals',V('Drawing'),0),[setv('Last X',V('Draw X')),setv('Last Y',V('Draw Y')),setv('Drawing',1)],[call('append drawn line')])],[setv('Drawing',0)])]),call('render'),stmt('control_wait',{'DURATION':.001})])]
script('event_whenflagclicked',main)
for keyname,seq in [('n',[call('physics frame'),setv('Camera X',L('X',5)),setv('Camera Y',L('Y',5)),call('render')]),('space',[setv('Playing',1-V('Playing')),setv('Editing',0)]),('r',[call('reset rider'),setv('Playing',0)]),('e',[setv('Editing',1-V('Editing')),setv('Playing',0)]),('1',[setv('Brush',0)]),('2',[setv('Brush',1)]),('x',[setv('Mounted',0)]),('c',[iff(cmp('equals',V('Editing'),1),[clear(k) for k in ['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']])])]:script('event_whenkeypressed',seq,{'KEY_OPTION':[keyname,None]})
assets={}
def costume(name,svg,cx=240,cy=180):
 h=hashlib.md5(svg.encode()).hexdigest();assets[h+'.svg']=svg;return {'name':name,'assetId':h,'md5ext':h+'.svg','dataFormat':'svg','rotationCenterX':cx,'rotationCenterY':cy,'bitmapResolution':1}
bg=costume('paper','<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360"><path fill="#faf8f5" d="M0 0h480v360H0z"/></svg>')
hud=costume('controls','''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360"><path fill="#faf8f5" d="M0 0h480v37H0zM0 332h480v28H0z"/><path stroke="#dedbd6" d="M0 37h480M0 332h480"/><g font-family="sans-serif" font-size="11" fill="#30332f"><text x="12" y="16">Space: play / pause    R: restart    E: draw    X: detach</text><text x="12" y="30">Draw: drag mouse · arrows pan · 1 normal · 2 friction · C clear</text><text x="12" y="349">lr-core / Scratch     /     black: normal track     brown: friction</text></g></svg>''')
def target(name,stage=False,blocks={},costumes=[],**kw):return dict(isStage=stage,name=name,variables={},lists={},broadcasts={},blocks=blocks,comments={},currentCostume=0,costumes=costumes,sounds=[],volume=100,layerOrder=0 if stage else 1,**kw)
stage=target('Stage',True,costumes=[bg],tempo=60,videoTransparency=50,videoState='off',textToSpeechLanguage=None)
engine=target('Line Rider core',blocks=B,costumes=[bg],visible=False,x=0,y=0,size=100,direction=90,draggable=False,rotationStyle='all around');engine['variables']=variables;engine['lists']=lists
engine['comments']={'credits':{'blockId':None,'x':20,'y':0,'width':440,'height':220,'minimized':False,'text':'Physics adapted from lr-core 0.8.2 by David Lu (conundrumer), MIT. Source commit ce48ebed967d24ff4582995b31342440901f913d. Port includes Point, Stick, RepelStick, BindStick, BindJoint, DirectedChain and SolidLine equations. Scarf flutter, ClassicGrid and immutable timeline omitted. Brown friction is a demo extension. See README and LICENSE.lr-core.txt.'}}
engine['comments']['credits']['text']+='\n\n'+(ROOT/'LICENSE.lr-core.txt').read_text(encoding='utf-8-sig')
overlay=target('Controls',costumes=[hud],visible=True,x=0,y=0,size=100,direction=90,draggable=False,rotationStyle='all around');overlay['layerOrder']=2
project={'targets':[stage,engine,overlay],'monitors':[],'extensions':['pen'],'meta':{'semver':'3.0.0','vm':'0.2.0','agent':'lr-core-scratch-port'}}
def save(path,p):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('project.json',json.dumps(p))
  for k,v in assets.items():z.writestr(k,v)
save(ROOT/'dist/Line Rider.sb3',project)
save(ROOT/'artifacts/before.sb3',{'targets':[stage],'monitors':[],'extensions':[],'meta':project['meta']})
(ROOT/'dist/project.json').write_text(json.dumps(project,indent=2))
print('Built',len(B),'blocks;',len(pts),'points;',len(cons),'sticks;',len(tracks),'track segments')






