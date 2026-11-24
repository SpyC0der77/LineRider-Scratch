"""Blend the seated drawing into the physical flight pose without changing motion."""
def install(api):
 globals().update(api)
 count=len(pts)
 for name in ['Release local X','Release local Y','Release angle delta','Draw X','Draw Y']:lists[name]=[name,[0]*count]
 ux=(L('X',3)-L('X',2))/15;uy=(L('Y',3)-L('Y',2))/15
 remember=[]
 for i in range(5,count+1):
  dx=L('X',i)-L('X',1);dy=L('Y',i)-L('Y',1)
  remember += [replace('Release local X',i,dx*ux+dy*uy),replace('Release local Y',i,dy*ux-dx*uy),replace('Release angle delta',i,0)]
 proc('remember seated pose',[iff(AND(cmp('equals',V('Mounted'),1),cmp('equals',V('Ragdoll active'),0)),remember)])
 advance=[iff(cmp('equals',V('Release pose seen'),0),[setv('Release pose frame',1),setv('Release pose seen',1)],[iff(cmp('gt',V('Release pose frame'),0),[change('Release pose frame',1),iff(cmp('gt',V('Release pose frame'),15),[setv('Release pose frame',0)])])])]
 proc('advance release pose',[iff(cmp('equals',V('Mounted'),1),[setv('Release pose frame',0),setv('Release pose seen',0)],[iff(AND(cmp('lt',V('State'),3),AND(cmp('equals',V('Flight failed'),0),cmp('equals',V('Landing frames'),0))),advance,[setv('Release pose frame',0),setv('Release pose seen',1)])])])
 # atan2 and unwrapped relative angles keep a limb from flipping at +/-180.
 proc('release bone angle',[iff(cmp('lt',mathop('abs',V('release dx')),.00001),[setv('release angle',90),iff(cmp('lt',V('release dy'),0),[setv('release angle',-90)])],[setv('release angle',mathop('atan',V('release dy')/V('release dx'))),iff(cmp('lt',V('release dx'),0),[change('release angle',180)])])])
 ease=[setv('release t',(V('Release pose frame')-1)/V('release duration')),iff(cmp('gt',V('release t'),1),[setv('release t',1)]),setv('release blend',V('release t')*V('release t')*(3-2*V('release t')))]
 child=V('release child');parent=V('release parent')
 adx=L('Release local X',child)-L('Release local X',parent);ady=L('Release local Y',child)-L('Release local Y',parent)
 bone=[setv('release dx',adx*V('release ux')-ady*V('release uy')),setv('release dy',adx*V('release uy')+ady*V('release ux')),setv('release anchor length',mathop('sqrt',V('release dx')*V('release dx')+V('release dy')*V('release dy'))),call('release bone angle'),setv('release anchor angle',V('release angle')),setv('release dx',L('X',child)-L('X',parent)),setv('release dy',L('Y',child)-L('Y',parent)),setv('release actual length',mathop('sqrt',V('release dx')*V('release dx')+V('release dy')*V('release dy'))),call('release bone angle'),setv('release delta',V('release angle')-V('release anchor angle')),iff(cmp('gt',V('release delta')-L('Release angle delta',child),180),[change('release delta',-360)]),iff(cmp('lt',V('release delta')-L('Release angle delta',child),-180),[change('release delta',360)]),replace('Release angle delta',child,V('release delta'))]+ease+[setv('release angle',V('release anchor angle')+V('release delta')*V('release blend')),setv('release length',V('release anchor length')+(V('release actual length')-V('release anchor length'))*V('release blend')),replace('Draw X',child,L('Draw X',parent)+V('release length')*mathop('cos',V('release angle'))),replace('Draw Y',child,L('Draw Y',parent)+V('release length')*mathop('sin',V('release angle')))]
 proc('blend release bone',bone)
 prepare=[setv('release point',1),loop(count,[replace('Draw X',V('release point'),L('X',V('release point'))),replace('Draw Y',V('release point'),L('Y',V('release point'))),change('release point',1)])]
 blend=[setv('release ux',ux),setv('release uy',uy),setv('release duration',12)]+ease
 # Position the hips continuously; articulated angles handle the rest of the body.
 ax=L('X',1)+L('Release local X',5)*V('release ux')-L('Release local Y',5)*V('release uy')
 ay=L('Y',1)+L('Release local X',5)*V('release uy')+L('Release local Y',5)*V('release ux')
 blend += [replace('Draw X',5,ax+(L('X',5)-ax)*V('release blend')),replace('Draw Y',5,ay+(L('Y',5)-ay)*V('release blend'))]
 for child,parent,duration in [(6,5,12),(9,5,8),(10,5,8),(7,6,14),(8,6,14),(22,6,12)]:
  blend += [setv('release child',child),setv('release parent',parent),setv('release duration',duration),call('blend release bone')]
 # Keep the scarf joined to the displayed shoulder throughout the blend.
 for i in range(11,18):
  blend += [replace('Draw X',i,L('X',i)+L('Draw X',6)-L('X',6)),replace('Draw Y',i,L('Y',i)+L('Draw Y',6)-L('Y',6))]
 proc('prepare rider drawing',prepare+[iff(cmp('gt',V('Release pose frame'),0),blend)])
