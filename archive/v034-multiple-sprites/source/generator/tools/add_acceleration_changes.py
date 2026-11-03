from pathlib import Path
p=Path('tools/core.py');s=p.read_text();s=s.replace('# Noniterating bind joints and scarf chain.',"""# Match lr-core AccLine's 0.1 directed tangent applied to previous position.
for material,direction in [(4,1),(5,-1)]:
 contact[-1][2].append(iff(cmp('equals',L('Material',V('j')),material),[
  replace('PX',V('i'),L('PX',V('i'))-L('NY',V('j'))*.1*direction),
  replace('PY',V('i'),L('PY',V('i'))+L('NX',V('j'))*.1*direction)]))
# Noniterating bind joints and scarf chain.""");p.write_bytes(s.encode())
for f in ['tools/build.py','tools/ragdoll.py']:
 p=Path(f);s=p.read_text().replace("cmp('lt',L('Material',V('j')),3)","cmp('equals',cmp('equals',L('Material',V('j')),3),0)")
 if f.endswith('build.py'):s=s.replace("iff(cmp('equals',L('Material',V('j')),3),[color('#b6b1a9')])", "iff(cmp('equals',L('Material',V('j')),3),[color('#b6b1a9')]),iff(cmp('gt',L('Material',V('j')),3),[color('#a13d32')])")
 p.write_bytes(s.encode())
p=Path('tools/menus.py');s=p.read_text().replace("['Normal','Grip','Ice','Scenery']","['Normal','Grip','Ice','Scenery','Acceleration','Reverse boost']").replace("labels+=['Grip','Ice','Scenery']","labels+=['Grip','Ice','Scenery','Acceleration','Reverse boost']");p.write_bytes(s.encode())
p=Path('tools/track_code.py');s=p.read_text().replace("V('Code token'), 7", "V('Code token'), 11");p.write_bytes(s.encode())
p=Path('converter/dist/converter.mjs');s=p.read_text().replace('[0,1,2,3].includes(l[4])','[0,1,2,3,4,5].includes(l[4])').replace('token>7','token>11').replace('let acceleration=0,direction=0,extension=0','let direction=0,extension=0').replace('if(r.type===1)acceleration++;','').replace("if(xx<x)[x,y,xx,yy]=[xx,yy,x,y];return [x,y,xx,yy,r.type===2?3:0];", "const reverse=xx<x;if(reverse)[x,y,xx,yy]=[xx,yy,x,y];return [x,y,xx,yy,r.type===2?3:r.type===1?(reverse?5:4):0];")
a=s.index('if(acceleration)warnings.push(');b=s.index('if(direction)',a);s=s[:a]+s[b:];p.write_bytes(s.encode())
p=Path('converter/dist/index.html');s=p.read_text().replace('Acceleration, reversed collision sides and endpoint extensions need changes.','Reversed collision sides and endpoint extensions need changes.').replace('Normal lines stay normal. Scenery stays scenery.', 'Normal lines stay normal. Acceleration lines keep their boost direction. Scenery stays scenery.');p.write_bytes(s.encode())
p=Path('converter/dist/app.mjs');s=p.read_text().replace("'#88877e'][l[4]]", "'#88877e','#a13d32','#a13d32'][l[4]]");p.write_bytes(s.encode())
p=Path('converter/test.mjs');s=p.read_text().replace('warnings.length,2','warnings.length,1');s+="\nassert.equal(parse(JSON.stringify({...fixture,lines:[{type:1,x1:0,y1:0,x2:10,y2:0}]})).lines[0][4],4);assert.equal(parse(JSON.stringify(lossy),{allowLossy:true}).lines[0][4],5);for(const m of [4,5])assert.equal(decode(encode({lines:[[0,28,100,28,m]],flags:[0,0,0,0],goal:0})).lines[0][4],m);\n";p.write_bytes(s.encode())
