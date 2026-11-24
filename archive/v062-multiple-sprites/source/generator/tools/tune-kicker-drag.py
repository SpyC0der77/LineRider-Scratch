import itertools
import contact_reference as m
orig=m.p['reset rider'];wall=350;drop=8;slope=.3;drag=.15;boost=0
floor=lambda x:28+.3*x
lower=lambda x:floor(wall)+drop+slope*(x-wall)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':drag})
m.p['reset rider']=reset
for wh,drop,slope,drag,boost in itertools.product([1,3],[4,12,24],[.3,.7],[.1,.25],[0,32]):
 start=354;xs=list(range(-100,wall,4))+[wall];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(wall,floor(wall)+wh,wall,floor(wall)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if x<start+boost else 0) for x in range(start,1600,4)]
 r=m.run(lines,400)
 if r[-1]['state']==4:
  free=[a for a in r if a['h']<-4 and a['load']<1e-8 and max(a['grips'])<1e-8]
  print('PASS',wh,drop,slope,drag,boost,'height',round(min(a['h'] for a in r),1),'free',len(free),'frame',r[-1]['frame'],flush=True)
