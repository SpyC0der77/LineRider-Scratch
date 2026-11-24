import itertools,math
import physics_model as m
from course import default_track
for bounce,friction in itertools.product([.1,.25,.5,.75,1,1.5,2,3],[0,.2,.6]):
 point_velocity=False
 def support():
  v,l=m.v,m.l
  if not(v['Release frames']>0 and v['State']<3):return
  x,y,px,py=[l[k] for k in ['X','Y','PX','PY']];ux,uy=(x[2]-x[1])/15,(y[2]-y[1])/15
  seatx,seaty=x[0]+(x[3]-x[0])*5/17.5,y[0]+(y[3]-y[0])*5/17.5
  h=(x[4]-seatx)*-uy+(y[4]-seaty)*ux
  if h<=0:return
  svx,svy=x[0]-px[0],y[0]-py[0]
  if point_velocity:svx=seatx-(px[0]+(px[3]-px[0])*5/17.5);svy=seaty-(py[0]+(py[3]-py[0])*5/17.5)
  vx,vy=x[4]-px[4],y[4]-py[4];rel=max(0,(vx-svx)*-uy+(vy-svy)*ux)*(1+bounce);tan=((vx-svx)*ux+(vy-svy)*uy)*friction*m.v['Seat attachment']
  x[4]+=uy*h;y[4]-=ux*h;px[4]=x[4]-(vx+uy*rel-ux*tan);py[4]=y[4]-(vy-ux*rel-uy*tan)
 m.p['solve releasing seat']=support
 r=m.run(default_track());h=min(a['h'] for a in r)
 print(bounce,friction,'end',r[-1]['state'],r[-1]['frame'],'height',round(h,1),'along',round(r[-1]['a'],1),flush=True)
