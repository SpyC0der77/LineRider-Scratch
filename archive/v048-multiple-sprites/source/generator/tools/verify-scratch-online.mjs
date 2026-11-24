import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';process.env.LINE_RIDER_RELEASE_TEST='1';
const root='C:/Users/Carter/code/Scratch/Line Rider',s=new EditorSession(),wait=ms=>new Promise(r=>setTimeout(r,ms));
const state=()=>s.call('get_variable_list_data');
async function until(c,label){const start=Date.now();while(Date.now()-start<20000){const v=await state();if(c(v))return v;await wait(40);}throw new Error('Timed out '+label);}
async function click(x,y){await s.clickStage(x-240,180-y);}
async function shot(name){const p=s.requirePage(),box=await p.$eval('canvas',e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}});await p.screenshot({path:root+'/artifacts/'+name+'.png',clip:box});}
const errors=[];
try{
 await s.openUrl('https://scratch.mit.edu/projects/1398648848/editor/');await s.extract();s.requirePage().on('pageerror',e=>errors.push(e.message));await s.call('green_flag');let v=await until(v=>+v.variables.Editing===1&&+v.variables.Mobile===1,'release startup');
 assert.ok(!('Capture hold' in v.variables)&&!('Capture ready' in v.variables)&&!('Queued steps' in v.variables));assert.equal(v.lists.LX.items.length,128);
 const screenshot=await s.capture();await fs.writeFile(root+'/artifacts/scratch-runtime-after.png',Buffer.from(screenshot.image_base64,'base64'));await click(32,20);await until(v=>+v.variables.Menu===1,'menu');await shot('mobile-after');await click(95,202);v=await until(v=>+v.variables['Code open']===1,'export');const code=v.variables['Code text'];assert.equal(code.length,823);await s.requirePage().waitForSelector('[class*="monitor_list-value"]');await shot('save-code-mobile');
 await click(402,295);await until(v=>+v.variables['Code open']===0,'close');await click(32,20);await until(v=>+v.variables.Menu===1,'menu');await click(95,228);await until(v=>+v.variables['Code open']===2,'load');const p=s.requirePage();await p.waitForSelector('[class*="question"] input');await p.focus('[class*="question"] input');await p.keyboard.sendCharacter(code);await p.keyboard.press('Enter');v=await until(v=>+v.variables['Code open']===0,'load complete');assert.equal(v.lists.LX.items.length,128);assert.equal(+v.variables.Mobile,1);
 await click(425,20);await until(v=>+v.variables.Editing===0,'Play');await shot('fullscreen-control-after');await click(260,21);v=await until(v=>+v.variables['Full play']===1,'fullscreen');assert.equal(+v.variables.Frame,0);await wait(120);await shot('fullscreen-after');await click(240,180);await until(v=>+v.variables.Frame>4,'play');await click(456,24);await until(v=>+v.variables['Full play']===0&&+v.variables.Playing===1,'exit');assert.deepEqual(errors,[],'native GUI runtime errors');console.log('PASS delivered file has no test state; mobile export/load, native code field, fullscreen and playback work without GUI errors');
}finally{await s.close();}
