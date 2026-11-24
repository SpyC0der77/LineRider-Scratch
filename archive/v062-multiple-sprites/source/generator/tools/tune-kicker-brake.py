import itertools
import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=16;drag=.25;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':drag})
m.p['reset rider']=reset
body=[4,5,6,7,8,9,17,18,19,20,21]
for drop,drag,brake,start,length in itertools.product([8,16,24],[.15,.3],[1,5],[360,376,392],[4,8,16]):
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+1,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),brake if start<=x<start+length else 0) for x in range(354,1600,4)]
 r=m.run(lines,400)
 if r[-1]['state']==4:
  free=[a for a in r if max(a['contacts'][i] for i in body)<1e-7 and max(a['ground'][i] for i in body)<1e-7 and max(a['grips'])<1e-7]
  print('PASS',drop,drag,brake,start,length,'height',round(min(a['h'] for a in r),1),'free',len(free),'frame',r[-1]['frame'],flush=True)
