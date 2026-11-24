import itertools,math
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;wh=2;slope=1;knee=460;boost=64

def lower(x):
 y=floor(350)+4+slope*(min(x,knee)-350)
 if x>knee:y+=.02*(min(x,knee+80)-knee)
 if x>knee+80:y+=.3*(x-knee-80)
 return y

def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':.3})
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
for wh,slope,knee,boost in itertools.product([2,3],[.6,1,1.4],[420,460,500],[32,64,96]):
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+wh,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if x<354+boost else 0) for x in range(354,1600,4)]
 r=m.run(lines,450)
 if r[-1]['state']==4:
  free=[]
  for a in r:
   x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;dist=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
   if dist>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:free.append((a['frame'],dist))
  print('PASS',wh,slope,knee,boost,'h',round(min(a['h'] for a in r),1),'free',len(free),'dist',round(max((d for f,d in free),default=0),1),'end',r[-1]['frame'],flush=True)
