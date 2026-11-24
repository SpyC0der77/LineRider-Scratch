import itertools,math
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=16;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():
 m.v['Spawn Y']=22;orig();m.v.update({'Goal X':1050,'Goal Y':lower(1050)})
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
for air,drop,wh in itertools.product([.005,.01,.02,.04],[8,16,24,32],[1,2]):
 for i in body:m.l['Initial air'][i]=air
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+wh,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if 378<=x<490 else 0) for x in range(354,1200,4)]
 r=m.run(lines,400);free=[]
 for a in r:
  x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;d=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
  if d>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:free.append((a['frame'],d))
 print('END',r[-1]['state'],'air/drop/lip',air,drop,wh,'free',len(free),'dist',round(max((d for f,d in free),default=0),1),'frame',r[-1]['frame'],flush=True)
