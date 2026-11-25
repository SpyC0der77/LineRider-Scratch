import {EditorSession} from './editor-session.mjs';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';
const root=decodeURIComponent(new URL('..',import.meta.url).pathname).replace(/^\/(?=[A-Za-z]:)/,'').replace(/\/$/,''), s=new EditorSession();
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const state=()=>s.call('get_variable_list_data');
async function until(check,label,ms=25000){const start=Date.now();while(Date.now()-start<ms){const v=await state();if(check(v))return v;await wait(35);}throw new Error('Timed out '+label);}
async function click(x,y){await s.clickStage(x-240,180-y);}
async function key(k){await s.pressKeys([{key:k,hold_duration_ms:60,time_after_last_key_press_ms:60}]);}
async function menu(){await click(32,20);await until(v=>+v.variables.Menu===1,'Track menu');}
async function saveCode(){await menu();await click(95,202);return until(v=>+v.variables['Code open']===1,'save code');}
async function answer(code){const p=s.requirePage();await p.waitForSelector('[class*="question"] input');await p.focus('[class*="question"] input');await p.keyboard.sendCharacter(code);await p.keyboard.press('Enter');}
async function loadCode(code){await menu();await click(95,228);await until(v=>+v.variables['Code open']===2,'load prompt');await wait(120);await answer(code);return until(v=>[0,3].includes(+v.variables['Code open']),'decode');}
async function close(){await click(402,295);await until(v=>+v.variables['Code open']===0,'close');}
async function snap(name,dom=false){
 if(dom){const p=s.requirePage();const box=await p.$eval('canvas',e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};});await p.screenshot({path:root+'/artifacts/'+name+'.png',clip:box});return;}
 await s.call('set_variable_values',{values:{'Capture hold':1}});await until(v=>+v.variables['Capture ready']===1,'capture hold');
 const r=await s.capture();await fs.writeFile(root+'/artifacts/'+name+'.png',Buffer.from(r.image_base64,'base64'));
 await s.call('set_variable_values',{values:{'Capture hold':0}});await until(v=>+v.variables['Capture ready']===0,'release');
}
const alphabet='0123456789ABCDEFGHJKMNPQRSTVWXYZ';
function encode(track,meta){
 let chars=[],hash=1;
 function unsigned(n,hashing=true){do{const d=n%16+(n>=16?16:0);n=Math.floor(n/16);chars.push(alphabet[d]);if(hashing)hash=(hash*33+d)%65521;}while(n);}
 const signed=n=>unsigned(n<0?-n*2-1:n*2), q=n=>Math.round(n*100);
 unsigned(track.length);unsigned(meta.goal);for(const n of meta.flags)signed(q(n));
 let px=0,py=0;for(const [x,y,xx,yy,m] of track){const a=q(x),b=q(y),c=q(xx),d=q(yy),connected=a===px&&b===py;unsigned(m*2+Number(connected));if(!connected){signed(a-px);signed(b-py);}signed(c-a);signed(d-b);px=c;py=d;}
 unsigned(hash,false);return 'LR1'+chars.join('');
}
function geometry(v){return v.lists.LX.items.map((x,i)=>[+x,+v.lists.LY.items[i],+x+ +v.lists.DX.items[i],+v.lists.LY.items[i]+ +v.lists.DY.items[i],+v.lists.Material.items[i]]);}
function metadata(v){return {goal:+v.variables['Goal enabled'],flags:['Spawn X','Spawn Y','Goal X','Goal Y'].map(n=>+v.variables[n])};}
function expectTrack(v,track,meta){
 assert.equal(v.lists.LX.items.length,track.length);const actual=geometry(v);
 for(let i=0;i<track.length;i++)for(let j=0;j<5;j++)assert.ok(Math.abs(actual[i][j]-Math.round(track[i][j]*100)/100)<1e-7,`${i}:${j} ${actual[i][j]} != ${track[i][j]}`);
 assert.deepEqual(metadata(v),{goal:meta.goal,flags:meta.flags.map(n=>Math.round(n*100)/100)});
 for(const name of ['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']){assert.equal(v.lists[name].items.length,track.length);assert.ok(v.lists[name].items.every(n=>Number.isFinite(+n)));}
}
const metrics={};
try{
 await s.openFile(root+'/dist/Line Rider.sb3');await s.extract();await s.call('green_flag');await until(v=>+v.variables.Editing===1&&+v.variables.Zoom===1.8,'startup');await wait(350);
 const original=await state(), originalTrack=geometry(original), originalMeta=metadata(original);
 await menu();await snap('save-code-after');await key('q');
 let start=Date.now(),v=await saveCode();metrics.exportMs=Date.now()-start;
 const code=v.variables['Code text'];assert.ok(code.startsWith('LR1'));assert.equal(code,encode(originalTrack,originalMeta));assert.deepEqual(v.lists['Track code'].items,[code]);assert.equal(+v.variables.Dirty,0);assert.equal(v.lists['Undo Count'].items.length,0);
 await fs.writeFile(root+'/artifacts/demo-track-code.txt',code+'\n');metrics.characters=code.length;metrics.segmentJsonCharacters=JSON.stringify(originalTrack).length;metrics.reductionPercent=Math.round((1-code.length/metrics.segmentJsonCharacters)*1000)/10;
 console.log('PASS native export matches independent format encoder',metrics);await snap('save-code-dialog',true);
 // Verify the actual native list offers a selectable text field for copying.
 const page=s.requirePage();await page.waitForSelector('[class*="monitor_list-value"]');await page.click('[class*="monitor_list-value"]',{clickCount:2});await page.keyboard.down('Control');await page.keyboard.press('KeyA');await page.keyboard.up('Control');const selection=await page.evaluate(()=>{const e=document.activeElement;return {tag:e.tagName,value:e.value,start:e.selectionStart,end:e.selectionEnd,text:window.getSelection().toString()}});console.log('PASS full save code can be selected and copied');assert.ok(selection.text===code||(selection.value===code&&selection.end-selection.start===code.length),'full save code can be selected');
 await close();await key('s');await until(v=>+v.variables['Saved exists']===1,'save slot');
 await menu();await click(95,54);await until(v=>v.lists.LX.items.length===0,'new');
 start=Date.now();v=await loadCode(code);metrics.importMs=Date.now()-start;if(+v.variables['Code open']!==0)console.log('DECODE DEBUG',Object.fromEntries(Object.entries(v.variables).filter(([k])=>k.startsWith('Code '))));assert.equal(+v.variables['Code open'],0,v.variables['Code error']);expectTrack(v,originalTrack,originalMeta);assert.equal(v.lists['Saved LX'].items.length,originalTrack.length);console.log('PASS default round trip, collision caches rebuilt, saved slot retained');
 await key('z');await until(v=>v.lists.LX.items.length===0,'undo import');await key('y');v=await until(v=>v.lists.LX.items.length===originalTrack.length,'redo import');console.log('PASS import is undoable and redoable');
 const frozen=JSON.stringify(geometry(v)), history=v.lists['Undo Count'].items.length;
 const invalid=[code.slice(0,-1),code.slice(0,20)+'!'+code.slice(21),code+'0',code.slice(0,-1)+(code.at(-1)==='0'?'1':'0'),'LR2'+code.slice(3),encode([[0,0,0,0,0]],originalMeta),encode([[0,0,1,0,7]],originalMeta),encode([[0,0,1000001,0,0]],originalMeta)];
 for(const bad of invalid){v=await loadCode(bad);assert.equal(+v.variables['Code open'],3);assert.ok(v.variables['Code error']);assert.equal(JSON.stringify(geometry(v)),frozen);assert.equal(v.lists['Undo Count'].items.length,history);await click(282,295);await until(v=>+v.variables['Code open']===0,'cancel invalid');}
 console.log('PASS truncated, corrupt, trailing, wrong-version, zero-length, material and range failures keep track/history');
 v=await loadCode('');assert.equal(JSON.stringify(geometry(v)),frozen);assert.equal(v.lists['Undo Count'].items.length,history);console.log('PASS empty input cancels without mutation');
 const mixed=[[-100.125,-20.4,5.1,50.2,0],[5.1,50.2,20.8,10.9,1],[200.23,-100.78,201.01,-100.78,2],[-12.34,-50.12,-12.34,120.56,3]];
 const mixedMeta={goal:0,flags:[-45.123,9.887,1234.56,-999.99]};
 v=await loadCode(' \n'+encode(mixed,mixedMeta).toLowerCase().match(/.{1,30}/g).join('-\n')+'\t');assert.equal(+v.variables['Code open'],0,v.variables['Code error']);expectTrack(v,mixed,mixedMeta);console.log('PASS disconnected/vertical segments, all four materials, negative flags, disabled goal, whitespace and lowercase');
 v=await saveCode();assert.equal(v.variables['Code text'],encode(mixed,mixedMeta));await close();console.log('PASS stable encode-decode-encode');
 // Use the demo for the modal test so a short crash cannot end the ride first.
 v=await loadCode(code);expectTrack(v,originalTrack,originalMeta);
 await until(v=>+v.variables['Timeline ready']===1&&+v.variables['Timeline loading']===0,'demo timeline');
 await click(315.3333333333333,56);await until(v=>+v.variables.Playing===1&&+v.variables.Frame>0,'run');v=await saveCode();const frame=+v.variables.Frame;await wait(250);assert.equal(+(await state()).variables.Frame,frame);assert.equal(+v.variables.Editing,0);await close();await until(v=>+v.variables.Frame>frame,'resume');
 await menu();await click(95,228);await until(v=>+v.variables['Confirm open']===1,'load from Play confirmation');await click(264,219);await until(v=>+v.variables['Confirm open']===0,'cancel mode change');assert.equal(+(await state()).variables.Editing,0);
 await menu();await click(95,228);await until(v=>+v.variables['Confirm open']===1,'confirm again');await click(378,219);await until(v=>+v.variables['Code open']===2&&+v.variables.Editing===1,'accept mode change');await wait(100);await answer(code);v=await until(v=>+v.variables['Code open']===0,'load after confirm');expectTrack(v,originalTrack,originalMeta);console.log('PASS Play export pauses/resumes; loading uses existing mode-change confirmation');
 // The documented capacity is exercised in stock Scratch's VM, including string limits.
 const large=Array.from({length:3000},(_,i)=>[i*2,Math.floor(i/20),i*2+2,Math.floor((i+1)/20),i%4]);
 const largeCode=encode(large,originalMeta);start=Date.now();v=await loadCode(largeCode);assert.equal(+v.variables['Code open'],0,v.variables['Code error']);expectTrack(v,large,originalMeta);metrics.maxImportMs=Date.now()-start;metrics.maxCodeCharacters=largeCode.length;
 start=Date.now();v=await saveCode();assert.equal(v.variables['Code text'],largeCode);metrics.maxExportMs=Date.now()-start;await close();console.log('PASS all 3000 segments round trip',metrics);
 // Return to a representative export for delivery screenshots.
 v=await loadCode(code);await saveCode();await snap('save-code-dialog',true);await close();await menu();await click(95,228);await until(v=>+v.variables['Code open']===2,'final load prompt');await snap('load-code-dialog',true);await answer('');await until(v=>+v.variables['Code open']===0,'final cancel');
 await fs.writeFile(root+'/artifacts/track-code-metrics.json',JSON.stringify(metrics,null,2));
}finally{await s.close();}
