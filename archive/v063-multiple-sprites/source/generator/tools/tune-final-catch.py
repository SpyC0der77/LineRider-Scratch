import itertools,math,json
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=8;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1050,'Goal Y':lower(1050),'Angular drag':.3})
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21];best=[]
for drop,start,length in itertools.product([8,10,12,14],[388,392,396],[12,16,20]):
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+1,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),5 if start<=x<start+length else 0) for x in range(354,1200,4)]
 r=m.run(lines,350)
 if r[-1]['state']==4:
  free=[]
  for a in r:
   x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;dist=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
   if dist>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:free.append((a['frame'],dist))
  score=max((d for f,d in free),default=0)
  print('PASS',drop,start,length,'free',len(free),'dist',round(score,1),'height',round(min(a['h'] for a in r),1),'end',r[-1]['frame'],flush=True);best.append((score,len(free),drop,start,length))
print('BEST',sorted(best,reverse=True)[:5])
