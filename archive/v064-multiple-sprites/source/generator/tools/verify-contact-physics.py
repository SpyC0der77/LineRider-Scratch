"""Regression checks for continuous rider physics and the physical demo stunt."""
import json, math
from pathlib import Path
import contact_reference as m
from course import default_track

BODY=[4,5,6,7,8,9,17,18,19,20,21]
def seat_distance(row):
 x,y=row['x'],row['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15
 return math.hypot(x[4]-x[0]-5*u,y[4]-y[0]-5*v)
def free_flight(row):
 return (seat_distance(row)>5 and max(row['contacts'][i] for i in BODY)<1e-7
         and max(row['ground'][i] for i in BODY)<1e-7 and max(row['grips'])<1e-7)
def longest_run(frames):
 longest=current=0;previous=-2
 for frame in frames:
  current=current+1 if frame==previous+1 else 1
  longest=max(longest,current);previous=frame
 return longest

rows=m.run(default_track(),400)
assert rows[-1]['state']==4,('Demo did not finish',rows[-1]['frame'],rows[-1]['state'])
free=[a['frame'] for a in rows if free_flight(a)]
assert longest_run(free)>=5,('No sustained whole-body flight',free)
assert max(seat_distance(a) for a in rows if free_flight(a))>=8
assert any(a['m']==1 for a in rows if a['frame']>free[-1]),'Rider did not return to the seat'
assert not any(a['failed'] for a in rows),'Body crashed before finishing'
Path('artifacts/contact-reference.json').write_text(json.dumps(rows))

# Compare the same steady riding state and camera as the before/after capture.
for a in [rows[59],rows[-1]]:
 x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15
 def local(i):return ((x[i]-x[0])*u+(y[i]-y[0])*v,(y[i]-y[0])*u-(x[i]-x[0])*v)
 hip=local(4);shoulder=local(5)
 assert 1<hip[0]<7 and abs(hip[1])<.3,('Outside the seat',a['frame'],hip)
 assert abs(shoulder[0]-hip[0])<1 and -6.1<shoulder[1]-hip[1]<-4.7
 for i in [6,7]:
  hand=local(i);assert 5<hand[0]-shoulder[0]<7.2 and -1<hand[1]-shoulder[1]<2.5,('Arm posture',a['frame'],i,hand)
 for i in [8,9]:
  foot=local(i);assert 4<foot[0]-hip[0]<6 and 3.5<foot[1]-hip[1]<5.3,('Leg posture',a['frame'],i,foot)

# Mounted is only an observation: changing it cannot change any physical point.
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

def isolated_seat(y):
 m.v.update({'Spawn X':0,'Spawn Y':0});m.p['reset rider']();m.v['State']=1
 for i in range(4,len(m.l['X'])):m.l['X'][i]=1000+i*20;m.l['Y'][i]=-100
 m.l['X'][4]=5;m.l['Y'][4]=y;m.l['PX'][:]=m.l['X'][:];m.l['PY'][:]=m.l['Y'][:]
def weighted_position(indices):
 return tuple(sum(m.l[k][i]/m.l['Inverse mass'][i] for i in indices) for k in ['X','Y'])
# No contact attraction, and equal/opposite reaction when the seat compresses.
isolated_seat(-4);x=m.l['X'][:];y=m.l['Y'][:];m.p['solve sled contacts']()
assert m.l['X']==x and m.l['Y']==y,'Seat attracts an airborne body'
isolated_seat(.2);before=weighted_position([0,1,2,3,4]);hip_y=m.l['Y'][4]
m.p['solve sled contacts']();after=weighted_position([0,1,2,3,4])
assert m.l['Y'][4]<hip_y and m.l['Sled contact'][4]>0,'Contact test did not compress the seat'
assert math.dist(before,after)<1e-9,'Contact does not conserve momentum'

# A physical loose rope exchanges force with the hand and yields continuously.
forces=[]
for distance in [0,.01,.1,.5,1,2,2.9,2.99,3,3.01]:
 m.p['reset rider']();m.v['State']=1
 m.l['X'][6]=m.l['X'][22]+distance;m.l['Y'][6]=m.l['Y'][22]
 m.l['X'][7]=1000;m.l['Y'][7]=-100
 before=weighted_position([6,22]);m.p['solve elastic grips']();after=weighted_position([6,22])
 force=m.l['Grip force'][6];forces.append(force)
 expected=.05*distance*(1-distance/3)**2 if 0<distance<3 else 0
 assert abs(force-expected)<1e-12,(distance,force,expected)
 assert math.dist(before,after)<1e-9,'Grip reaction does not conserve momentum'
assert forces[0]==forces[-1]==forces[-2]==0 and 0<forces[-3]<forces[-4]/50
for state in [3,4]:
 m.v['State']=state;m.l['Grip force'][6]=0
 m.l['X'][6]=m.l['X'][22]+.5;m.l['Y'][6]=m.l['Y'][22]
 m.p['solve elastic grips']();assert m.l['Grip force'][6]==0

project=json.loads(Path('dist/project.json').read_text())
variables=[v[0] for t in project['targets'] for v in t['variables'].values()]
for name in ['Ragdoll active','Landing frames','Release pose frame','Seat attachment','Ragdoll blend']:
 assert name not in variables,name
for name in ['Draw X','Draw Y','Release local X','Release local Y']:
 assert not any(v[0]==name for t in project['targets'] for v in t['lists'].values()),name
print('PASS seated posture, continuous contacts, momentum exchange, yielding grips, observational Mounted, terminal lock, direct physics rendering')
print('PASS demo whole-body flight',free,'longest',longest_run(free),'seated finish',rows[-1]['frame'])
