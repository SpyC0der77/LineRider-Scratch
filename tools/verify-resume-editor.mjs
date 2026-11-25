import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const session = new EditorSession();
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const read = item_name => session.call('get_variable_list_data', {item_name});
const scalar = async name => Number((await read(name)).variables[name]);
const list = async name => (await read(name)).lists[name].items;
const key = name => session.pressKeys([{key: name, hold_duration_ms: 80, time_after_last_key_press_ms: 80}]);
const page = () => session.requirePage();

async function until(label, predicate, timeout = 30_000) {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
        if (await predicate()) return;
        await delay(60);
    }
    throw Error('Timed out waiting for ' + label);
}

async function seek(frame, end) {
    const x = Math.round(-226 + 294 * frame / end);
    await session.clickStage(x, -142);
    const actual = Math.round((x + 226) * end / 294);
    await until('scrubbed frame', async () => await scalar('Frame') === actual);
    return actual;
}

// Ready means the edit has been accepted and the timeline is complete. The update
// procedure recounts the track lines, so a stale count after an edit reads as unsettled.
const settled = async () => await scalar('Timeline ready') === 1 && await scalar('Timeline loading') === 0
    && await scalar('Drawing') === 0 && await scalar('Grid ready') === 1
    && await scalar('Timeline expected lines') === (await list('LX')).length;

const camera = async () => ({x: await scalar('Camera X'), y: await scalar('Camera Y'), zoom: await scalar('Zoom')});
const toStage = (cam, wx, wy) => ({x: (wx - cam.x) * cam.zoom, y: -20 - (wy - cam.y) * cam.zoom});

async function pencil(stagePoints) {
    const mouse = page().mouse;
    const first = await session.stagePoint(stagePoints[0].x, stagePoints[0].y);
    await mouse.move(first.x, first.y);
    await mouse.down();
    await until('pencil held', async () => await scalar('Drawing') === 1);
    for (const p of stagePoints.slice(1)) {
        const at = await session.stagePoint(p.x, p.y);
        await mouse.move(at.x, at.y);
        await delay(110);
    }
    await mouse.up();
    await until('pencil released', async () => await scalar('Drawing') === 0);
}

async function eraseAt(p) {
    const mouse = page().mouse;
    const at = await session.stagePoint(p.x, p.y);
    await mouse.move(at.x, at.y);
    await mouse.down();
    await until('eraser held', async () => await scalar('Drawing') === 1);
    await delay(250);
    await mouse.up();
    await until('eraser released', async () => await scalar('Drawing') === 0);
}

// Full recalculation: Timeline dirty all and Timeline restart are plain Stage scalars,
// so they can be set directly. Resume 0 proves the solver restarted from frame 0.
async function forceFullRecalc() {
    await session.call('set_variable_values', {values: {'Timeline dirty all': 1, 'Timeline restart': 1}});
    await until('full recalculation', async () => await scalar('Timeline resume') === 0 && await settled());
}

const FIELDS = ['Timeline X', 'Timeline Y', 'Timeline PX', 'Timeline PY',
    'Timeline Ride result', 'LX', 'LY', 'DX', 'DY'];
async function snapshot() {
    const out = {end: await scalar('Timeline end')};
    for (const field of FIELDS) out[field] = await list(field);
    return out;
}
function assertSameSnapshot(actual, expected, label) {
    assert.equal(actual.end, expected.end, label + ' Timeline end');
    for (const field of FIELDS) assert.deepEqual(actual[field], expected[field], label + ' ' + field);
}

function segmentDistance(px, py, sx, sy, ex, ey) {
    const dx = ex - sx, dy = ey - sy;
    const t = Math.min(1, Math.max(0, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)));
    return Math.hypot(px - sx - dx * t, py - sy - dy * t);
}

