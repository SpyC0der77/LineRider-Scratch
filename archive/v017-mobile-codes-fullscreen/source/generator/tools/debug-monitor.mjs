import {EditorSession} from './editor-session.mjs';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
process.env.SCRATCH_OPTIMIZER_HEADLESS='1';
const root='C:/Users/Carter/code/Scratch/Line Rider', s=new EditorSession();
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
 await s.openFile(root+'/dist/Line Rider.sb3');await s.extract();s.requirePage().on('pageerror',e=>console.log('PAGE ERROR',e.message));s.requirePage().on('console',e=>{if(e.type()==='error')console.log('CONSOLE ERROR',e.text())});await s.call('green_flag');await wait(600);const v=await saveCode();await wait(1000);console.log('MONITORS',(await s.call('get_project_json')).monitors);console.log('MONITOR DOM',await s.requirePage().evaluate(()=>Array.from(document.querySelectorAll('[class*=monitor]')).map(e=>({cls:e.getAttribute('class'),text:e.textContent.slice(0,70)}))));console.log('TRACK VALUE',v.lists['Track code'].items.map(x=>x.length));await snap('monitor-debug',true);
}finally{await s.close();}
