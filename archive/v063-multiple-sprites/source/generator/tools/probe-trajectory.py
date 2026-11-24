import math
import contact_reference as m
from course import default_track
r=m.run(default_track());
for a in r[110:]:
 x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15
 print(a['frame'],'sled',round(x[0],1),round(y[0],1),'angle',round(math.degrees(math.atan2(v,u)),1),'hip',round(x[4],1),round(y[4],1),'rel',round(a['a'],1),round(a['h'],1),'grip',*[round(g,4) for g in a['grips']],'contact',round(max(a['contacts'][i] for i in [4,5,6,7,8,9,17,18,19,20,21]),2),'ground',[(i+1,round(g,2)) for i,g in enumerate(a['ground']) if g>.01])
