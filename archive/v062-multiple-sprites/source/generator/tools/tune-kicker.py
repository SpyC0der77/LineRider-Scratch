import itertools
import contact_reference as m
orig=m.p['reset rider'];wall=350;drop=24;start=370;boost=0
floor=lambda x:28+.3*x
lower=lambda x:floor(wall)+drop+.3*(x-wall)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v['Goal X']=1400;m.v['Goal Y']=lower(1400)
m.p['reset rider']=reset
for wallheight,drop,gap,boost in itertools.product([3,6,10],[12,24,40],[4,20,40],[0,16]):
 start=wall+gap;xs=list(range(-100,wall,4))+[wall];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]
 lines += [(wall,floor(wall)+wallheight,wall,floor(wall)-.1,0)]
 lines += [(x,lower(x),x+4,lower(x+4),4 if x<start+boost else 0) for x in range(start,1600,4)]
 r=m.run(lines,400);height=min(a['h'] for a in r)
 if r[-1]['state']==4:
  free=[a for a in r if a['h']<-4 and a['load']<1e-8 and max(a['grips'])<1e-8]
  print('PASS',wallheight,drop,gap,boost,'height',round(height,1),'free',len(free),'frame',r[-1]['frame'],flush=True)
 elif height<-15:print('AIR',wallheight,drop,gap,boost,'height',round(height,1),'end',r[-1]['frame'],flush=True)