async function verifyResume() {
    await session.call('green_flag');
    await until('full timeline', async () => await settled() && await scalar('Timeline end') === 348);
    const end = await scalar('Timeline end');
    assert.equal(end, 348);
    assert.equal(await scalar('Timeline resume'), 0, 'A green-flag start is a full calculation');
    const points = (await list('Initial X')).length;
    console.log('PASS full timeline through finish at frame', end);

    // Step 2: pencil stroke just under the rider at frame 250.
    const frame = await seek(250, end);
    assert.equal(await scalar('Editing'), 1);
    await key('1');
    assert.equal(await scalar('Tool'), 0, 'Pencil tool');
    assert.equal(await scalar('Brush'), 0, 'Normal material collides with the rider');
    let cam = await camera();
    const tx = await list('Timeline X'), ty = await list('Timeline Y');
    // World Y grows downward on screen (stage y = -20 - (y - camY) * zoom), so the lowest point has the largest Y.
    let low = null;
    for (let k = 0; k < points; k++) {
        const y = Number(ty[frame * points + k]);
        if (!low || y > low.y) low = {x: Number(tx[frame * points + k]), y};
    }
    const beforeStroke = (await list('LX')).length;
    await pencil([toStage(cam, low.x - 40, low.y + 6), toStage(cam, low.x + 40, low.y + 6)]);
    await until('stroke applied at frame 250', async () =>
        (await list('LX')).length > beforeStroke && await settled());
    const resume250 = await scalar('Timeline resume');
    const end250 = await scalar('Timeline end');
    assert.ok(resume250 > 150, `Timeline resume ${resume250} should keep frames before 150`);
    assert.ok(resume250 <= frame + 5, `Timeline resume ${resume250} should not exceed frame ${frame} + 5`);
    assert.equal(await scalar('Timeline ready'), 1);
    assert.equal(await scalar('Timeline loading'), 0);
    assert.equal((await list('Timeline Ride result')).length, end250 + 1, 'Ride result covers the timeline');
    assert.equal((await list('Timeline X')).length, (end250 + 1) * points, 'Pose cache covers the timeline');
    const incremental250 = await snapshot();
    console.log(`PASS pencil at frame ${frame} kept frames before ${resume250}, timeline end ${end250}`);

    // Step 3: a full recalculation of the same track must match the incremental result.
    await forceFullRecalc();
    assert.equal(await scalar('Timeline resume'), 0);
    assertSameSnapshot(await snapshot(), incremental250, 'full-vs-incremental (pencil)');
    console.log('PASS full recalculation after the pencil edit matches the incremental lists');

    // Step 4: eraser over the track segment nearest the rider at frame 120.
    const frame120 = await seek(120, await scalar('Timeline end'));
    cam = await camera();
    const lx = await list('LX'), ly = await list('LY'), dx = await list('DX'), dy = await list('DY');
    const rx = await list('Timeline X'), ry = await list('Timeline Y');
    let target = {d: Infinity};
    for (let k = 0; k < points; k++) {
        const px = Number(rx[frame120 * points + k]), py = Number(ry[frame120 * points + k]);
        for (let h = 0; h < lx.length; h++) {
            const sx = Number(lx[h]), sy = Number(ly[h]);
            const d = segmentDistance(px, py, sx, sy, sx + Number(dx[h]), sy + Number(dy[h]));
            if (d < target.d) target = {d, mx: sx + Number(dx[h]) / 2, my: sy + Number(dy[h]) / 2, h};
        }
    }
    await key('3');
    assert.equal(await scalar('Tool'), 2, 'Eraser tool');
    const beforeErase = (await list('LX')).length;
    await eraseAt(toStage(cam, target.mx, target.my));
    await until('segment erased', async () => (await list('LX')).length < beforeErase && await settled());
    const resume120 = await scalar('Timeline resume');
    assert.ok(resume120 > 0, 'Erase must not force a full calculation');
    assert.ok(resume120 <= 125 + 5, `Timeline resume ${resume120} should be near frame 120`);
    const incremental120 = await snapshot();
    console.log(`PASS eraser at frame ${frame120} (nearest segment ${target.h}, distance ${target.d.toFixed(2)}) kept frames before ${resume120}`);

    await forceFullRecalc();
    assertSameSnapshot(await snapshot(), incremental120, 'full-vs-incremental (eraser)');
    console.log('PASS full recalculation after the eraser edit matches the incremental lists');

    // Step 5: a stroke far from the ride keeps every frame.
    await key('1');
    await key('f');
    await until('track fitted', async () => await settled());
    const prevEnd = await scalar('Timeline end');
    const beforeFar = await snapshot();
    cam = await camera();
    const rideX = await list('Timeline X'), rideY = await list('Timeline Y');
    let far = null;
    // The editor only accepts pointer Y below stage y 100, so the stroke stays in the upper canvas.
    search: for (const sy of [80, 70, 60, 50]) {
        for (let sx = -200; sx <= 160; sx += 20) {
            const a = {x: cam.x + sx / cam.zoom, y: cam.y + (-20 - sy) / cam.zoom};
            const b = {x: cam.x + (sx + 40) / cam.zoom, y: a.y};
            let clearance = Infinity;
            for (let i = 0; i < rideX.length; i++) {
                clearance = Math.min(clearance, segmentDistance(Number(rideX[i]), Number(rideY[i]), a.x, a.y, b.x, b.y));
            }
            if (clearance > 60) {
                far = {sx, sy};
                break search;
            }
        }
    }
    assert.ok(far, 'No on-screen stroke position was clear of the ride');
    const beforeFarCount = (await list('LX')).length;
    const t0 = Date.now();
    await pencil([{x: far.sx, y: far.sy}, {x: far.sx + 40, y: far.sy}]);
    await until('far stroke applied', async () => (await list('LX')).length > beforeFarCount && await settled(), 5000);
    const elapsed = Date.now() - t0;
    assert.equal(await scalar('Timeline resume'), prevEnd + 1, 'Every frame kept');
    assert.equal(await scalar('Timeline end'), prevEnd);
    assert.ok(elapsed < 2000, `Far stroke took ${elapsed} ms to become ready`);
    const afterFar = await snapshot();
    for (const field of FIELDS.slice(0, 5)) assert.deepEqual(afterFar[field], beforeFar[field], 'far stroke ' + field);
    assert.equal(afterFar.end, beforeFar.end, 'far stroke Timeline end');
    console.log(`PASS far stroke kept every frame (resume ${prevEnd + 1}) and was ready after ${elapsed} ms`);
}

try {
    await session.openFile(resolve('dist/Line Rider.sb3'));
    await verifyResume();
    console.log('PASS resume editor checks complete');
} finally {
    await session.close();
}
