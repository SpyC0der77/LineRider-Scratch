import {EditorSession} from './editor-session.mjs';import fs from 'node:fs/promises';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';const root='C:/Users/Carter/code/Scratch/Line Rider';const s=new EditorSession();const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{await s.openFile(root+'/dist/Line Rider.sb3');const project=await s.extract();await s.call('green_flag');await s.call('set_variable_values',{values:{'Capture hold':1}});for(let i=0;i<150;i++){if(+(await s.call('get_variable_list_data')).variables['Capture ready']===1)break;await wait(20);}const image=await s.capture();await fs.writeFile(root+'/artifacts/long-course-after.png',Buffer.from(image.image_base64,'base64'));const state=await s.call('get_variable_list_data');console.log(JSON.stringify({blocks:project.total_block_count,mode:state.variables.Editing,frame:state.variables.Frame,lines:state.lists.LX.length,zoom:state.variables.Zoom,savedSlot:state.variables['Saved exists']}));}finally{await s.close();}


