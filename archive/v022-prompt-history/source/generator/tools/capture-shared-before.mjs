import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';const root='C:/Users/Carter/code/Scratch/Line Rider',s=new EditorSession(),wait=ms=>new Promise(r=>setTimeout(r,ms));
async function shot(name){await wait(150);const r=await s.capture();await fs.writeFile(root+'/artifacts/'+name+'.png',Buffer.from(r.image_base64,'base64'));}
try{await s.openFile(root+'/artifacts/shared-before-update.sb3');await s.extract();await s.call('green_flag');await wait(400);await s.clickStage(-208,160);await shot('mobile-before');await s.clickStage(210,-100);await s.clickStage(185,160);await shot('fullscreen-before');}finally{await s.close();}
