# Independent numerical reading of upstream equations, used to check generated blocks.
import json,math,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
b=json.loads((root/'reference/lr-core/src/line-rider-engine/rider-data/index.json').read_text())
p=[dict(q,pos=[q['x'],q['y']],prev=[q['x']-.4,q['y']],vel=[.4,0]) for q in b['states'] if q['type']!='Binding'];ids={q['id']:q for q in p};mounted=True;intact=True
cs=[]
for c in b['constraints']:
 if c['type'] in ['Stick','BindStick','RepelStick']:
  a,z=ids[c['p1']],ids[c['p2']];rest=math.dist(a['pos'],z['pos'])*c.get('lengthFactor',1);cs.append((c,a,z,rest))
from course import default_track, DEFAULT_GOAL
tracks=default_track()
for frame in range(3000):
 for q in p:
  v=[(q['pos'][i]-q['prev'][i])*(1-q.get('airFriction',0))+(0 if i==0 else .175) for i in range(2)];q['vel']=v;q['prev']=q['pos'][:];q['pos']=[q['pos'][i]+v[i] for i in range(2)]
 for iteration in range(6):
  for c,a,z,rest in cs:
   if c['type']=='BindStick' and not mounted:continue
   d=[a['pos'][i]-z['pos'][i] for i in range(2)];le=math.hypot(*d)
   if not le:continue
   diff=(le-rest)/le*.5
   if c['type']=='BindStick' and diff>c['endurance']*rest*.5:mounted=False;continue
   if c['type']=='RepelStick' and le>=rest:continue
   for i in range(2):a['pos'][i]-=d[i]*diff;z['pos'][i]+=d[i]*diff
  for q in p[:10]:
   for x,y,xx,yy,m in tracks:
    dx,dy=xx-x,yy-y;le=math.hypot(dx,dy);nx,ny=-dy/le,dx/le;ox,oy=q['pos'][0]-x,q['pos'][1]-y;depth=ox*nx+oy*ny;along=(ox*dx+oy*dy)/(le*le)
    if not (0<depth<10 and -.000001<along<1.000001 and nx*q['vel'][0]+ny*q['vel'][1]>0):continue
    q['pos'][0]-=nx*depth;q['pos'][1]-=ny*depth
    fx,fy=ny*q.get('friction',0)*depth,-nx*q.get('friction',0)*depth
    if q['prev'][0]>q['pos'][0]-.0000001:fx=-fx
    if q['prev'][1]<q['pos'][1]:fy=-fy
    q['prev'][0]+=fx;q['prev'][1]+=fy
    if m==1:
     tangent=(q['pos'][0]-q['prev'][0])*ny-(q['pos'][1]-q['prev'][1])*nx
     q['prev'][0]+=ny*tangent*.08;q['prev'][1]-=nx*tangent*.08
 for c in b['constraints']:
  if c['type']=='BindJoint':
   a,z,q,r=[ids[c[k]]['pos'] for k in ['p1','p2','q1','q2']];cross=(z[0]-a[0])*(r[1]-q[1])-(z[1]-a[1])*(r[0]-q[0])
   if cross<0:
    if c['binding']=='RIDER_MOUNTED':mounted=False
    else:intact=False
 chain=[ids[k] for k in b['parts']['SCARF']]
 for a,z in zip(chain,chain[1:]):
  rest=math.hypot(a['x']-z['x'],a['y']-z['y']);d=[a['pos'][i]-z['pos'][i] for i in range(2)];le=math.hypot(*d)
  if le:
   for i in range(2):z['pos'][i]+=d[i]*(le-rest)/le

 if not mounted:
  print("CRASH",frame+1,ids["BUTT"]["pos"]);break
 if ids["BUTT"]["pos"][0]>DEFAULT_GOAL[0]:
  print("FINISH",frame+1,ids["BUTT"]["pos"]);break
else:print("TIMEOUT",ids["BUTT"]["pos"])
