import itertools,math
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=8;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':.3})
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
for wh,drop in itertools.product([1,1.5,2],[8,12,16]):
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+wh,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),0) for x in range(354,1600,4)]
 r=m.run(lines,400);air=False;landing=None;free=[]
 for a in r:
  x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;dx=x[4]-x[0]-5*u;dy=y[4]-y[0]-5*v
  if math.hypot(dx,dy)>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:air=True;free.append(a['frame'])
  if air and max(a['ground'][i] for i in body)>.2 and landing is None:landing=(a['frame'],round(dx,1),round(dy,1))
 print(wh,drop,'end',r[-1]['state'],'free',free,'ground',landing,flush=True)
