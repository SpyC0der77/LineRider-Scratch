/** Native controls, repeated release playback, fresh recordings and frame capture. */
import {EditorSession} from './editor-session.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';

process.env.SCRATCH_OPTIMIZER_HEADLESS='1';
process.env.LINE_RIDER_RELEASE_TEST='1';
const root=process.cwd(), out=path.join(root,'artifacts/extra-qa');
await fs.mkdir(path.join(out,'slow-frames'),{recursive:true});
const s=new EditorSession(), wait=ms=>new Promise(r=>setTimeout(r,ms));
const expected=JSON.parse(await fs.readFile('artifacts/contact-reference.json'));
const results=[], recordings=[], errors=[];
const state=()=>s.call('get_variable_list_data');
const click=(x,y)=>s.clickStage(x-240,180-y);
const key=k=>s.pressKeys([{key:k,hold_duration_ms:30,time_after_last_key_press_ms:50}]);
const positions=v=>['X','Y','PX','PY'].map(k=>v.lists[k].items.map(Number));
async function until(check,label,timeout=20000){
 const start=Date.now();
 while(Date.now()-start<timeout){const v=await state();if(check(v))return v;await wait(25);}
 throw Error('Timed out: '+label+' '+JSON.stringify((await state()).variables));
}
function compare(v){
 const frame=+v.variables.Frame;
 if(frame===0)return;
 const ref=expected[frame-1];assert.ok(ref,'Unexpected frame '+frame);
 let error=0;
 for(const axis of ['X','Y'])for(let i=0;i<ref[axis.toLowerCase()].length;i++)
  error=Math.max(error,Math.abs(+v.lists[axis].items[i]-ref[axis.toLowerCase()][i]));
 assert.ok(error<1e-7,'Physics differs at frame '+frame+': '+error);
}
async function fresh(){
 await s.call('green_flag');
 return until(v=>+v.variables.Editing===1&&+v.variables.Frame===0,'reset');
}
async function hold(){
 await s.call('set_variable_values',{values:{'Capture hold':1}});
 return until(v=>+v.variables['Capture ready']===1,'hold');
}
async function release(){
 await s.call('set_variable_values',{values:{'Capture hold':0}});
 await until(v=>+v.variables['Capture ready']===0,'release');
}
async function queued(frame){
 const now=+(await state()).variables.Frame;
 assert.ok(frame>=now);
 await s.call('set_variable_values',{values:{'Queued steps':frame-now}});
 return until(v=>+v.variables.Frame===frame,'queued '+frame);
}
async function snap(name){
 const r=await s.capture();await fs.writeFile(path.join(out,name+'.png'),Buffer.from(r.image_base64,'base64'));
}
async function startRecording(name){
 const info=await s.requirePage().evaluate(()=>{
  const canvas=document.querySelector('canvas[class*="stage_stage"]')||document.querySelector('canvas');
  const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(m=>MediaRecorder.isTypeSupported(m));
  const stream=canvas.captureStream(30), recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:4000000});
  const data=[];recorder.ondataavailable=e=>{if(e.data.size)data.push(e.data)};
  globalThis.__riderQARec={recorder,data,stream};recorder.start(200);
  return {width:canvas.width,height:canvas.height,mime};
 });
 recordings.push({name,...info});
}
async function stopRecording(name){
 const base64=await s.requirePage().evaluate(async()=>{
  const {recorder,data,stream}=globalThis.__riderQARec;
  await new Promise(resolve=>{recorder.onstop=resolve;recorder.stop()});stream.getTracks().forEach(t=>t.stop());
  const bytes=new Uint8Array(await new Blob(data,{type:recorder.mimeType}).arrayBuffer());
  let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
  delete globalThis.__riderQARec;return btoa(binary);
 });
 await fs.writeFile(path.join(out,name+'.webm'),Buffer.from(base64,'base64'));
}
async function finish(){
 const v=await until(v=>[3,4].includes(+v.variables.State),'finish');
 assert.equal(+v.variables.State,4,'Unexpected crash');compare(v);return v;
}
async function test(name,fn){
 const start=Date.now();
 try{const details=await fn();results.push({name,pass:true,seconds:(Date.now()-start)/1000,...details});console.log('PASS',name,details||'');}
 catch(e){results.push({name,pass:false,error:e.message});console.log('FAIL',name,e.message);}
 await fs.writeFile(path.join(out,'native-tests.json'),JSON.stringify({results,recordings,errors},null,2));
}

