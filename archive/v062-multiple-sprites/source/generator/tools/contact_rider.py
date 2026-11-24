"""One continuous articulated solver with unilateral sled contact and elastic grips.

Mounted is an observation used by the finish condition. It never selects forces,
constraints, integration, drawing, or a landing/release animation.
"""
import math


def install(api):
 globals().update(api)
 count=len(pts);rider=[5,6,7,8,9,10,18,19,20,21,22];colliders=rider+[23]
 inverse=[.25 if i<=4 else (1.5 if i in [7,8,9,10,18,19,20,21] else (100 if i==23 else 1)) for i in range(1,count+1)]
 radius={5:1.2,6:1,7:.45,8:.45,9:.4,10:.4,18:.5,19:.5,20:.5,21:.5,22:1.6,23:.1}
 for i in [9,10]:
  lists['Initial Y'][1][i-1]=4.6;pts[i-1]['y']=4.6
 # Match the original forward-reaching silhouette; knees start only slightly bent.
 for knee,foot in [(20,9),(21,10)]:
  hip=pts[4];end=pts[foot-1];dx=end['x']-hip['x'];dy=end['y']-hip['y'];limb_length=math.hypot(dx,dy)
  x=(hip['x']+end['x'])/2+dy/limb_length*.45;y=(hip['y']+end['y'])/2-dx/limb_length*.45
  pts[knee-1]['x']=x;pts[knee-1]['y']=y;lists['Initial X'][1][knee-1]=x;lists['Initial Y'][1][knee-1]=y
 for name,values in [('Inverse mass',inverse),('Body radius',[radius.get(i,0) for i in range(1,count+1)]),('Ground contact',[0]*count),('Sled contact',[0]*count),('Initial air',[.2 if 11<=i<=17 else (.03 if i==23 else .0002) for i in range(1,count+1)]),('Grip force',[0]*count)]:lists[name]=[name,values]
 bones=[]
 def bone(a,b,kind=0,rest=None,strength=.9):
  if isinstance(a,str):a=idx[a];b=idx[b]
  if rest is None:rest=math.hypot(pts[a-1]['x']-pts[b-1]['x'],pts[a-1]['y']-pts[b-1]['y'])
  bones.append((a,b,rest,kind,strength))
 for c in cons:
  if idx[c['p1']]<=4 and idx[c['p2']]<=4:bone(c['p1'],c['p2'],strength=1)
 for a,b in [('BUTT','SHOULDER'),('SHOULDER','HEAD'),('SHOULDER','LELBOW'),('LELBOW','LHAND'),('SHOULDER','RELBOW'),('RELBOW','RHAND'),('BUTT','LKNEE'),('LKNEE','LFOOT'),('BUTT','RKNEE'),('RKNEE','RFOOT')]:bone(a,b)
 # Passive muscle/tendon springs preserve the original forward-reaching rest posture.
 for end in ['LHAND','RHAND']:
  bone('SHOULDER',end,3,strength=1)
  bone('BUTT',end,3,strength=3.5)
 for end in ['LFOOT','RFOOT']:
  bone('BUTT',end,3,strength=1)
  bone('SHOULDER',end,3,strength=2)
 bone('STRING','ROPE_END',2,math.sqrt(61),1)
 bone('BUTT','HEAD',1,6.5,.6);bone('BUTT','HEAD',2,8.2,.6)
 for a,b,r in [('LHAND','RHAND',.6),('LFOOT','RFOOT',.6),('HEAD','LHAND',2),('HEAD','RHAND',2),('HEAD','LFOOT',2),('HEAD','RFOOT',2)]:bone(a,b,1,r,.4)
 for name,col in [('Bone A',0),('Bone B',1),('Bone rest',2),('Bone kind',3),('Bone strength',4)]:lists[name]=[name,[b[col] for b in bones]]
 reset=[setv('i',1),loop(count,[replace('X',V('i'),L('Initial X',V('i'))+V('Spawn X')),replace('Y',V('i'),L('Initial Y',V('i'))+V('Spawn Y')),replace('PX',V('i'),L('Initial X',V('i'))+V('Spawn X')-.4),replace('PY',V('i'),L('Initial Y',V('i'))+V('Spawn Y')),replace('VX',V('i'),.4),replace('VY',V('i'),0),replace('Ground contact',V('i'),0),replace('Sled contact',V('i'),0),replace('Grip force',V('i'),0),change('i',1)])]
 reset += [setv(k,z) for k,z in [('Frame',0),('Mounted',1),('Sled intact',1),('Flight frames',0),('Flight departed',0),('Flight failed',0),('Crash complete',0),('Ragdoll sleep frames',0),('Ragdoll speed squared',0),('Support load',0),('Seat load',0),('Seat gap',0),('Angular drag',.3),('Posture spring',.05),('Balance stiffness',.4),('Grip stiffness',.15),('Grip reach',3),('Seat friction',.4),('Foot friction',.08),('Camera X',0),('Camera Y',0)]]
 proc('reset rider',reset)
 proc('integrate points',[setv('i',1),loop(count,[setv('vx',(L('X',V('i'))-L('PX',V('i')))*(1-L('Initial air',V('i')))),setv('vy',(L('Y',V('i'))-L('PY',V('i')))*(1-L('Initial air',V('i')))+.175),replace('VX',V('i'),V('vx')),replace('VY',V('i'),V('vy')),replace('PX',V('i'),L('X',V('i'))),replace('PY',V('i'),L('Y',V('i'))),replace('X',V('i'),L('X',V('i'))+V('vx')),replace('Y',V('i'),L('Y',V('i'))+V('vy')),change('i',1)])])
 adjust=[setv('a',L('Bone A',V('c'))),setv('b',L('Bone B',V('c'))),setv('dx',L('X',V('b'))-L('X',V('a'))),setv('dy',L('Y',V('b'))-L('Y',V('a'))),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),.00001),[iff(OR(OR(cmp('equals',L('Bone kind',V('c')),0),cmp('equals',L('Bone kind',V('c')),3)),OR(AND(cmp('equals',L('Bone kind',V('c')),1),cmp('lt',V('distance'),L('Bone rest',V('c')))),AND(cmp('equals',L('Bone kind',V('c')),2),cmp('gt',V('distance'),L('Bone rest',V('c')))))),[setv('bone stiffness',L('Bone strength',V('c'))),iff(cmp('equals',L('Bone kind',V('c')),3),[setv('bone stiffness',V('bone stiffness')*V('Posture spring'))]),setv('correction',(V('distance')-L('Bone rest',V('c')))/V('distance')*V('bone stiffness')/(L('Inverse mass',V('a'))+L('Inverse mass',V('b')))),replace('X',V('a'),L('X',V('a'))+V('dx')*V('correction')*L('Inverse mass',V('a'))),replace('Y',V('a'),L('Y',V('a'))+V('dy')*V('correction')*L('Inverse mass',V('a'))),replace('X',V('b'),L('X',V('b'))-V('dx')*V('correction')*L('Inverse mass',V('b'))),replace('Y',V('b'),L('Y',V('b'))-V('dy')*V('correction')*L('Inverse mass',V('b')))])])]
 proc('solve body bones',[setv('c',1),loop(len(bones),adjust+[change('c',1)])])
 # These anatomical limits stay identical on the seat and in free flight.
 joints=[]
 for a,b,c,side,limit in [(6,18,8,1,.15),(6,19,7,-1,.15),(5,20,9,-1,.15),(5,21,10,-1,.15),(6,7,5,-1,.5),(6,8,5,-1,.5),(6,20,5,-1,.5),(6,21,5,-1,.5)]:
  joints += [setv('dx',L('X',c)-L('X',a)),setv('dy',L('Y',c)-L('Y',a)),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),.001),[setv('nx',0-V('dy')/V('distance')),setv('ny',V('dx')/V('distance')),setv('bend',((L('X',b)-L('X',a))*V('nx')+(L('Y',b)-L('Y',a))*V('ny'))*side),iff(cmp('lt',V('bend'),limit),[setv('joint t',((L('X',b)-L('X',a))*V('dx')+(L('Y',b)-L('Y',a))*V('dy'))/(V('distance')*V('distance'))),setv('denominator',L('Inverse mass',b)+(1-V('joint t'))*(1-V('joint t'))*L('Inverse mass',a)+V('joint t')*V('joint t')*L('Inverse mass',c)),setv('correction',(limit-V('bend'))*side*.6/V('denominator'))]+sum(([replace(axis,b,L(axis,b)+V(n)*V('correction')*L('Inverse mass',b)),replace(axis,a,L(axis,a)-V(n)*V('correction')*(1-V('joint t'))*L('Inverse mass',a)),replace(axis,c,L(axis,c)-V(n)*V('correction')*V('joint t')*L('Inverse mass',c))] for axis,n in [('X','nx'),('Y','ny')]),[]))])]
 proc('solve joint limits',joints)
 proc('sled coordinate frame',[setv('sled ux',(L('X',3)-L('X',2))/15),setv('sled uy',(L('Y',3)-L('Y',2))/15)])
 # Hands interact with the rope's physical loose end through yielding springs.
 # Distance controls each grip continuously; a released rope does not follow the hand.
 grip=[]
 for hand in [7,8]:
  grip += [setv('dx',L('X',hand)-L('X',23)),setv('dy',L('Y',hand)-L('Y',23)),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(AND(cmp('gt',V('distance'),.00001),cmp('lt',V('distance'),V('Grip reach'))),[setv('grip envelope',1-V('distance')/V('Grip reach')),setv('tension',V('Grip stiffness')*V('distance')*V('grip envelope')*V('grip envelope')),setv('correction',V('tension')/(V('distance')*(L('Inverse mass',hand)+L('Inverse mass',23)))),replace('X',hand,L('X',hand)-V('dx')*V('correction')*L('Inverse mass',hand)),replace('Y',hand,L('Y',hand)-V('dy')*V('correction')*L('Inverse mass',hand)),replace('X',23,L('X',23)+V('dx')*V('correction')*L('Inverse mass',23)),replace('Y',23,L('Y',23)+V('dy')*V('correction')*L('Inverse mass',23)),replace('Grip force',hand,L('Grip force',hand)+V('tension'))])]
 proc('solve elastic grips',[iff(AND(cmp('lt',V('State'),3),cmp('equals',V('Flight failed'),0)),grip)])
 # The torso has a compliant balance muscle while close to the seat. Its
 # angular reaction is applied to the sled; it never sets a body pose.
 balance=[call('sled coordinate frame'),setv('hip local x',(L('X',5)-L('X',1))*V('sled ux')+(L('Y',5)-L('Y',1))*V('sled uy')),setv('hip local y',(L('Y',5)-L('Y',1))*V('sled ux')-(L('X',5)-L('X',1))*V('sled uy')),setv('proximity',(V('hip local x')-5)*(V('hip local x')-5)/81+V('hip local y')*V('hip local y')/2.25),iff(cmp('lt',V('proximity'),1),[setv('dx',L('X',6)-L('X',5)),setv('dy',L('Y',6)-L('Y',5)),setv('balance error',V('dx')*V('sled ux')+V('dy')*V('sled uy')),setv('gradient x',(V('dx')-V('sled ux')*V('balance error'))/15),setv('gradient y',(V('dy')-V('sled uy')*V('balance error'))/15),setv('denominator',L('Inverse mass',5)+L('Inverse mass',6)+(L('Inverse mass',2)+L('Inverse mass',3))*(V('gradient x')*V('gradient x')+V('gradient y')*V('gradient y'))),setv('correction',0-V('balance error')*V('Balance stiffness')*(V('Support load')/(V('Support load')+.05))*(1-V('proximity'))*(1-V('proximity'))/V('denominator'))]+sum(([replace(axis,6,L(axis,6)+V(u)*V('correction')*L('Inverse mass',6)),replace(axis,5,L(axis,5)-V(u)*V('correction')*L('Inverse mass',5)),replace(axis,3,L(axis,3)+V(g)*V('correction')*L('Inverse mass',3)),replace(axis,2,L(axis,2)-V(g)*V('correction')*L('Inverse mass',2))] for axis,u,g in [('X','sled ux','gradient x'),('Y','sled uy','gradient y')]),[]))]
 proc('solve rider balance',[iff(AND(cmp('lt',V('State'),3),cmp('equals',V('Flight failed'),0)),balance)])
 # Circle/capsule contacts with barycentric reaction on the rigid sled.

 contact=[call('sled coordinate frame'),setv('local x',(L('X',V('i'))-L('X',1))*V('sled ux')+(L('Y',V('i'))-L('Y',1))*V('sled uy')),setv('local y',(L('Y',V('i'))-L('Y',1))*V('sled ux')-(L('X',V('i'))-L('X',1))*V('sled uy')),setv('closest x',V('local x')),iff(cmp('lt',V('closest x'),V('segment ax')),[setv('closest x',V('segment ax'))]),iff(cmp('gt',V('closest x'),V('segment bx')),[setv('closest x',V('segment bx'))]),setv('closest y',V('segment y')),iff(cmp('equals',V('segment id'),3),[setv('closest x',3.8),setv('closest y',V('local y')),iff(cmp('lt',V('closest y'),-.3),[setv('closest y',-.3)]),iff(cmp('gt',V('closest y'),1.2),[setv('closest y',1.2)])]),setv('dx',V('local x')-V('closest x')),setv('dy',V('local y')-V('closest y')),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),setv('depth',L('Body radius',V('i'))-V('distance')),setv('contact lx',0),setv('contact ly',-1),iff(cmp('gt',V('distance'),.00001),[setv('contact lx',V('dx')/V('distance')),setv('contact ly',V('dy')/V('distance'))]),setv('previous local y',((L('PY',V('i'))-L('PY',1))*(L('PX',3)-L('PX',2))-(L('PX',V('i'))-L('PX',1))*(L('PY',3)-L('PY',2)))/15),iff(AND(AND(cmp('gt',V('local x'),V('segment ax')),cmp('lt',V('local x'),V('segment bx'))),AND(cmp('lt',V('previous local y'),V('segment y')),cmp('gt',V('local y'),V('segment y')-L('Body radius',V('i'))))),[setv('depth',V('local y')-V('segment y')+L('Body radius',V('i'))),setv('contact lx',0),setv('contact ly',-1)]),iff(cmp('gt',V('depth'),0),[setv('nx',V('sled ux')*V('contact lx')-V('sled uy')*V('contact ly')),setv('ny',V('sled uy')*V('contact lx')+V('sled ux')*V('contact ly')),setv('weight 4',V('closest x')/17.5),setv('weight 2',V('closest y')/5),setv('weight 1',1-V('weight 4')-V('weight 2')),setv('denominator',L('Inverse mass',V('i'))+L('Inverse mass',1)*V('weight 1')*V('weight 1')+L('Inverse mass',2)*V('weight 2')*V('weight 2')+L('Inverse mass',4)*V('weight 4')*V('weight 4')),setv('impulse',V('depth')/V('denominator')),replace('Sled contact',V('i'),L('Sled contact',V('i'))+V('impulse'))]+sum(([replace(axis,V('i'),L(axis,V('i'))+V(n)*V('impulse')*L('Inverse mass',V('i')))]+[replace(axis,j,L(axis,j)-V(n)*V('impulse')*V('weight '+str(j))*L('Inverse mass',j)) for j in [1,2,4]] for axis,n in [('X','nx'),('Y','ny')]),[])+[iff(AND(OR(cmp('equals',V('i'),5),OR(cmp('equals',V('i'),9),cmp('equals',V('i'),10))),cmp('lt',V('contact ly'),-.2)),[change('Support load',V('impulse'))]),iff(AND(AND(cmp('equals',V('i'),5),cmp('equals',V('segment id'),1)),cmp('lt',V('contact ly'),-.2)),[change('Seat load',V('impulse'))]),setv('contact vx',L('X',V('i'))-L('PX',V('i'))-V('weight 1')*(L('X',1)-L('PX',1))-V('weight 2')*(L('X',2)-L('PX',2))-V('weight 4')*(L('X',4)-L('PX',4))),setv('contact vy',L('Y',V('i'))-L('PY',V('i'))-V('weight 1')*(L('Y',1)-L('PY',1))-V('weight 2')*(L('Y',2)-L('PY',2))-V('weight 4')*(L('Y',4)-L('PY',4))),setv('tangent impulse',(V('contact vx')*(0-V('ny'))+V('contact vy')*V('nx'))/V('denominator')),setv('surface friction',V('Seat friction')),iff(AND(cmp('equals',V('segment id'),2),OR(cmp('equals',V('i'),9),cmp('equals',V('i'),10))),[setv('surface friction',V('Foot friction'))]),setv('friction limit',V('impulse')*V('surface friction')),iff(cmp('gt',V('tangent impulse'),V('friction limit')),[setv('tangent impulse',V('friction limit'))]),iff(cmp('lt',V('tangent impulse'),0-V('friction limit')),[setv('tangent impulse',0-V('friction limit'))])]+sum(([replace(prev,V('i'),L(prev,V('i'))+t*V('tangent impulse')*L('Inverse mass',V('i')))]+[replace(prev,j,L(prev,j)-t*V('tangent impulse')*V('weight '+str(j))*L('Inverse mass',j)) for j in [1,2,4]] for prev,t in [('PX',0-V('ny')),('PY',V('nx'))]),[]))]

 # Reject separated circle/segment pairs before their narrow-phase math.

 # The swept top-face test remains active for crossings from above.

 r=L('Body radius',V('i'))

 horizontal=AND(AND(cmp('gt',V('local x'),V('segment ax')-r-.000001),cmp('lt',V('local x'),V('segment bx')+r+.000001)),cmp('gt',V('local y'),V('segment y')-r-.000001))

 vertical=AND(cmp('lt',mathop('abs',V('local x')-3.8),r+.000001),AND(cmp('gt',V('local y'),-.3-r-.000001),cmp('lt',V('local y'),1.2+r+.000001)))

 near=OR(AND(cmp('equals',V('segment id'),3),vertical),AND(cmp('equals',cmp('equals',V('segment id'),3),0),horizontal))

 contact=contact[:3]+[iff(near,contact[3:])]

 proc('body sled contact',contact)

 deck=[]

 for a,b,y,id in [(0,15,5,2),(3.8,3.8,-.3,3),(0,7,1.2,1)]:

  deck += [setv('segment ax',a),setv('segment bx',b),setv('segment y',y),setv('segment id',id)]

  for i in colliders[1:]+colliders[:1]:deck += [setv('i',i),call('body sled contact')]

 proc('solve sled contacts',deck)

 # Static one-sided terrain, queried through the existing spatial index.

 terrain=[setv('dx',L('X',V('i'))-L('LX',V('j'))),setv('dy',L('Y',V('i'))-L('LY',V('j'))),setv('depth',V('dx')*L('NX',V('j'))+V('dy')*L('NY',V('j'))+L('Body radius',V('i'))),setv('along',(V('dx')*L('DX',V('j'))+V('dy')*L('DY',V('j')))*L('InvSq',V('j'))),setv('previous depth',(L('PX',V('i'))-L('LX',V('j')))*L('NX',V('j'))+(L('PY',V('i'))-L('LY',V('j')))*L('NY',V('j'))+L('Body radius',V('i'))),iff(AND(AND(cmp('gt',V('depth'),0),cmp('lt',V('previous depth'),L('Body radius',V('i'))+.75)),AND(cmp('gt',V('along'),-.000001),cmp('lt',V('along'),1.000001))),[replace('X',V('i'),L('X',V('i'))-L('NX',V('j'))*V('depth')),replace('Y',V('i'),L('Y',V('i'))-L('NY',V('j'))*V('depth')),iff(cmp('gt',V('depth'),L('Ground contact',V('i'))),[replace('Ground contact',V('i'),V('depth'))]),setv('terrain friction',.12),iff(cmp('lt',V('i'),5),[setv('terrain friction',L('Friction',V('i')))]),iff(cmp('equals',L('Material',V('j')),2),[setv('terrain friction',0)]),setv('terrain vx',L('X',V('i'))-L('PX',V('i'))),setv('terrain vy',L('Y',V('i'))-L('PY',V('i'))),setv('tangent impulse',V('terrain vx')*L('NY',V('j'))-V('terrain vy')*L('NX',V('j'))),setv('friction limit',V('depth')*V('terrain friction')),iff(cmp('gt',V('tangent impulse'),V('friction limit')),[setv('tangent impulse',V('friction limit'))]),iff(cmp('lt',V('tangent impulse'),0-V('friction limit')),[setv('tangent impulse',0-V('friction limit'))]),replace('PX',V('i'),L('PX',V('i'))+L('NY',V('j'))*V('tangent impulse')),replace('PY',V('i'),L('PY',V('i'))-L('NX',V('j'))*V('tangent impulse')),iff(cmp('equals',L('Material',V('j')),1),[setv('terrain vx',(L('X',V('i'))-L('PX',V('i')))*L('NY',V('j'))-(L('Y',V('i'))-L('PY',V('i')))*L('NX',V('j'))),replace('PX',V('i'),L('PX',V('i'))+L('NY',V('j'))*V('terrain vx')*.08),replace('PY',V('i'),L('PY',V('i'))-L('NX',V('j'))*V('terrain vx')*.08)]),iff(cmp('equals',L('Material',V('j')),4),[replace('PX',V('i'),L('PX',V('i'))-L('NY',V('j'))*.1),replace('PY',V('i'),L('PY',V('i'))+L('NX',V('j'))*.1)]),iff(cmp('equals',L('Material',V('j')),5),[replace('PX',V('i'),L('PX',V('i'))+L('NY',V('j'))*.1),replace('PY',V('i'),L('PY',V('i'))-L('NX',V('j'))*.1)])])]

 proc('terrain circle contact',terrain)

 query=[]

 for i in [1,2,3,4]+colliders:

  query += [setv('i',i),call('nearby lines'),setv('k',1),loop(length('Candidates'),[setv('j',L('Candidates',V('k'))),iff(cmp('equals',cmp('equals',L('Material',V('j')),3),0),[call('terrain circle contact')]),change('k',1)])]

 proc('collide points with lines',query)

 scarf=[]

 chain=[idx[k] for k in body['parts']['SCARF']]

 for a,b in zip(chain,chain[1:]):

  rest=math.hypot(pts[a-1]['x']-pts[b-1]['x'],pts[a-1]['y']-pts[b-1]['y'])

  scarf += [setv('dx',L('X',b)-L('X',a)),setv('dy',L('Y',b)-L('Y',a)),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(cmp('gt',V('distance'),.0001),[replace('X',b,L('X',a)+V('dx')*rest/V('distance')),replace('Y',b,L('Y',a)+V('dy')*rest/V('distance'))])]

 proc('solve scarf',scarf)

 observe=[call('sled coordinate frame'),setv('Seat gap',(L('Y',5)-L('Y',1))*V('sled ux')-(L('X',5)-L('X',1))*V('sled uy')),setv('Seat along',(L('X',5)-L('X',1))*V('sled ux')+(L('Y',5)-L('Y',1))*V('sled uy')),setv('Mounted',0),iff(AND(AND(cmp('lt',V('State'),3),cmp('gt',V('Support load'),.00001)),AND(cmp('lt',mathop('abs',V('Seat gap')),1.5),AND(cmp('gt',V('Seat along'),0),AND(cmp('lt',V('Seat along'),8.2),cmp('lt',(L('Y',6)-L('Y',5))*V('sled ux')-(L('X',6)-L('X',5))*V('sled uy'),-2))))),[setv('Mounted',1)]),iff(cmp('equals',V('Mounted'),0),[change('Flight frames',1)],[setv('Flight frames',0)]),iff(cmp('lt',V('Seat gap'),-3),[setv('Flight departed',1)]),setv('Ragdoll speed squared',0)]

 for i in rider:

  observe += [setv('vx',L('X',i)-L('PX',i)),setv('vy',L('Y',i)-L('PY',i)),iff(cmp('gt',V('vx')*V('vx')+V('vy')*V('vy'),V('Ragdoll speed squared')),[setv('Ragdoll speed squared',V('vx')*V('vx')+V('vy')*V('vy'))])]

 for i in [5,6,22]:observe += [iff(cmp('gt',L('Ground contact',i),.1),[setv('Flight failed',1)])]

 observe += [iff(cmp('lt',V('Ragdoll speed squared'),.025),[change('Ragdoll sleep frames',1)],[setv('Ragdoll sleep frames',0)])]

 proc('observe rider contacts',observe)

 # Viscous angular resistance removes spin energy while preserving translation.
 drag=[setv('sled vx',sum((L('X',i)-L('PX',i) for i in range(1,5)),0)/4),setv('sled vy',sum((L('Y',i)-L('PY',i) for i in range(1,5)),0)/4)]
 for i in range(1,5):
  drag += [replace('PX',i,L('PX',i)+(L('X',i)-L('PX',i)-V('sled vx'))*V('Angular drag')),replace('PY',i,L('PY',i)+(L('Y',i)-L('PY',i)-V('sled vy'))*V('Angular drag'))]
 proc('damp sled rotation',drag)
 proc('physics frame',[setv('Support load',0),setv('Seat load',0),setv('i',1),loop(count,[replace('Ground contact',V('i'),0),replace('Sled contact',V('i'),0),replace('Grip force',V('i'),0),change('i',1)]),call('integrate points'),loop(8,[call('solve body bones'),call('solve joint limits'),call('solve elastic grips'),call('solve rider balance'),call('collide points with lines'),call('solve sled contacts')]),call('solve scarf'),call('damp sled rotation'),call('observe rider contacts'),change('Frame',1)])

