import itertools,math
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=16;drag=.4;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':drag})
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
for wh,drop,drag,boost in itertools.product([3,6],[12,24,40],[.25,.4,.6],[32,64,96]):
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+wh,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if x<354+boost else 0) for x in range(354,1600,4)]
 r=m.run(lines,400)
 if r[-1]['state']==4:
  free=[]
  for a in r:
   x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;dist=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
   if dist>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:free.append((a['frame'],dist))
  print('PASS',wh,drop,drag,boost,'height',round(min(a['h'] for a in r),1),'free',len(free),'dist',round(max((d for f,d in free),default=0),1),'end',r[-1]['frame'],flush=True)
