import itertools,math
import contact_reference as m
orig=m.p['reset rider']
def reset():orig();m.v.update({'Balance stiffness':.4,'Grip stiffness':.002,'Seat friction':.4})
m.p['reset rider']=reset
for amp,width in itertools.product([35,40,44,48,52,60],[50,58,65,75,85]):
 def h(x):return 28+.4*x+amp*math.exp(-((x-350)/width)**2)
 r=m.run([(x,h(x),x+4,h(x+4),0) for x in range(-100,1152,4)])
 if r[-1]['state']==4:print('PASS',amp,width,'h',round(min(a['h'] for a in r),2),'off',sum(not a['m'] for a in r),'frame',r[-1]['frame'],flush=True)
