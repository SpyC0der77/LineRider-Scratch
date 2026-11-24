import itertools
import physics_model as m
from course import default_track
original=m.p['reset rider'];physics=m.p['physics frame'];duration=10;amount=.04
def reset():original();m.v.update({'Release duration':duration,'Release compression':1.1,'Binding mass':1})
def frame():
 physics();l,v=m.l,m.v
 if v['Seat attachment'] or v['Sled supported'] or not v['Ragdoll active']:return
 vx=sum(l['X'][i]-l['PX'][i] for i in range(4))/4;vy=sum(l['Y'][i]-l['PY'][i] for i in range(4))/4
 for i in range(4):l['PX'][i]+=(l['X'][i]-l['PX'][i]-vx)*amount;l['PY'][i]+=(l['Y'][i]-l['PY'][i]-vy)*amount
m.p['reset rider']=reset;m.p['physics frame']=frame
for duration,amount in itertools.product([8,10,12,16,20],[.02,.04,.08,.12,.2,.35,.5]):
 r=m.run(default_track())
 if any(a['landing'] for a in r):print('LAND',duration,amount,'end',r[-1]['state'],r[-1]['frame'],'h',round(min(a['h'] for a in r),1),flush=True)
 if r[-1]['state']==4:print('PASS',duration,amount,flush=True)
