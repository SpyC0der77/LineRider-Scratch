import math
import contact_reference as m
from course import default_track
orig=m.p['reset rider'];spring=.08
def reset():orig();m.v['Posture spring']=spring
m.p['reset rider']=reset
for spring in [.02,.05,.08,.12,.2,.3]:
 r=m.run(default_track());free=[a['frame'] for a in r if a['h']<-1 and a['load']<1e-8 and max(a['grips'])<1e-8];a=r[min(59,len(r)-1)];x,y=a['x'],a['y'];u=((x[5]-x[4])/5.5,(y[5]-y[4])/5.5)
 pose=[(round((x[i]-x[parent])*-u[1]+(y[i]-y[parent])*u[0],2),round(-(x[i]-x[parent])*u[0]-(y[i]-y[parent])*u[1],2)) for i,parent in [(6,5),(8,4)]]
 print(spring,'end',r[-1]['state'],r[-1]['frame'],'height',round(min(a['h'] for a in r),2),'free',len(free),'hand/foot',pose,flush=True)
