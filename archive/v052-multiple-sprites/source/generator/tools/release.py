"""Continuous loss of seat support, preserving momentum during takeoff."""
def install(api):
 globals().update(api)
 begin=[setv('Release frames',1),call('activate ragdoll')]
 t=(V('Release frames')-1)/10
 weight=1-t*t*(3-2*t)
 # Convert the frame strength to per-pass stiffness. This prevents repeated
 # constraint iterations from making a partly released seat feel rigid.
 stiffness=1-mathop('sqrt',mathop('sqrt',mathop('sqrt',1-V('Seat attachment'))))
 fade=[iff(cmp('gt',V('Release frames'),0),[change('Release frames',1)],[iff(AND(cmp('equals',V('Release requested'),1),cmp('equals',V('Mounted'),1)),begin)]),iff(cmp('gt',V('Release frames'),0),[setv('Seat attachment',weight),iff(cmp('gt',V('Release frames'),10),[setv('Seat attachment',0),setv('Mounted',0),setv('Release frames',0)]),setv('Seat stiffness',stiffness)]),setv('Release requested',0)]
 proc('update seat release',[iff(OR(cmp('equals',V('State'),3),cmp('equals',V('Flight failed'),1)),[setv('Seat attachment',0),setv('Seat stiffness',0),setv('Mounted',0),setv('Release frames',0),setv('Release requested',0)],[iff(AND(cmp('equals',V('Landing frames'),0),cmp('lt',V('State'),3)),fade)])])
