import contact_reference as m
from course import default_track
orig=m.p['reset rider'];c=.5
def reset():m.v['Spawn Y']=22;orig();m.v['Seat compliance']=c
m.p['reset rider']=reset
for c in [0,.05,.1,.25,.5,1,2]:
 r=m.run(default_track(),400);free=[a['frame'] for a in r if a['h']<-3 and a['load']<1e-8 and max(a['grips'])<1e-8];print(c,'end',r[-1]['state'],r[-1]['frame'],'height',round(min(a['h'] for a in r),1),'free',len(free),flush=True)
