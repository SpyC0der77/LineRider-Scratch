import contact_reference as m
orig=m.p['reset rider'];check=m.p['check result'];floor=lambda x:28+.3*x;drop=16;drag=.15;lower=lambda x:floor(350)+drop+.3*(x-350);jump=False
body=[4,5,6,7,8,9,17,18,19,20,21]
def reset():
 global jump
 jump=False;m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':drag})
def result():
 global jump
 check();x,y=m.l['X'],m.l['Y'];hipdist=((x[4]-x[0]-5)**2+(y[4]-y[0])**2)**.5
 contact=max(m.l['Sled contact'][i] for i in body);ground=max(m.l['Ground contact'][i] for i in body)
 if hipdist>8 and contact<1e-7 and ground<1e-7 and max(m.l['Grip force'][6:8])<1e-7:jump=True
 if jump and ground>.2 and contact<1e-7:m.v['State']=3
m.p['reset rider']=reset;m.p['check result']=result
for drop in [8,12,16,20,24,32]:
 for drag in [x/100 for x in range(3,31,2)]:
  xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+1,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),0) for x in range(354,1600,4)]
  r=m.run(lines,400)
  if r[-1]['state']==4 and jump:print('PASS',drop,drag,'h',round(min(a['h'] for a in r),1),'frame',r[-1]['frame'],flush=True)
