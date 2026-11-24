import contact_reference as m
orig=m.p['reset rider'];floor=lambda x:28+.3*x;drop=4;lower=lambda x:floor(350)+drop+.3*(x-350)
def reset():m.v['Spawn Y']=floor(0)-6;orig();m.v.update({'Goal X':1400,'Goal Y':lower(1400),'Angular drag':.25})
m.p['reset rider']=reset
for drop in [4,12,24]:
 xs=list(range(-100,350,4))+[350];lines=[(a,floor(a),b,floor(b),0) for a,b in zip(xs,xs[1:])]+[(350,floor(350)+1,350,floor(350)-.1,0)]+[(x,lower(x),x+4,lower(x+4),4 if x<386 else 0) for x in range(354,1600,4)]
 r=m.run(lines,400);print('drop',drop,'end',r[-1]['state'],r[-1]['frame']);print([(a['frame'],round(a['x'][0]),round(a['x'][4]),round(a['h'],1),round(a['a'],1),a['m'],round(a['load'],1)) for a in r if a['frame']>=110 and a['frame']%5==0])
