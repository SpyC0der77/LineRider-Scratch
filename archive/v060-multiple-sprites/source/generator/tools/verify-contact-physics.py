import json,math,copy
import contact_reference as m
from course import default_track
rows=m.run(default_track());assert rows[-1]['state']==4
free=[a['frame'] for a in rows if a['h']<-1 and a['load']<1e-8 and max(a['grips'])<1e-8];assert len(free)>=15
open('artifacts/contact-reference.json','w').write(json.dumps(rows))
# Mounted is observational: toggling it must not alter a single physical point.
row=rows[120]
def state_at(row):
 m.p['reset rider']();m.v['State']=1
 for k in ['X','Y']:m.l[k][:]=row[k.lower()]
 previous=rows[row['frame']-2]
 m.l['PX'][:]=previous['x'];m.l['PY'][:]=previous['y']
for flag in [0,1]:
 state_at(row);m.v['Mounted']=flag;m.p['physics frame']()
 result=(m.l['X'][:],m.l['Y'][:])
 if flag:assert result==first,'Mounted changes dynamics'
 else:first=result
# Seat contacts must not attract an airborne body or depend on a mode flag.
m.p['reset rider']();m.v['State']=1
for i in range(4,22):
 m.l['X'][i]=1000+i*20;m.l['Y'][i]=-100
m.l['X'][4]=5;m.l['Y'][4]=-4;m.l['PX'][:]=m.l['X'][:];m.l['PY'][:]=m.l['Y'][:]
x=m.l['X'][:];y=m.l['Y'][:];m.p['solve sled contacts']();assert m.l['X']==x and m.l['Y']==y,'seat attracts body'
# A compressing contact exchanges equal and opposite mass-weighted impulse.
m.p['reset rider']();m.v['State']=1
for i in range(4,22):m.l['X'][i]=1000+i*20;m.l['Y'][i]=-100
m.l['X'][4]=5;m.l['Y'][4]=.2;m.l['PX'][:]=m.l['X'][:];m.l['PY'][:]=m.l['Y'][:]
def com():return tuple(sum(m.l[k][i]/m.l['Inverse mass'][i] for i in [0,1,2,3,4]) for k in ['X','Y'])
before=com();m.p['solve sled contacts']();after=com();assert math.dist(before,after)<1e-9
# Elastic grip force tends smoothly to zero at slip distance, without latching.
forces=[]
for extension in [0,.01,.1,.5,1,1.5,1.9,1.99,2,2.01]:
 m.p['reset rider']();m.v['State']=1;m.l['X'][6]=17.5+math.sqrt(61)+extension;m.l['Y'][6]=0;m.l['X'][7]=1000;m.l['Y'][7]=-100;m.p['solve elastic grips']();forces.append(m.l['Grip force'][6])
assert forces[0]<1e-10 and forces[-1]==0 and forces[-2]==0 and 0<forces[-3]<forces[6]/50
# An end screen disables active grip forces until Retry resets the run.
m.v['State']=3;m.l['Grip force'][6]=0;m.l['X'][6]=17.5+math.sqrt(61)+.5;m.l['Y'][6]=0;m.p['solve elastic grips']();assert m.l['Grip force'][6]==0
print('PASS continuous contacts, momentum exchange, smooth elastic release, observational Mounted, terminal grip lock; free flight',free[0],free[-1],'finish',rows[-1]['frame'])
