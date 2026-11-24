import itertools
import physics_model as m
from course import default_track
original=m.p['reset rider'];duration=10;compression=1.1;mass=1
def reset():original();m.v.update({'Release duration':duration,'Release compression':compression,'Binding mass':mass})
m.p['reset rider']=reset
for duration,compression,mass in itertools.product([8,10,12,16],[.8,1.1,1.5],[.1,.3,.5,.7,1]):
 r=m.run(default_track())
 if any(a['landing'] for a in r):print('LAND',duration,compression,mass,'end',r[-1]['state'],r[-1]['frame'],'h',round(min(a['h'] for a in r),1),flush=True)
 if r[-1]['state']==4:print('PASS',duration,compression,mass,flush=True)
