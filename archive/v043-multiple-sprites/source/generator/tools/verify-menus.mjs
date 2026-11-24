import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';const root='C:/Users/Carter/code/Scratch/Line Rider';const s=new EditorSession();const wait=ms=>new Promise(r=>setTimeout(r,ms));const state=()=>s.call('get_variable_list_data');
async function releaseFrame(){await s.call('set_variable_values',{values:{'Capture hold':0}});for(let i=0;i<100&&+(await state()).variables['Capture ready']===1;i++)await wait(20);}
async function freezeFrame(){
 await releaseFrame();
 for(let pass=0;pass<5;pass++){
  await s.call('set_variable_values',{values:{'Capture hold':1}});
  for(let i=0;i<500&&+(await state()).variables['Capture ready']!==1;i++){if(+(await state()).variables['Capture hold']===0)await s.call('set_variable_values',{values:{'Capture hold':1}});await wait(20);}
  const v=await state();assert.equal(+v.variables['Capture ready'],1);
  if(+v.variables['Queued click']===0 && v.lists['Input keys'].items.length===0)return;
  await releaseFrame();
 }
 throw new Error('Input queue did not settle');
}
async function flush(){await freezeFrame();await releaseFrame();}
const key=async k=>{await s.pressKeys([{key:k,hold_duration_ms:60,time_after_last_key_press_ms:60}]);await flush();if(k==='e'&&+(await state()).variables['Confirm open']===1){await s.pressKeys([{key:'Enter',hold_duration_ms:80,time_after_last_key_press_ms:80}]);await flush();}};
const click=async(x,y)=>{await s.clickStage(x-240,180-y);await flush();};
async function snap(n){
 const v=await state();const canHold=Object.hasOwn(v.variables,'Capture hold');
 if(canHold)await freezeFrame();else await wait(600);
 try{const r=await s.capture();await fs.writeFile(root+'/artifacts/'+n+'.png',Buffer.from(r.image_base64,'base64'));}finally{if(canHold)await releaseFrame();}
}
const open=async(x,y,id)=>{await click(x,y);for(let i=0;i<40&&+(await state()).variables.Menu!==id;i++)await wait(30);assert.equal(+(await state()).variables.Menu,id);};
try{
 await s.openFile(root+'/artifacts/editor-buttons.sb3');await s.extract();await s.call('green_flag');await wait(300);await snap('menus-before');
 await s.loadCurrentFile(root+'/dist/Line Rider.sb3');await s.extract();await s.call('green_flag');await wait(400);await snap('menus-after');
 await open(32,20,1);await snap('menus-track');let v=await state();const lines=v.lists.LX.items.length;
 // Load is disabled; the menu retains focus and no canvas stroke is created.
 await click(90,133);assert.equal(+(await state()).variables.Menu,1);assert.equal((await state()).lists.LX.items.length,lines);console.log('PASS disabled load item');
 await click(450,280);assert.equal(+(await state()).variables.Menu,0);assert.equal((await state()).lists.LX.items.length,lines);assert.equal(+(await state()).variables.Drawing,0);console.log('PASS outside click consumes input');
 await open(90,20,2);await snap('menus-edit');await key('q');assert.equal(+(await state()).variables.Menu,0);console.log('PASS Q closes menu');
 await open(68,56,5);await snap('menus-tools');await click(95,121);assert.equal(+(await state()).variables.Tool,1);assert.equal(+(await state()).variables.Menu,0);console.log('PASS tool selection');
 await open(194,56,6);await snap('menus-materials');await click(190,147);assert.equal(+(await state()).variables.Brush,2);console.log('PASS direct material selection');
 await open(32,20,1);await click(95,168);assert.equal(+(await state()).variables['Goal enabled'],0);console.log('PASS remove goal');await snap('menus-goal-off');await key('z');assert.equal(+(await state()).variables['Goal enabled'],1);await key('y');assert.equal(+(await state()).variables['Goal enabled'],0);console.log('PASS goal toggle undo/redo');
 await open(32,20,1);await click(95,168);assert.equal(+(await state()).variables['Goal enabled'],1);console.log('PASS restore goal');await open(32,20,1);await click(95,168);await s.call('set_variable_values',{values:{'Goal X':1,'Goal Y':0}});await click(315.3333333333333,56);await wait(650);assert.notEqual(+(await state()).variables.State,4);await key('e');await s.call('set_variable_values',{values:{'Goal X':620,'Goal Y':106}});await open(32,20,1);await click(95,168);console.log('PASS removed goal cannot finish a run');
 await open(32,20,1);await click(95,54);assert.equal((await state()).lists.LX.items.length,0);console.log('PASS New via dropdown');
 await s.dragStage([[-160,20],[-80,0],[0,-25]],120);await flush();assert.ok((await state()).lists.LX.items.length>3);console.log('PASS drawing after menu closes');
 await open(90,20,2);await click(130,54);assert.equal((await state()).lists.LX.items.length,0);await open(90,20,2);await click(130,80);assert.ok((await state()).lists.LX.items.length>3);console.log('PASS Undo/Redo menu actions');
 await open(32,20,1);await click(95,107);assert.equal(+(await state()).variables['Saved exists'],1);await open(32,20,1);await click(95,54);await open(32,20,1);await click(95,133);assert.ok((await state()).lists.LX.items.length>3);console.log('PASS save/load menu');await open(32,20,1);await click(95,168);await open(32,20,1);await click(95,107);await open(32,20,1);await click(95,54);await open(32,20,1);await click(95,133);assert.equal(+(await state()).variables['Goal enabled'],0);console.log('PASS removed goal saved and loaded');
 await open(148,20,3);const zoom=+(await state()).variables.Zoom;await click(195,54);assert.ok(+(await state()).variables.Zoom>zoom);await open(148,20,3);await key('ArrowDown');await key('Enter');assert.equal(+(await state()).variables.Menu,0);assert.ok(Math.abs(+(await state()).variables.Zoom-zoom)<1e-9);console.log('PASS keyboard selection');
 await open(148,20,3);await click(195,166);assert.equal(+(await state()).variables.Grid,1);console.log('PASS checked grid item');
 await open(205,20,4);await click(245,54);assert.equal(+(await state()).variables.Help,1);await click(240,200);assert.equal(+(await state()).variables.Help,0);console.log('PASS Help dropdown');
 await open(32,20,1);await click(95,80);await key('g');await click(315.3333333333333,56);await wait(600);v=await state();assert.equal(+v.variables.Editing,0);assert.ok(+v.variables.Frame>5);console.log('PASS play button');await open(90,20,2);const beforeFrame=+(await state()).variables.Frame;await wait(250);assert.equal(+(await state()).variables.Frame,beforeFrame);await key('q');v=await state();assert.equal(+v.variables.Editing,0);console.log('PASS game menu pauses physics; Q preserves run');await key('e');assert.equal(+(await state()).variables.Editing,1);console.log('PASS return to editor');
 await s.loadCurrentFile(root+'/dist/Line Rider.sb3');await s.call('green_flag');await wait(1500);for(let i=0;i<60;i++)await s.pressKeys([{key:'n',hold_duration_ms:100,time_after_last_key_press_ms:100}]);for(let i=0;i<100&&+(await state()).variables.Frame<60;i++)await wait(30);assert.equal(+(await state()).variables.Frame,60);v=await state();const expected=JSON.parse(await fs.readFile(root+'/artifacts/expected.json'));let error=0;for(const n of ['X','Y'])for(let i=0;i<17;i++)error=Math.max(error,Math.abs(+v.lists[n].items[i]-expected[n][i]));assert.ok(error<1e-7);console.log('PASS physics regression',error);
 await s.loadCurrentFile(root+'/dist/Line Rider.sb3');await s.call('green_flag');await wait(300);await snap('menus-after');await open(68,56,5);await snap('menus-open');
}finally{await s.close();}
