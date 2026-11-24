import math
import contact_reference as m
from course import default_track
orig=m.p['reset rider'];f=.4;s=.4
def reset():orig();m.v['Foot friction']=f;m.v['Seat friction']=s
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
for f,s in [(.08,.4),(.15,.4),(.25,.4),(.4,.4),(.6,.4),(.4,.8)]:
 r=m.run(default_track(),350);a=r[min(59,len(r)-1)];free=[]
 for q in r:
  x,y=q['x'],q['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;d=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
  if d>5 and max(q['contacts'][i] for i in body)<1e-7 and max(q['ground'][i] for i in body)<1e-7 and max(q['grips'])<1e-7:free.append((q['frame'],d))
 print(f,s,'hip60',round(a['a']+5,2),'end',r[-1]['state'],r[-1]['frame'],'free',len(free),'dist',round(max((d for t,d in free),default=0),1),flush=True)
