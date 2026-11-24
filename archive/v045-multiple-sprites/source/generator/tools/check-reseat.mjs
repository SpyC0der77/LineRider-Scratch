import {EditorSession} from './editor-session.mjs';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';
const s=new EditorSession(),wait=ms=>new Promise(r=>setTimeout(r,ms));
const state=()=>s.call('get_variable_list_data');
async function until(c){for(let i=0;i<1200;i++){const v=await state();if(c(v))return v;await wait(10);}throw Error('Timed out '+JSON.stringify((await state()).variables));}
async function release(){await s.call('set_variable_values',{values:{'Capture hold':0}});await until(v=>+v.variables['Capture ready']===0);}
async function step(){const before=+(await state()).variables.Frame;await release();await s.call('set_variable_values',{values:{'Queued steps':1}});await until(v=>+v.variables.Frame>before||+v.variables['Crash complete']===1);await s.call('set_variable_values',{values:{'Capture hold':1}});return until(v=>+v.variables['Capture ready']===1);}
async function capture(name,values){await release();await s.call('set_variable_values',{values:{...values,'Capture hold':1}});await until(v=>+v.variables['Capture ready']===1);const r=await s.capture();await fs.writeFile('artifacts/'+name+'.png',Buffer.from(r.image_base64,'base64'));}
try{
 await s.openFile(process.cwd()+'/dist/Line Rider.sb3');await s.extract();await s.call('green_flag');await wait(500);
 if(!process.argv.includes('--terminal-only')){
 const rows=[];let off=0,on=0,maxHeight=0;
 for(let f=1;f<=300;f++){
  const v=await step(),n=v.variables,l=k=>v.lists[k].items.map(Number),x=l('X'),y=l('Y');
  const sx=(x[2]-x[1])/15,sy=(y[2]-y[1])/15,rx=x[4]-x[0]-(x[3]-x[0])*5/17.5,ry=y[4]-y[0]-(y[3]-y[0])*5/17.5,h=-rx*sy+ry*sx;
  rows.push({f:+n.Frame,m:+n.Mounted,state:+n.State,height:h,failed:+n['Flight failed'],contact:Math.max(...l('R contact depth').slice(4,10),...l('R contact depth').slice(17))});
  assert.equal(+n.Frame,f);assert.notEqual(+n.State,3,'Crash screen at frame '+f);assert.equal(+n['Flight failed'],0);
  if(!+n.Mounted){off ||=f;maxHeight=Math.max(maxHeight,-h);if(f>off+2)assert.ok(rows.at(-1).contact<=.05,'Terrain collision during flight');}else if(off&&!on)on=f;
  if(f===105)await capture('flight-after',{'Camera X':340,'Camera Y':140,Zoom:3});
  if(f===138)await capture('flight-airborne',{'Camera X':x[4]+15,'Camera Y':y[4]+5,Zoom:4});
  if(+n.State===4){assert.ok(off&&on&&on-off>=25);assert.ok(maxHeight>9);assert.equal(+n.Mounted,1);console.log('PASS no crash screen; airborne',off,'through',on-1,'catch',on,'finish',f,'clearance',maxHeight);break;}
 }
 assert.ok(rows.some(r=>r.state===4),'Did not finish');await fs.writeFile('artifacts/flight-verified.json',JSON.stringify(rows,null,2));
 }
 // Put the returning rider near the seat, then declare a terminal crash.
 await release();await s.call('green_flag');await wait(500);
 await s.call('set_variable_values',{values:{'Queued steps':145}});
 await until(v=>+v.variables.Frame===145);
 await s.call('set_variable_values',{values:{'Capture hold':1}});
 await until(v=>+v.variables['Capture ready']===1);
 await s.call('set_variable_values',{values:{State:3,'Crash frames':0,'Crash complete':0}});
 for(let i=0;i<20;i++){const v=await step();assert.equal(+v.variables.State,3,'Crash restarted');assert.equal(+v.variables.Mounted,0,'Crashed rider remounted');}
 console.log('PASS crash state remains terminal through the landing window');
 await s.call('set_variable_values',{values:{'Crash complete':1}});const f=+(await state()).variables.Frame;await step();assert.equal(+(await state()).variables.Frame,f);console.log('PASS completed crash cannot advance or catch');
 await release();await s.pressKeys([{key:'r',hold_duration_ms:70,time_after_last_key_press_ms:70}]);const retry=await until(v=>+v.variables.Frame<10&&+v.variables.Mounted===1);assert.equal(+retry.variables['Flight failed'],0);assert.equal(+retry.variables['Crash complete'],0);console.log('PASS explicit Retry clears the terminal state');
}finally{await s.close();}
