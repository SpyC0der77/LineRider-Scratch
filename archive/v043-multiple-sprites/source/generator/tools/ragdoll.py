"""Articulated post-detachment rider; mounted lr-core dynamics stay unchanged."""
import math

def extend_rider(body):
 states={p['id']:p for p in body['states'] if 'x' in p}
 def bent(a,b,offset):
  a,b=states[a],states[b];dx,dy=b['x']-a['x'],b['y']-a['y'];le=math.hypot(dx,dy)
  return ((a['x']+b['x'])/2-dy/le*offset,(a['y']+b['y'])/2+dx/le*offset)
 extras=[('LELBOW',*bent('SHOULDER','LHAND',1.2)),('RELBOW',*bent('SHOULDER','RHAND',-1.2)),('LKNEE',10,0),('RKNEE',10,0),('HEAD',5,-8.2)]
 for name,x,y in extras:body['states'].append(dict(id=name,type='CollisionPoint',x=x,y=y,friction=.1))
 body['parts'].update(LEFT_ARM=['SHOULDER','LELBOW','LHAND'],RIGHT_ARM=['SHOULDER','RELBOW','RHAND'],LEFT_LEG=['BUTT','LKNEE','LFOOT'],RIGHT_LEG=['BUTT','RKNEE','RFOOT'])
 return body

