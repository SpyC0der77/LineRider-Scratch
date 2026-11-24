"""Continuous loss of seat support, preserving momentum during takeoff."""
def install(api):
 globals().update(api)
 begin=[setv('Release frames',1)]
 t=(V('Release frames')-1)/10
 weight=1-t*t*(3-2*t)
 # Convert the frame strength to per-pass stiffness. This prevents repeated
 # constraint iterations from making a partly released seat feel rigid.
 stiffness=1-mathop('sqrt',mathop('sqrt',mathop('sqrt',1-V('Seat attachment'))))
 fade=[iff(cmp('gt',V('Release frames'),0),[change('Release frames',1)],[iff(AND(cmp('equals',V('Release requested'),1),cmp('equals',V('Mounted'),1)),begin)]),iff(cmp('gt',V('Release frames'),0),[setv('Seat attachment',weight),iff(cmp('gt',V('Release frames'),10),[setv('Seat attachment',0),setv('Mounted',0),setv('Release frames',0),call('activate ragdoll')]),setv('Seat stiffness',stiffness)]),setv('Release requested',0)]
 compression=((L('X',5)-L('X',1)-(L('X',4)-L('X',1))*5/17.5)*(L('Y',2)-L('Y',3))+(L('Y',5)-L('Y',1)-(L('Y',4)-L('Y',1))*5/17.5)*(L('X',3)-L('X',2)))/15
 unload=iff(AND(cmp('equals',V('Mounted'),1),AND(cmp('gt',compression,1.1),cmp('gt',L('VX',1),3))),[setv('Release requested',1)])
 proc('update seat release',[unload,iff(OR(cmp('equals',V('State'),3),cmp('equals',V('Flight failed'),1)),[setv('Seat attachment',0),setv('Seat stiffness',0),setv('Mounted',0),setv('Release frames',0),setv('Release requested',0)],[iff(AND(cmp('equals',V('Landing frames'),0),cmp('lt',V('State'),3)),fade)])])
