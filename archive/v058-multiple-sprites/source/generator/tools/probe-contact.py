import contact_reference as m
from course import default_track
orig=m.p['reset rider']
def reset():orig();m.v.update({'Balance stiffness':.7,'Grip stiffness':.02,'Seat friction':.4})
m.p['reset rider']=reset
r=m.run(default_track());free=[a for a in r if a['frame']>80 and a['load']<1e-8 and max(a['grips'])<1e-8];print('end',r[-1]['state'],r[-1]['frame'],'free',[(a['frame'],round(a['h'],2)) for a in free],'min',min(a['h'] for a in r));print('grip peak',max(max(a['grips']) for a in r))
