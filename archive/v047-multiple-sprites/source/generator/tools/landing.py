"""Compliant sled contact and bounded pose recovery after a successful catch."""
def install(api):
 globals().update(api)
 dynamic=[5,6,7,8,9,10,18,19,20,21,22]
 active=AND(cmp('gt',V('Landing frames'),0),AND(cmp('lt',V('State'),3),cmp('equals',V('Flight failed'),0)))
 basis=[setv('seat ux',(L('X',3)-L('X',2))/15),setv('seat uy',(L('Y',3)-L('Y',2))/15)]
 damp=basis[:]
 for i in [9,10]:
  lx=(L('X',i)-L('X',5))*V('seat ux')+(L('Y',i)-L('Y',5))*V('seat uy')
  ly=(L('X',i)-L('X',5))*(0-V('seat uy'))+(L('Y',i)-L('Y',5))*V('seat ux')
  stage='Leg swing '+str(i)
  damp += [iff(cmp('equals',V(stage),0),[setv(stage,1),iff(cmp('gt',lx,2),[setv(stage,3)])]),iff(AND(cmp('equals',V(stage),1),cmp('lt',ly,-4)),[setv(stage,2)]),iff(AND(cmp('equals',V(stage),2),cmp('gt',lx,4)),[setv(stage,3)])]
 for i in dynamic:
  for axis,previous in [('X','PX'),('Y','PY')]:
   # Absorb relative motion over several frames while retaining follow-through.
   damp += [replace(previous,i,L(previous,i)+((L(axis,i)-L(previous,i))-(L(axis,1)-L(previous,1)))*.3)]
 proc('damp landing motion',[iff(active,damp)])
 solve=basis[:]
 for i in dynamic:
  limit=.4 if i in [9,10] else (.28 if i in [20,21] else .12)
  target_height=L('Initial Y',i)
  targetx=L('X',1)+L('Initial X',i)*V('seat ux')-target_height*V('seat uy')
  targety=L('Y',1)+L('Initial X',i)*V('seat uy')+target_height*V('seat ux')
  if i in [9,10]:
   stage=V('Leg swing '+str(i))
   solve += [setv('leg target x',5),setv('leg target y',5),iff(cmp('equals',stage,1),[setv('leg target x',-4),setv('leg target y',-5.8)]),iff(cmp('equals',stage,2),[setv('leg target x',6),setv('leg target y',-4)])]
   targetx=L('X',5)+V('leg target x')*V('seat ux')-V('leg target y')*V('seat uy')
   targety=L('Y',5)+V('leg target x')*V('seat uy')+V('leg target y')*V('seat ux')
  solve += [setv('seat dx',(targetx-L('X',i))*.12),setv('seat dy',(targety-L('Y',i))*.12),setv('seat distance',mathop('sqrt',V('seat dx')*V('seat dx')+V('seat dy')*V('seat dy'))),iff(cmp('gt',V('seat distance'),limit),[setv('seat dx',V('seat dx')*limit/V('seat distance')),setv('seat dy',V('seat dy')*limit/V('seat distance'))])]
  # Move current and previous positions together so correction adds no impulse.
  for axis,previous,delta in [('X','PX','seat dx'),('Y','PY','seat dy')]:
   solve += [replace(axis,i,L(axis,i)+V(delta)),replace(previous,i,L(previous,i)+V(delta))]
  # The sled's upper deck catches the body before it can strike the terrain.
  if i not in [9,10,20,21]:
   depth=(L('X',i)-L('X',2))*(0-V('seat uy'))+(L('Y',i)-L('Y',2))*V('seat ux')+L('R radius',i)+.5
   solve += [setv('seat depth',depth),iff(cmp('gt',V('seat depth'),0),[replace('X',i,L('X',i)+V('seat uy')*V('seat depth')),replace('Y',i,L('Y',i)-V('seat ux')*V('seat depth')),replace('PX',i,L('PX',i)+V('seat uy')*V('seat depth')),replace('PY',i,L('PY',i)-V('seat ux')*V('seat depth'))])]
 proc('solve landing',[iff(active,solve)])
 finish=[change('Landing frames',1)]+basis+[setv('Landing error',0)]
 for i in dynamic:
  dx=L('X',i)-(L('X',1)+L('Initial X',i)*V('seat ux')-L('Initial Y',i)*V('seat uy'))
  dy=L('Y',i)-(L('Y',1)+L('Initial X',i)*V('seat uy')+L('Initial Y',i)*V('seat ux'))
  finish += [setv('seat distance',mathop('sqrt',dx*dx+dy*dy)/(1.5 if i in [9,10,20,21] else .8)),iff(cmp('gt',V('seat distance'),V('Landing error')),[setv('Landing error',V('seat distance'))])]
 # Hand control to the normal constraints only after every body point is close.
 finish += [iff(AND(cmp('gt',V('Landing frames'),16),cmp('lt',V('Landing error'),1)),[setv('Mounted',1),setv('Ragdoll active',0),setv('Landing frames',0),setv('Flight frames',0),setv('Flight departed',0)]+[replace('Air',i,L('Initial air',i)) for i in dynamic])]
 proc('finish landing',[iff(active,finish)])
