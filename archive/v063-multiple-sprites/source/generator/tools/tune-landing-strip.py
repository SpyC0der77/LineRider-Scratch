import itertools
import contact_reference as m
from course import default_track
orig=m.p['reset rider'];spring=.05
for spring,start,length in itertools.product([.05,.08],[520,540,560,580,600,620],[4,8,12,20]):
 def reset():orig();m.v['Posture spring']=spring
 m.p['reset rider']=reset
 lines=[(x,y,xx,yy,1 if start<=x<start+length else material) for x,y,xx,yy,material in default_track()]
 r=m.run(lines,400)
 if r[-1]['state']==4:
  free=[a for a in r if a['h']<-3 and a['load']<1e-8 and max(a['grips'])<1e-8]
  print('PASS',spring,start,length,'height',round(min(a['h'] for a in r),1),'free',len(free),'frame',r[-1]['frame'],flush=True)
