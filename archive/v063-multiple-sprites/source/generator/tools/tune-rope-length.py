import itertools,math
import contact_reference as m
from course import default_track
orig=m.p['reset rider'];ri=next(i for i,(a,b) in enumerate(zip(m.l['Bone A'],m.l['Bone B'])) if a==4 and b==23)
def reset():
 orig();m.v['Grip stiffness']=grip;m.l['Bone rest'][ri]=rope_length
m.p['reset rider']=reset;body=[4,5,6,7,8,9,17,18,19,20,21]
for rope_length,grip in itertools.product([9.5,10,10.5,11],[.03,.05,.08]):
 r=m.run(default_track(),350);free=[]
 for a in r:
  x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;d=math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
  if d>5 and max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7:free.append((a['frame'],d))
 print('END',r[-1]['state'],'length/grip',rope_length,grip,'held60',r[59]['grips'],'free',len(free),'peak',round(max((d for f,d in free),default=0),1),'frame',r[-1]['frame'],flush=True)
