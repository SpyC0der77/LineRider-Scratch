import {EditorSession} from './editor-session.mjs';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

process.env.SCRATCH_OPTIMIZER_HEADLESS='1';
process.env.LINE_RIDER_RELEASE_TEST='1';
const s=new EditorSession(),wait=ms=>new Promise(r=>setTimeout(r,ms));
const errors=[];
const file=path.join(process.cwd(),'dist/Line Rider - before jump-out.sb3');
async function state(){return s.call('get_variable_list_data');}
async function until(test,label){
 const started=Date.now();
 while(Date.now()-started<25000){const v=await state();if(test(v))return v;await wait(40);}
 throw Error('Timed out '+label);
}
try{
 await s.openFile(file);await s.extract();
 s.requirePage().on('pageerror',e=>errors.push(e.message));
 await s.call('green_flag');
 const initial=await until(v=>+v.variables.Editing===1&&+v.variables.Frame===0,'startup');
 assert.equal(initial.lists.LX.items.length,413);
 assert.ok(!('Support load' in initial.variables));
 assert.ok(!('Leg balance stiffness' in initial.variables));
 await s.clickStage(315.333-240,180-56);
 let finish;
 for(let i=0;i<600;i++){
  const v=await state();assert.notEqual(+v.variables.State,3,'Baseline crashed');
  assert.equal(+v.variables.Mounted,1,'Rider left the sled');
  if(+v.variables.State===4){finish=v;break;}
  await wait(30);
 }
 assert.ok(finish,'Did not finish');
 assert.equal(+finish.variables.Playing,0);
 assert.deepEqual(errors,[]);
 const result={file,segments:413,finishFrame:+finish.variables.Frame,riderStayedMounted:true,pageErrors:errors};
 await fs.writeFile('artifacts/pre-jump-build-verification.json',JSON.stringify(result,null,2));
 console.log('PASS',result);
}finally{await s.close();}
