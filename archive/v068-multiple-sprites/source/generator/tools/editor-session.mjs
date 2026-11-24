/** Purpose-built pointer adapter for the optimizer-owned isolated editor. */
import {ScratchSession} from 'file:///C:/Users/Carter/Code/Scratch/Scratch%20AI%20Integrations/project-optimizer/dist/session.js';
import {existsSync} from 'node:fs';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
export class EditorSession extends ScratchSession {
 // Capture gates exist only in the testing build. Set LINE_RIDER_RELEASE_TEST=1
 // to exercise the actual delivered file without instrumentation.
 fixture(path){const normalized=path.replaceAll('\\','/');const test=normalized.replace('/dist/Line Rider.sb3','/dist/testing/Line Rider.sb3');return !process.env.LINE_RIDER_RELEASE_TEST&&test!==normalized&&existsSync(test)?test:path;}
 async openFile(path){return super.openFile(this.fixture(path));}
 async loadCurrentFile(path){return super.loadCurrentFile(this.fixture(path));}
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
 async touchDragStage(points,hold=90){
  const page=this.requirePage();let touch;
  for(let i=0;i<points.length;i++){const p=await this.stagePoint(...points[i]);if(i===0)touch=await page.touchscreen.touchStart(p.x,p.y);else await touch.move(p.x,p.y);await wait(hold);}
  await touch.end();await wait(100);
 }
}
