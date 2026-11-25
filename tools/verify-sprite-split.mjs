import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';process.env.LINE_RIDER_RELEASE_TEST='1';
const root=decodeURIComponent(new URL('..',import.meta.url).pathname).replace(/^\/(?=[A-Za-z]:)/,'').replace(/\/$/,''),s=new EditorSession(),before=process.argv.includes('--before'),wait=ms=>new Promise(r=>setTimeout(r,ms));
const state=()=>s.call('get_variable_list_data');
async function until(c,label){const start=Date.now();while(Date.now()-start<20000){const v=await state();if(c(v))return v;await wait(30);}throw Error('Timeout '+label);}
try{
 await s.openFile(root+'/dist/Line Rider.sb3');await s.extract();await s.call('green_flag');await until(v=>+v.variables.Editing===1&&+v.variables.Zoom===1.8,'startup');await wait(250);
 const project=await s.call('get_project_json');
 const screenshot=await s.capture();await fs.writeFile(root+'/artifacts/sprites-game-'+(before?'before':'after')+'.png',Buffer.from(screenshot.image_base64,'base64'));
 await s.requirePage().screenshot({path:root+'/artifacts/sprites-editor-'+(before?'before':'after')+'.png'});
 if(!before){
  const expected=['Game controller','Physics','Track editor','Menus','Track codes','Renderer','Prompt history'];
  assert.deepEqual(project.targets.filter(t=>!t.isStage).map(t=>t.name),expected);
  for(const target of project.targets){const definitions=new Set(Object.values(target.blocks).filter(b=>b.opcode==='procedures_prototype').map(b=>b.mutation.proccode));for(const block of Object.values(target.blocks))if(block.opcode==='procedures_call')assert.ok(definitions.has(block.mutation.proccode),target.name+' missing local '+block.mutation.proccode);}
 }
 await s.clickStage(315.333333333-240,180-56);await until(v=>+v.variables.Playing===1&&+v.variables.Frame>=10,'run');const first=await state(),start=Date.now();const last=await until(v=>+v.variables.Frame>=70,'benchmark');
 const metrics={sprites:project.targets.filter(t=>!t.isStage).map(t=>({name:t.name,blocks:Object.keys(t.blocks).length})),simulationFramesPerSecond:(+last.variables.Frame- +first.variables.Frame)/((Date.now()-start)/1000)};
 await fs.writeFile(root+'/artifacts/sprites-'+(before?'before':'after')+'-metrics.json',JSON.stringify(metrics,null,2));console.log(JSON.stringify(metrics));
 if(!before)assert.ok(metrics.simulationFramesPerSecond>=24,'Refactor slowed native simulation excessively');
}finally{await s.close();}
