import contact_reference as m
from course import default_track
orig=m.p['reset rider'];restitution=.2
def reset():orig();m.v['Seat restitution']=restitution
m.p['reset rider']=reset
for restitution in [0,.1,.2,.3,.5]:
 r=m.run(default_track(),400);free=[a['frame'] for a in r if a['h']<-3 and a['load']<1e-8 and max(a['grips'])<1e-8];print(restitution,'end',r[-1]['state'],r[-1]['frame'],'height',round(min(a['h'] for a in r),1),'free',len(free),flush=True)
