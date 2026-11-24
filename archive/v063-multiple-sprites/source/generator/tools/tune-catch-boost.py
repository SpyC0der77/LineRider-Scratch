import itertools,math,json
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=8;drag=.3;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():
 m.v['Spawn Y']=22;orig();m.v.update({'Goal X':1050,'Goal Y':lower(1050),'Angular drag':drag})
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
best=[]
for wh,drop,start,length,drag in itertools.product([1,2],[8,16,24],[378,390,402],[48,96],[.3]):
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+wh,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if start<=x<start+length else 0) for x in range(354,1200,4)]
 r=m.run(lines,350);free=[]
 for a in r:
  x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;d=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
  if d>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:free.append((a['frame'],d))
 if r[-1]['state']==4 or len(free)>10:
  print('END',r[-1]['state'],'lip/drop/start/len/drag',wh,drop,start,length,drag,'free',len(free),'dist',round(max((d for f,d in free),default=0),2),'frame',r[-1]['frame'],flush=True)
 if r[-1]['state']==4:best.append((len(free),max((d for f,d in free),default=0),wh,drop,start,length,drag))
print('BEST',sorted(best,reverse=True))
