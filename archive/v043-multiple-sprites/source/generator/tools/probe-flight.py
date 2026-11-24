exec(open('tools/search-flight.py').read().split('orig=')[0])
def h(x):return 28+.4*x+40*math.exp(-((x-350)/70)**2)
r=t.run([(x,h(x),x+4,h(x+4),0) for x in range(-100,1201,4)],240)
print([(a['f'],a['m'],round(a['h'],1),round(a['a'],1),round(a['contact'],2)) for a in r if 100<=a['f']<=160])
