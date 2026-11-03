import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {parse,encode,decode} from './dist/converter.mjs';
const context={};vm.createContext(context);vm.runInContext(fs.readFileSync(new URL('./dist/lz-string.js',import.meta.url),'utf8'),context);
const fixture={version:'6.2',startPosition:{x:0,y:0},lines:[{type:0,x1:-100,y1:28,x2:0,y2:28},{type:0,x1:0,y1:28,x2:100,y2:55},{type:2,x1:120,y1:80,x2:20,y2:90}]};
const track=parse(JSON.stringify(fixture));assert.equal(track.goal,0);assert.equal(track.lines[2][4],3);const code=encode(track);assert.deepEqual(decode(code).lines,track.lines);assert.deepEqual(decode(code).flags,track.flags);
assert.equal(encode(parse(code.toLowerCase().match(/.{1,15}/g).join('-\n'))),code);
for(const raw of [code.slice(0,-1),code+'0','LR1bad',JSON.stringify({...fixture,lines:[{type:0,x1:0,y1:0,x2:0,y2:0}]})])assert.throws(()=>parse(raw));
const lossy={...fixture,lines:[{type:1,x1:10,y1:10,x2:0,y2:0}]};assert.throws(()=>parse(JSON.stringify(lossy)),/compatibility/);assert.equal(parse(JSON.stringify(lossy),{allowLossy:true}).warnings.length,1);
const arrays=fixture.lines.map((l,i)=>[l.type,i,l.x1,l.y1,l.x2,l.y2]);for(const field of ['linesArray','linesArrayCompressed']){const value=field==='linesArray'?JSON.stringify(arrays):context.LZString.compressToBase64(JSON.stringify(arrays));assert.deepEqual(parse(JSON.stringify({startPosition:{x:0,y:0},[field]:value}),{decompress:context.LZString.decompressFromBase64}).lines,track.lines);}
const max={lines:Array.from({length:3000},(_,i)=>[i,28,i+1,28,i%4]),goal:1,flags:[0,0,3000,28]};assert.deepEqual(decode(encode(max)).lines,max.lines);assert.throws(()=>encode({...max,lines:[...max.lines,max.lines[0]]}));
fs.writeFileSync(new URL('./fixture.track.json',import.meta.url),JSON.stringify(fixture,null,2));fs.writeFileSync(new URL('../artifacts/converter-test-code.txt',import.meta.url),code);console.log('PASS JSON, compressed arrays, LR1 round trip, checksum, invalid geometry, compatibility consent and 3,000-segment limit');

assert.equal(parse(JSON.stringify({...fixture,lines:[{type:1,x1:0,y1:0,x2:10,y2:0}]})).lines[0][4],4);assert.equal(parse(JSON.stringify(lossy),{allowLossy:true}).lines[0][4],5);for(const m of [4,5])assert.equal(decode(encode({lines:[[0,28,100,28,m]],flags:[0,0,0,0],goal:0})).lines[0][4],m);
