import itertools,math
import contact_reference as m
orig=m.p['reset rider'];e=.2
def reset():orig();m.v['Seat restitution']=e
m.p['reset rider']=reset
for e,amp,width in itertools.product([0,.2,.4],[-60,-35,25,44,65],[45,65,85,110]):
 def h(x):return 28+.4*x+amp*math.exp(-((x-350)/width)**2)
 r=m.run([(x,h(x),x+4,h(x+4),0) for x in range(-100,1152,4)],350)
 if r[-1]['state']==4:
  free=[a for a in r if a['h']<-3 and a['load']<1e-8 and max(a['grips'])<1e-8]
  print('PASS',e,amp,width,'height',round(min(a['h'] for a in r),1),'free',len(free),'frame',r[-1]['frame'],flush=True)