def install(api):
 globals().update(api)
 count=len(pts);dynamic=[5,6,7,8,9,10,18,19,20,21,22]
 radii={5:1.2,6:1.1,7:.6,8:.6,9:.75,10:.75,18:.65,19:.65,20:.75,21:.75,22:1.75}
 inverse={5:1,6:1,7:1.4,8:1.4,9:1.2,10:1.2,18:1.2,19:1.2,20:1.1,21:1.1,22:.8}
 lists['Initial air']=['Initial air',lists['Air'][1][:]]
 for name,values in [('R radius',[radii.get(i,0) for i in range(1,count+1)]),('R inverse mass',[inverse.get(i,1) for i in range(1,count+1)]),('R contact depth',[0]*count),('R contact nx',[0]*count),('R contact ny',[0]*count),('R contact material',[0]*count)]:lists[name]=[name,values]
 links=[]
 def link(a,b,kind=0,rest=None,strength=1):
  ia,ib=idx[a],idx[b]
  if rest is None:rest=math.hypot(pts[ia-1]['x']-pts[ib-1]['x'],pts[ia-1]['y']-pts[ib-1]['y'])
  links.append((ia,ib,rest,kind,strength))
 for a,b in [('SHOULDER','HEAD'),('SHOULDER','LELBOW'),('LELBOW','LHAND'),('SHOULDER','RELBOW'),('RELBOW','RHAND'),('BUTT','LKNEE'),('LKNEE','LFOOT'),('BUTT','RKNEE'),('RKNEE','RFOOT')]:link(a,b)
 link('BUTT','HEAD',1,6.8);link('BUTT','HEAD',2,8.2,.6)
 for end in ['LHAND','RHAND']:link('SHOULDER',end,1,2.0,.8)
 for end in ['LFOOT','RFOOT']:link('BUTT',end,1,2.5,.8)
 for a,b,r in [('LHAND','RHAND',1),('LFOOT','RFOOT',1.2),('LKNEE','RKNEE',.8),('HEAD','LHAND',2.4),('HEAD','RHAND',2.4),('HEAD','LFOOT',2.7),('HEAD','RFOOT',2.7),('BUTT','LELBOW',1.8),('BUTT','RELBOW',1.8),('SHOULDER','LKNEE',2.6),('SHOULDER','RKNEE',2.6)]:link(a,b,1,r,.7)
 for k,j in [('R bone A',0),('R bone B',1),('R bone rest',2),('R bone kind',3),('R bone strength',4)]:lists[k]=[k,[r[j] for r in links]]
 pose=[]
 for current,previous in [('X','Y'),('PX','PY')]:
  for dest,a,b,bend in [(18,6,8,1.2),(19,6,7,-1.2),(20,5,9,-math.sqrt(12.5)),(21,5,10,-math.sqrt(12.5))]:
   pose += [setv('pose dx',L(current,b)-L(current,a)),setv('pose dy',L(previous,b)-L(previous,a)),setv('pose length',mathop('sqrt',V('pose dx')*V('pose dx')+V('pose dy')*V('pose dy'))),iff(cmp('lt',V('pose length'),.001),[setv('pose length',.001)]),replace(current,dest,(L(current,a)+L(current,b))/2-V('pose dy')/V('pose length')*bend),replace(previous,dest,(L(previous,a)+L(previous,b))/2+V('pose dx')/V('pose length')*bend)]
  pose += [setv('pose dx',L(current,6)-L(current,5)),setv('pose dy',L(previous,6)-L(previous,5)),setv('pose length',mathop('sqrt',V('pose dx')*V('pose dx')+V('pose dy')*V('pose dy'))),iff(cmp('lt',V('pose length'),.001),[setv('pose length',.001)]),replace(current,22,L(current,6)+V('pose dx')/V('pose length')*2.7),replace(previous,22,L(previous,6)+V('pose dy')/V('pose length')*2.7)]
 proc('update ragdoll pose',pose)
 proc('begin ragdoll contacts',[setv('ri',1),loop(count,[replace(k,V('ri'),0) for k in ['R contact depth','R contact nx','R contact ny','R contact material']]+[change('ri',1)])])
 adjust=[setv('ra',L('R bone A',V('rj'))),setv('rb',L('R bone B',V('rj'))),setv('rdx',L('X',V('ra'))-L('X',V('rb'))),setv('rdy',L('Y',V('ra'))-L('Y',V('rb'))),setv('rlen',mathop('sqrt',V('rdx')*V('rdx')+V('rdy')*V('rdy'))),iff(cmp('lt',V('rlen'),.0001),[setv('rdx',.0001),setv('rdy',0),setv('rlen',.0001)]),iff(OR(cmp('equals',L('R bone kind',V('rj')),0),OR(AND(cmp('equals',L('R bone kind',V('rj')),1),cmp('lt',V('rlen'),L('R bone rest',V('rj')))),AND(cmp('equals',L('R bone kind',V('rj')),2),cmp('gt',V('rlen'),L('R bone rest',V('rj')))))),[setv('rdiff',(V('rlen')-L('R bone rest',V('rj')))/V('rlen')*L('R bone strength',V('rj'))),setv('rweight',L('R inverse mass',V('ra'))+L('R inverse mass',V('rb'))),replace('X',V('ra'),L('X',V('ra'))-V('rdx')*V('rdiff')*L('R inverse mass',V('ra'))/V('rweight')),replace('Y',V('ra'),L('Y',V('ra'))-V('rdy')*V('rdiff')*L('R inverse mass',V('ra'))/V('rweight')),replace('X',V('rb'),L('X',V('rb'))+V('rdx')*V('rdiff')*L('R inverse mass',V('rb'))/V('rweight')),replace('Y',V('rb'),L('Y',V('rb'))+V('rdy')*V('rdiff')*L('R inverse mass',V('rb'))/V('rweight'))])]
 joint=[]
 for a,b,c,side in [(6,18,8,1),(6,19,7,-1),(5,20,9,-1),(5,21,10,-1)]:
  joint += [setv('jdx',L('X',c)-L('X',a)),setv('jdy',L('Y',c)-L('Y',a)),setv('jlength',mathop('sqrt',V('jdx')*V('jdx')+V('jdy')*V('jdy'))),iff(cmp('gt',V('jlength'),.001),[setv('jnx',(0-V('jdy'))/V('jlength')),setv('jny',V('jdx')/V('jlength')),setv('jbend',((L('X',b)-L('X',a))*V('jnx')+(L('Y',b)-L('Y',a))*V('jny'))*side),iff(cmp('lt',V('jbend'),.2),[setv('jpush',(.2-V('jbend'))*side*.8)]+sum(([replace(axis,b,L(axis,b)+V(normal)*V('jpush')*2/3),replace(axis,a,L(axis,a)-V(normal)*V('jpush')/3),replace(axis,c,L(axis,c)-V(normal)*V('jpush')/3)] for axis,normal in [('X','jnx'),('Y','jny')]),[]))])]
 proc('solve ragdoll',[setv('rj',1),loop(len(links),adjust+[change('rj',1)])]+joint)
 # Circle contacts share the original line normals: no rectangular segment ends.
 contact_circle=[setv('rox',L('X',V('i'))-L('LX',V('j'))),setv('roy',L('Y',V('i'))-L('LY',V('j'))),setv('rdepth',V('rox')*L('NX',V('j'))+V('roy')*L('NY',V('j'))+L('R radius',V('i'))),setv('ralong',(V('rox')*L('DX',V('j'))+V('roy')*L('DY',V('j')))*L('InvSq',V('j'))),setv('rprevious',(L('PX',V('i'))-L('LX',V('j')))*L('NX',V('j'))+(L('PY',V('i'))-L('LY',V('j')))*L('NY',V('j'))+L('R radius',V('i'))),setv('rbound',mathop('abs',L('NX',V('j'))*L('VX',V('i'))+L('NY',V('j'))*L('VY',V('i')))+L('R radius',V('i'))+2),iff(cmp('lt',V('rbound'),10),[setv('rbound',10)]),iff(AND(AND(cmp('gt',V('rdepth'),0),cmp('lt',V('rdepth'),V('rbound'))),AND(AND(cmp('gt',V('ralong'),-.000001),cmp('lt',V('ralong'),1.000001)),OR(cmp('equals',V('Preserve contact velocity'),1),cmp('lt',V('rprevious'),L('R radius',V('i'))+.75)))),[replace('X',V('i'),L('X',V('i'))-L('NX',V('j'))*V('rdepth')),replace('Y',V('i'),L('Y',V('i'))-L('NY',V('j'))*V('rdepth')),iff(cmp('equals',V('Preserve contact velocity'),1),[replace('PX',V('i'),L('PX',V('i'))-L('NX',V('j'))*V('rdepth')),replace('PY',V('i'),L('PY',V('i'))-L('NY',V('j'))*V('rdepth'))]),iff(cmp('gt',V('rdepth'),L('R contact depth',V('i'))),[replace('R contact depth',V('i'),V('rdepth')),replace('R contact nx',V('i'),L('NX',V('j'))),replace('R contact ny',V('i'),L('NY',V('j'))),replace('R contact material',V('i'),L('Material',V('j')))])])]
 proc('ragdoll circle contact',contact_circle)
 proc('project ragdoll contacts',[setv('i',5),loop(count-4,[iff(OR(cmp('lt',V('i'),11),cmp('gt',V('i'),17)),[call('nearby lines'),setv('k',1),loop(length('Candidates'),[setv('j',L('Candidates',V('k'))),iff(cmp('equals',cmp('equals',L('Material',V('j')),3),0),[call('ragdoll circle contact')]),change('k',1)])]),change('i',1)])])
 activate=[call('update ragdoll pose'),setv('Ragdoll active',1),setv('Flight frames',0),setv('Flight departed',0),setv('Ragdoll sleep frames',0),setv('Ragdoll speed squared',1),setv('Preserve contact velocity',1)]
 # Give coincident left/right limbs physical width without adding velocity.
 for i,offset in [(7,-.25),(8,.25),(9,-.3),(10,.3),(20,-.2),(21,.2)]:
  activate += [replace('X',i,L('X',i)+offset),replace('PX',i,L('PX',i)+offset)]
 activate += [replace('Air',i,0) for i in dynamic]+[call('project ragdoll contacts'),setv('Preserve contact velocity',0)]
 proc('activate ragdoll',activate)
 velocity=[setv('rvx',L('X',V('ri'))-L('PX',V('ri'))),setv('rvy',L('Y',V('ri'))-L('PY',V('ri'))),iff(cmp('gt',L('R contact depth',V('ri')),0),[setv('rnx',L('R contact nx',V('ri'))),setv('rny',L('R contact ny',V('ri'))),setv('rvn',V('rvx')*V('rnx')+V('rvy')*V('rny')),setv('rincoming',L('VX',V('ri'))*V('rnx')+L('VY',V('ri'))*V('rny')),iff(cmp('lt',V('rincoming'),0),[setv('rincoming',0)]),setv('rbounce',(0-V('rincoming'))*.03),iff(cmp('lt',V('rbounce'),-.2),[setv('rbounce',-.2)]),iff(cmp('gt',V('rvn'),V('rbounce')),[change('rvx',V('rnx')*(V('rbounce')-V('rvn'))),change('rvy',V('rny')*(V('rbounce')-V('rvn')))]),iff(cmp('equals',L('R contact material',V('ri')),4),[change('rvx',V('rny')*.1),change('rvy',(0-V('rnx'))*.1)]),iff(cmp('equals',L('R contact material',V('ri')),5),[change('rvx',(0-V('rny'))*.1),change('rvy',V('rnx')*.1)]),setv('rvt',V('rvx')*V('rny')-V('rvy')*V('rnx')),setv('rmu',.12),iff(cmp('equals',L('R contact material',V('ri')),1),[setv('rmu',.24)]),iff(cmp('equals',L('R contact material',V('ri')),2),[setv('rmu',0)]),setv('rfriction',V('rmu')*(V('rincoming')+.175*mathop('abs',V('rny')))),iff(cmp('gt',V('rfriction'),mathop('abs',V('rvt'))),[setv('rfriction',mathop('abs',V('rvt')))]),iff(cmp('lt',V('rvt'),0),[setv('rfriction',0-V('rfriction'))]),change('rvx',0-V('rny')*V('rfriction')),change('rvy',V('rnx')*V('rfriction'))]),setv('rspeed',V('rvx')*V('rvx')+V('rvy')*V('rvy')),iff(cmp('gt',V('rspeed'),400),[setv('rscale',20/mathop('sqrt',V('rspeed'))),setv('rvx',V('rvx')*V('rscale')),setv('rvy',V('rvy')*V('rscale')),setv('rspeed',400)]),replace('PX',V('ri'),L('X',V('ri'))-V('rvx')),replace('PY',V('ri'),L('Y',V('ri'))-V('rvy')),replace('VX',V('ri'),V('rvx')),replace('VY',V('ri'),V('rvy')),iff(cmp('gt',V('rspeed'),V('Ragdoll speed squared')),[setv('Ragdoll speed squared',V('rspeed'))])]
 proc('resolve ragdoll velocities',[setv('Ragdoll speed squared',0),setv('ri',5),loop(count-4,[iff(OR(cmp('lt',V('ri'),11),cmp('gt',V('ri'),17)),velocity),change('ri',1)]),iff(cmp('lt',V('Ragdoll speed squared'),.025),[change('Ragdoll sleep frames',1)],[setv('Ragdoll sleep frames',0)])])
