import itertools,math
import contact_reference as m
orig=m.p['reset rider'];height=None
def reset():m.v['Spawn Y']=height(0)-6;orig();m.v['Goal X']=1800;m.v['Goal Y']=height(1800)
m.p['reset rider']=reset
for boost,amp,width in itertools.product([0,32,64,96],[-100,-60,40,80],[60,90,120]):
 def height(x):return 28+.4*x+amp*math.exp(-((x-350)/width)**2)
 lines=[(x,height(x),x+4,height(x+4),4 if 100<=x<100+boost else 0) for x in range(-100,2000,4)]
 r=m.run(lines,450);h=min(a['h'] for a in r)
 if r[-1]['state']==4:
  free=[a for a in r if a['h']<-4 and a['load']<1e-8 and max(a['grips'])<1e-8]
  print('PASS',boost,amp,width,'height',round(h,1),'free',len(free),'frame',r[-1]['frame'],flush=True)
 elif h<-10:print('FLIGHT',boost,amp,width,'height',round(h,1),'end',r[-1]['frame'],flush=True)
