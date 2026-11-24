import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';const before=process.argv.includes('--before'),s=new EditorSession(),wait=ms=>new Promise(r=>setTimeout(r,ms));
const state=()=>s.call('get_variable_list_data');async function until(c){for(let i=0;i<1500;i++){let v=await state();if(c(v))return v;await wait(10);}throw Error('timeout '+JSON.stringify((await state()).variables));}
async function release(){await s.call('set_variable_values',{values:{'Capture hold':0}});await until(v=>+v.variables['Capture ready']===0);}
async function hold(){await s.call('set_variable_values',{values:{'Capture hold':1}});return until(v=>+v.variables['Capture ready']===1);}
try{await s.openFile(process.cwd()+'/'+(before?'artifacts/before-soft-landing.sb3':'dist/Line Rider.sb3'));await s.extract();await s.call('green_flag');await wait(500);await s.call('set_variable_values',{values:{'Queued steps':140}});await until(v=>+v.variables.Frame===140);await hold();const rows=[];
for(let frame=141;frame<=230;frame++){await release();await s.call('set_variable_values',{values:{'Queued steps':1}});await until(v=>+v.variables.Frame===frame||+v.variables['Crash complete']===1);let v=await hold();let row={frame:+v.variables.Frame,m:+v.variables.Mounted,landing:+v.variables['Landing frames']||0,state:+v.variables.State,failed:+v.variables['Flight failed'],x:v.lists.X.items.map(Number),y:v.lists.Y.items.map(Number),px:v.lists.PX.items.map(Number),py:v.lists.PY.items.map(Number)};rows.push(row);
if([149,154,160,170].includes(frame)){await release();await s.call('set_variable_values',{values:{'Camera X':675,'Camera Y':300,Zoom:3}});await hold();const r=await s.capture();await fs.writeFile('artifacts/landing-'+(before?'before':'after')+'-'+frame+'.png',Buffer.from(r.image_base64,'base64'));}
if(!before){assert.notEqual(row.state,3,'crash at '+frame);assert.equal(row.failed,0);}
if(row.state===4||+v.variables['Crash complete']===1)break;}
await fs.writeFile('artifacts/landing-'+(before?'before':'after')+'.json',JSON.stringify(rows,null,2));console.log(rows.map(r=>({frame:r.frame,m:r.m,landing:r.landing,state:r.state})).filter((r,i)=>!i||r.frame%5===0));if(!before)assert.ok(rows.some(r=>r.state===4),'finish');
}finally{await s.close();}
