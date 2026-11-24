import physics_model as m
from course import course_height
original=m.p['reset rider'];duration=16;compression=1.1;mass=1
def reset():original();m.v.update({'Release duration':duration,'Release compression':compression,'Binding mass':mass,'Goal X':1800,'Goal Y':course_height(1800)})
m.p['reset rider']=reset
lines=[(x,course_height(x),x+4,course_height(x+4),0) for x in range(-100,2000,4)]
for duration,compression,mass in [(16,1.1,1),(16,1.5,1),(16,1.1,1.2),(8,.8,.1),(10,1.1,1),(12,1.1,1)]:
 r=m.run(lines,500);print(duration,compression,mass,'end',r[-1]['state'],r[-1]['frame'],'height',round(min(a['h'] for a in r),1),'land',next((a['frame'] for a in r if a['landing']),0),'mounted',r[-1]['m'],flush=True)
