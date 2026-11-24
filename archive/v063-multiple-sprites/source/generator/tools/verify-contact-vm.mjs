import {EditorSession} from './editor-session.mjs';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';
const s=new EditorSession(),wait=ms=>new Promise(r=>setTimeout(r,ms));
const state=()=>s.call('get_variable_list_data');
async function until(check){
 for(let i=0;i<1800;i++){const v=await state();if(check(v))return v;await wait(10);}
 throw Error('Timed out '+JSON.stringify((await state()).variables));
}
async function release(){await s.call('set_variable_values',{values:{'Capture hold':0}});await until(v=>+v.variables['Capture ready']===0);}
async function hold(){await s.call('set_variable_values',{values:{'Capture hold':1}});return until(v=>+v.variables['Capture ready']===1);}
async function screenshot(row,name){
 await s.call('set_variable_values',{values:{'Camera X':row.x[0]+10,'Camera Y':row.y[0]-7,Zoom:5}});
 await release();await wait(80);await hold();const r=await s.capture();
 await fs.writeFile('artifacts/'+name+'.png',Buffer.from(r.image_base64,'base64'));
}
const body=[4,5,6,7,8,9,17,18,19,20,21];
function freeFlight(r){
 const u=(r.x[2]-r.x[1])/15,v=(r.y[2]-r.y[1])/15;
 const d=Math.hypot(r.x[4]-r.x[0]-5*u,r.y[4]-r.y[0]-5*v);
 return d>5&&Math.max(...body.map(i=>r.contacts[i]))<1e-7&&Math.max(...body.map(i=>r.ground[i]))<1e-7&&Math.max(...r.grips)<1e-7;
}
try{
 await s.openFile(process.cwd()+'/dist/Line Rider.sb3');await s.extract();await s.call('green_flag');await wait(500);
 const expected=JSON.parse(await fs.readFile('artifacts/contact-reference.json')),rows=[];let error=0;
 for(let frame=1;frame<=400;frame++){
  await release();await s.call('set_variable_values',{values:{'Queued steps':1}});
  await until(v=>+v.variables.Frame===frame||+v.variables['Crash complete']===1);
  const v=await hold(),n=v.variables;
  const row={frame:+n.Frame,m:+n.Mounted,state:+n.State,load:+n['Support load'],gap:+n['Seat gap'],grips:v.lists['Grip force'].items.slice(6,8).map(Number),contacts:v.lists['Sled contact'].items.map(Number),ground:v.lists['Ground contact'].items.map(Number),x:v.lists.X.items.map(Number),y:v.lists.Y.items.map(Number)};
  rows.push(row);assert.notEqual(row.state,3,'Crashed at '+frame);
  const ref=expected[frame-1];assert.ok(ref);
  for(const axis of ['x','y'])for(let i=0;i<ref[axis].length;i++)error=Math.max(error,Math.abs(row[axis][i]-ref[axis][i]));
  assert.ok(error<1e-6,'Reference mismatch at '+frame+': '+error);
  if(frame===60)await screenshot(row,'posture-after-60');
  if(frame>=105&&frame<=160)await screenshot(row,'demo-physics-'+frame);
  if(row.state===4)break;
 }
 assert.equal(rows.at(-1).state,4);
 const free=rows.filter(freeFlight);let longest=0,run=0,prev=-2;
 for(const row of free){run=row.frame===prev+1?run+1:1;longest=Math.max(longest,run);prev=row.frame;}
 assert.ok(longest>=5,'No sustained whole-body flight');
 assert.ok(rows.some(r=>r.frame>free.at(-1).frame&&r.m===1),'No seated return');
 await fs.writeFile('artifacts/contact-vm.json',JSON.stringify(rows,null,2));
 console.log('PASS Scratch VM/reference max error',error,'whole-body flight',free.map(r=>r.frame),'seated finish',rows.at(-1).frame);

 // A crash remains terminal even when physical motion continues through the return.
 await release();await s.call('green_flag');await wait(300);
 await s.call('set_variable_values',{values:{'Queued steps':120}});await until(v=>+v.variables.Frame===120);await hold();
 await s.call('set_variable_values',{values:{State:3,'Crash frames':0,'Crash complete':0}});
 for(let i=0;i<40;i++){
  const frame=+(await state()).variables.Frame;await release();await s.call('set_variable_values',{values:{'Queued steps':1}});
  await until(v=>+v.variables.Frame>frame);const v=await hold();
  assert.equal(+v.variables.State,3);assert.equal(+v.variables.Mounted,0);
  assert.equal(+v.lists['Grip force'].items[6],0);assert.equal(+v.lists['Grip force'].items[7],0);
 }
 console.log('PASS end screen stays terminal; no grip or restart');

 // Use the actual menus to prove Demo restores the new course and start flags.
 await release();await s.clickStage(331-240,180-20);await until(v=>+v.variables.Editing===1);
 await s.clickStage(36-240,180-20);await until(v=>+v.variables.Menu===1);
 await s.clickStage(95-240,180-55);await until(v=>+v.variables.Menu===0&&v.lists.LX.items.length===0);
 await s.clickStage(36-240,180-20);await until(v=>+v.variables.Menu===1);
 await s.clickStage(95-240,180-81);const restored=await until(v=>+v.variables.Menu===0&&v.lists.LX.items.length>0);
 const project=JSON.parse(await fs.readFile('dist/project.json')).targets[0];
 for(const name of ['LX','LY','DX','DY','Material'])assert.deepEqual(restored.lists[name].items.map(Number),project.lists[name][1].map(Number),name+' not restored');
 for(const name of ['Spawn X','Spawn Y','Goal X','Goal Y','Goal enabled'])assert.equal(+restored.variables[name],+project.variables[name][1],name+' not restored');
 console.log('PASS Track > Demo restores the tested course, materials, start and goal');
}finally{await s.close();}
