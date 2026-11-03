import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';process.env.LINE_RIDER_RELEASE_TEST='1';
const root='C:/Users/Carter/code/Scratch/Line Rider',s=new EditorSession(),before=process.argv.includes('--before'),wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
 await s.openFile(root+'/dist/Line Rider.sb3');const extracted=await s.extract();await s.call('green_flag');await wait(400);await s.call('stop_button');const page=s.requirePage();
 await page.screenshot({path:root+'/artifacts/prompt-history-'+(before?'before':'after')+'.png'});
 if(process.argv.includes('--usernames')){await page.click('[aria-label="Prompt history"]');await wait(300);await page.screenshot({path:root+'/artifacts/prompt-usernames-'+(before?'before':'after')+'.png',clip:{x:310,y:95,width:475,height:750}});}
 if(!before){
  const expected=JSON.parse(await fs.readFile(root+'/docs/prompt-history.json','utf8'));
  const project=await s.call('get_project_json'),sprite=project.targets.find(t=>t.name==='Prompt history');assert.ok(sprite);assert.equal(sprite.visible,false);assert.equal(Object.keys(sprite.comments).length,expected.prompts.length+1);
  for(const prompt of expected.prompts){assert.equal(sprite.comments['prompt-'+String(prompt.number).padStart(2,'0')].text,'Prompt '+String(prompt.number).padStart(2,'0')+'\n\n'+prompt.text);}
  const targets=await page.$$eval('[class*="sprite-selector-item"]',els=>els.filter(e=>e.textContent.trim()==='Prompt history').map(e=>({cls:e.className,role:e.getAttribute('role'),label:e.getAttribute('aria-label')})));
  console.log('Sprite selector',targets);
  const candidates=await page.$$('[class*="sprite-selector-item"]');
  for(const candidate of candidates){const info=await candidate.evaluate(e=>({text:e.textContent.trim(),cls:e.className}));if(info.text==='Prompt history'&&info.cls.includes('sprite-selector-item_sprite-selector-item')){await candidate.click();break;}}
  await wait(500);await page.screenshot({path:root+'/artifacts/prompt-history-comments.png'});
  console.log('PASS all '+expected.prompts.length+' redacted prompts survive native Scratch load, in a hidden sprite');
 }
}finally{await s.close();}
