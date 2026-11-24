"""Continuous loss of seat support, preserving momentum during takeoff."""
def install(api):
 globals().update(api)
 begin=[setv('Release frames',1),call('activate ragdoll'),setv('Ragdoll blend',0)]
 t=(V('Release frames')-1)/V('Release duration')
 weight=1-t*t*(3-2*t)
 # Convert the frame strength to per-pass stiffness. This prevents repeated
 # constraint iterations from making a partly released seat feel rigid.
 stiffness=1-mathop('sqrt',mathop('sqrt',mathop('sqrt',1-V('Seat attachment'))))
 fade=[iff(cmp('gt',V('Release frames'),0),[change('Release frames',1)],[iff(AND(cmp('equals',V('Release requested'),1),cmp('equals',V('Mounted'),1)),begin)]),iff(cmp('gt',V('Release frames'),0),[setv('Seat attachment',weight),iff(cmp('gt',V('Release frames'),V('Release duration')),[setv('Seat attachment',0),setv('Mounted',0),setv('Release frames',0)]),setv('Seat stiffness',stiffness),setv('Ragdoll blend',1-V('Seat attachment'))]),setv('Release requested',0)]
 compression=((L('X',5)-L('X',1)-(L('X',4)-L('X',1))*5/17.5)*(L('Y',2)-L('Y',3))+(L('Y',5)-L('Y',1)-(L('Y',4)-L('Y',1))*5/17.5)*(L('X',3)-L('X',2)))/15
 unload=iff(AND(cmp('equals',V('Mounted'),1),AND(cmp('gt',compression,V('Release compression')),cmp('gt',L('VX',1),3))),[setv('Release requested',1)])
 proc('update seat release',[unload,iff(OR(cmp('equals',V('State'),3),cmp('equals',V('Flight failed'),1)),[setv('Seat attachment',0),setv('Seat stiffness',0),setv('Mounted',0),setv('Release frames',0),setv('Release requested',0)],[iff(AND(cmp('equals',V('Landing frames'),0),cmp('lt',V('State'),3)),fade)])])

 # The seat still supports weight while the grip loosens. It can push the
 # rider upward with the sled, but cannot pull a lifting rider back down.
 seatx=L('X',1)+(L('X',4)-L('X',1))*5/17.5
 seaty=L('Y',1)+(L('Y',4)-L('Y',1))*5/17.5
 ux=(L('X',3)-L('X',2))/15
 uy=(L('Y',3)-L('Y',2))/15
 height=(L('X',5)-seatx)*(0-uy)+(L('Y',5)-seaty)*ux
 support=[setv('support height',height),iff(cmp('gt',V('support height'),0),[
  setv('support vx',L('X',5)-L('PX',5)),setv('support vy',L('Y',5)-L('PY',5)),
  setv('support inward',(V('support vx')-(L('X',1)-L('PX',1)))*(0-uy)+(V('support vy')-(L('Y',1)-L('PY',1)))*ux),
  iff(cmp('lt',V('support inward'),0),[setv('support inward',0)]),
  replace('X',5,L('X',5)+uy*V('support height')),replace('Y',5,L('Y',5)-ux*V('support height')),
  replace('PX',5,L('X',5)-(V('support vx')+uy*V('support inward'))),replace('PY',5,L('Y',5)-(V('support vy')-ux*V('support inward')))])]
 proc('solve releasing seat',[iff(AND(cmp('gt',V('Release frames'),0),cmp('lt',V('State'),3)),support)])

 deck=[]
 for i in [6,7,8,18,19,22]:
  h=(L('X',i)-L('X',2))*(0-uy)+(L('Y',i)-L('Y',2))*ux+L('R radius',i)*V('Ragdoll blend')+.5
  deck += [setv('support height',h),iff(cmp('gt',V('support height'),0),[replace('X',i,L('X',i)+uy*V('support height')),replace('Y',i,L('Y',i)-ux*V('support height')),replace('PX',i,L('PX',i)+uy*V('support height')),replace('PY',i,L('PY',i)-ux*V('support height'))])]
 proc('solve release deck',[iff(AND(cmp('gt',V('Release frames'),0),cmp('lt',V('State'),3)),deck)])
