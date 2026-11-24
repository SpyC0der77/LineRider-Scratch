import importlib.util,math,json,itertools
spec=importlib.util.spec_from_file_location('tune','tools/tune-flight.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
best=[]
for amp,width in itertools.product([-15,-25,-40,-60,-90,15,40,60],[20,35,50,70,100]):
 def h(x):return 28+.30*x+35*math.sin(x/140)+amp*math.exp(-((x-350)/width)**2)
 xs=range(-100,901,5);lines=[(x,h(x),x+5,h(x+5),0) for x in xs];rows=t.run(lines,240)
 off=[r for r in rows if not r['m']];clean=[]
 for r in off:
  if r['contact']>.05 and len(clean)>2:break
  clean.append(r)
 low=min((r['h'] for r in clean),default=0)
 if low<-5:print(amp,width,'clean',len(clean),'height',round(low,1),'catch',any(r['m'] for r in rows[off[0]['f']:]),flush=True);best.append((low,amp,width,len(clean)))
print('BEST',sorted(best)[:10])
