import math,json
import contact_reference as m
from course import default_track
orig=m.p['reset rider']
def reset():
 orig();m.v.update({'Grip stiffness':.05,'Seat back':3.8});m.l['Inverse mass'][22]=5
m.p['reset rider']=reset;r=m.run(default_track(),400)
print('END',r[-1]['state'],r[-1]['frame'])
for a in r:
 if a['frame']>=110 and (a['frame']<=160 or a['frame']%20==0):
  x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15;sdy=(y[5]-y[4])*u-(x[5]-x[4])*v
  print(a['frame'],'sled',round(x[0],1),'seat',round(a['a']+5,1),round(a['h'],1),'torso',round(sdy,1),'m',a['m'],'load',round(a['load'],2),'grip',round(max(a['grips']),3),'ground',[(i+1,round(g,2)) for i,g in enumerate(a['ground']) if i in [4,5,21] and g>.01])
open('artifacts/candidate.json','w').write(json.dumps(r))