try{
 await s.openFile(path.join(root,'dist/Line Rider.sb3'));await s.extract();
 s.requirePage().on('pageerror',e=>errors.push(String(e)));

 await test('Release playback recorded at normal speed, then idle after finish',async()=>{
  await fresh();await s.call('set_variable_values',{values:{Zoom:5}});
  await startRecording('normal-playback');const start=Date.now();await click(315.333,56);
  const v=await finish();const seconds=(Date.now()-start)/1000;
  await wait(700);const idle=await state();assert.equal(+idle.variables.Frame,232);assert.deepEqual(positions(idle),positions(v));
  await snap('finished-idle');await stopRecording('normal-playback');
  return {frame:232,seconds,fps:232/seconds};
 });
 for(let run=1;run<=2;run++)await test('Repeated release run '+run,async()=>{
  if(run===1){await fresh();await key('space');}else await click(378,56);
  const v=await finish();return {frame:+v.variables.Frame};
 });

 await test('Pause near launch, wait, mouse/keyboard step, camera change and resume',async()=>{
  await fresh();await s.call('set_variable_values',{values:{Zoom:5}});await startRecording('pause-step-resume');
  await key('space');await until(v=>+v.variables.Frame>=108,'approach');await key('space');
  const paused=await until(v=>+v.variables.Playing===0,'pause');compare(paused);
  const frame=+paused.variables.Frame;assert.ok(frame<125,'Missed the jump pause');
  await wait(450);assert.deepEqual(positions(await state()),positions(paused));
  for(let n=1;n<=18;n++){
   if(n%2)await key('n');else await click(440.6667,56);
   const v=await until(v=>+v.variables.Frame===frame+n,'step');compare(v);assert.equal(+v.variables.Playing,0);
  }
  const before=await state();await s.call('set_variable_values',{values:{Zoom:3,'Camera X':-90,'Camera Y':-60}});
  await wait(150);assert.deepEqual(positions(await state()),positions(before));await key('n');compare(await state());
  await key('space');await finish();await stopRecording('pause-step-resume');return {pausedAt:frame,steps:19};
 });

 await s.loadCurrentFile(path.join(root,'dist/testing/Line Rider.sb3'));await s.extract();
 await test('Fresh frame-by-frame recording and exact native/reference comparison',async()=>{
  await fresh();const rows=[];
  for(let frame=1;frame<=232;frame++){
   await release();await queued(frame);let v=await hold();compare(v);
   rows.push({frame,m:+v.variables.Mounted,state:+v.variables.State,
    x:v.lists.X.items.map(Number),y:v.lists.Y.items.map(Number),
    grips:v.lists['Grip force'].items.slice(6,8).map(Number)});
   if(frame===60||(frame>=105&&frame<=210)){
    await s.call('set_variable_values',{values:{'Camera X':+v.lists.X.items[0]+10,'Camera Y':+v.lists.Y.items[0]-7,Zoom:5}});
    await release();await wait(45);v=await hold();compare(v);
    if(frame===60)await snap('hands-before-launch');
    else await snap('slow-frames/frame-'+String(frame).padStart(4,'0'));
    if([118,122,128,136,155,175,210].includes(frame))await snap('detail-'+frame);
   }
  }
  await release();await fs.writeFile(path.join(out,'native-motion.json'),JSON.stringify(rows));return {frames:232,maxPositionError:'<1e-7'};
 });

 await test('Fullscreen entered while airborne, stepped, exited and resumed',async()=>{
  await fresh();await queued(120);const before=await state();compare(before);
  await click(260,21);await until(v=>+v.variables['Full play']===1,'fullscreen');
  assert.deepEqual(positions(await state()),positions(before));
  for(let frame=121;frame<=130;frame++){await key('n');const v=await until(v=>+v.variables.Frame===frame,'fullscreen step');compare(v);}
  await click(456,24);await until(v=>+v.variables['Full play']===0,'exit fullscreen');
  await key('space');await finish();return {airborneSteps:10};
 });

 await test('Actual X crash during flight stays terminal; N is disabled after stop; Retry works',async()=>{
  await fresh();await queued(120);await s.call('set_variable_values',{values:{Zoom:5}});
  await startRecording('terminal-crash');await key('x');await key('n');
  await until(v=>+v.variables.State===3,'crash');await key('space');
  const stopped=await until(v=>+v.variables['Crash complete']===1,'crash complete');
  assert.equal(+stopped.variables.Playing,0);assert.equal(+stopped.variables.Mounted,0);
  assert.ok(stopped.lists['Grip force'].items.slice(6,8).every(x=>+x===0));
  const frame=+stopped.variables.Frame;await wait(600);await key('n');const idle=await state();
  assert.equal(+idle.variables.Frame,frame);assert.equal(+idle.variables.State,3);
  assert.deepEqual(positions(idle),positions(stopped));await snap('crash-terminal');await stopRecording('terminal-crash');
  await key('r');await until(v=>+v.variables.State===1&&+v.variables.Frame<30,'Retry');await finish();
  return {crashStopsAt:frame,retryFinishesAt:232};
 });
}finally{
 await fs.writeFile(path.join(out,'native-tests.json'),JSON.stringify({results,recordings,errors},null,2));await s.close();
}
if(results.some(r=>!r.pass)||errors.length)process.exitCode=1;
