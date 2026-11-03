import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';const root='C:/Users/Carter/code/Scratch/Line Rider',s=new EditorSession();
const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{await s.openFile(root+'/dist/Line Rider.sb3');await s.extract();await s.call('green_flag');await wait(500);await s.clickStage(185,160);await wait(350);for(let i=0;i<300;i++){const v=await s.call('get_variable_list_data');if(+v.variables['Capture ready']===1)break;await s.call('set_variable_values',{values:{'Capture hold':1}});await wait(20);}const r=await s.capture();await fs.writeFile(root+'/artifacts/fullscreen-before.png',Buffer.from(r.image_base64,'base64'));}finally{await s.close();}
