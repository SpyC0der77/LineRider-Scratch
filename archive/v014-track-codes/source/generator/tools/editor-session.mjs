/** Purpose-built pointer adapter for the optimizer-owned isolated editor. */
import {ScratchSession} from 'file:///C:/Users/Carter/Code/Scratch/Scratch%20AI%20Integrations/project-optimizer/dist/session.js';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
export class EditorSession extends ScratchSession {
 async dragStage(points,hold=90) {
  const page=this.requirePage();
  for (let i=0;i<points.length;i++) {
   const point=await this.stagePoint(points[i][0],points[i][1]);
   await page.mouse.move(point.x,point.y);
   if(i===0)await page.mouse.down();
   await wait(hold);
  }
  await page.mouse.up();await wait(100);
 }
 async clickStage(x,y) {await this.dragStage([[x,y]],100);}
}
