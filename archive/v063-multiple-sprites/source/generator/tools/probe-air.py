import math
import contact_reference as m
floor=lambda x:28+.3*x;drop=24;lower=lambda x:floor(350)+drop+.3*(x-350)
for i in [4,5,6,7,8,9,17,18,19,20,21]:m.l['Initial air'][i]=.02
xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+2,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if 378<=x<490 else 0) for x in range(354,1200,4)]
r=m.run(lines,400)
for a in r:
 if a['x'][0]<330:continue
 x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15
 print(a['frame'],'sled',round(x[0],1),round(y[0],1),'angle',round(math.degrees(math.atan2(v,u)),1),'rel',round(a['a'],1),round(a['h'],1),'m',a['m'],'grip',round(max(a['grips']),3),'contact',round(max(a['contacts'][i] for i in [4,5,6,7,8,9,17,18,19,20,21]),2),'ground',[(i+1,round(g,2)) for i,g in enumerate(a['ground']) if g>.1])
