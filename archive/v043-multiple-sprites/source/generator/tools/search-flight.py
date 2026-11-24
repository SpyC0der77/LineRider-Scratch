import importlib.util,math,itertools
spec=importlib.util.spec_from_file_location('tune','tools/tune-flight.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
for amp,width in itertools.product([42,44,46,48],[58,60,62,64,66]):
 def h(x):return 28+.4*x+amp*math.exp(-((x-350)/width)**2)
 rows=t.run([(x,h(x),x+4,h(x+4),0) for x in range(-100,1201,4)],225)
 off=[r for r in rows if not r['m']]
 if off and any(r['m'] for r in rows[off[0]['f']:]):print('CATCH',amp,width,'off',off[0]['f'],'on',next(r['f'] for r in rows[off[0]['f']:] if r['m']),'height',round(min(r['h'] for r in off),1),flush=True)
