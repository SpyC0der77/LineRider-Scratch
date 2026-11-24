import math
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;lower=lambda x:floor(350)+8+.3*(x-350)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':.3})
m.p['reset rider']=reset;xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+1,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),5 if 392<=x<408 else 0) for x in range(354,1600,4)]
r=m.run(lines,400);body=[4,5,6,7,8,9,17,18,19,20,21]
print('end',r[-1]['state'],r[-1]['frame']);free=[]
for a in r:
 x,y=a['x'],a['y'];sx,sy=(x[2]-x[1])/15,(y[2]-y[1])/15;dist=math.hypot(x[4]-x[0]-5*sx,y[4]-y[0]-5*sy)
 if max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7 and dist>5:free.append((a['frame'],round(dist,1)))
 if 112<=a['frame']<=145 and a['frame']%2==0:print(a['frame'],round(a['h'],1),round(a['a'],1),round(dist,1),round(max(a['contacts'][i] for i in body),2),round(max(a['ground'][i] for i in body),2))
print('FREE',free)
