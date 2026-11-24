import itertools
import contact_reference as m
from course import default_track
orig=m.p['reset rider'];b=.4;g=.002
def reset():orig();m.v.update({'Balance stiffness':b,'Grip stiffness':g,'Seat friction':.4})
m.p['reset rider']=reset
for b,g in itertools.product([.3,.4,.5],[.001,.002,.004,.006,.008]):
 r=m.run(default_track());free=[a['frame'] for a in r if a['h']<-1 and a['load']<1e-8 and max(a['grips'])<1e-8]
 if r[-1]['state']==4:print('PASS',b,g,'free',free,'height',round(min(a['h'] for a in r),2),flush=True)
