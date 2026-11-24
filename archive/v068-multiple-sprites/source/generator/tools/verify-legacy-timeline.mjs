import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const session = new EditorSession();
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const click = (x, y) => session.clickStage(x - 240, 180 - y);
const read = item_name => session.call('get_variable_list_data', {item_name});
const key = name => session.pressKeys([{key: name, hold_duration_ms: 80, time_after_last_key_press_ms: 80}]);
const scalar = async name => Number((await read(name)).variables[name]);
const list = async name => (await read(name)).lists[name].items;

async function until(label, predicate) {
    const deadline = Date.now() + 30_000;
    while (Date.now() < deadline) {
        if (await predicate()) return;
        await delay(80);
    }
    throw Error('Timed out waiting for ' + label);
}

async function seek(frame, end) {
    const x = Math.round(-226 + 294 * frame / end);
    await session.clickStage(x, -142);
    const actualFrame = Math.round((x + 226) * end / 294);
    await until('scrubbed frame', async () => await scalar('Frame') === actualFrame);
    return actualFrame;
}

const ready = async () => await scalar('Timeline ready') === 1 && await scalar('Timeline current pose') === 1;

function observeOriginal(page) {
    return page.evaluate(async () => {
        const read = name => window.__scratchOptimizer.call('get_variable_list_data', {item_name: name});
        const variable = async name => +((await read(name)).variables[name]);
        const frames = [];
        const deadline = performance.now() + 30_000;
        while (performance.now() < deadline) {
            const frame = await variable('Frame');
            const state = await variable('State');
            const mounted = await variable('Mounted');
            if (mounted === 1 && frame !== frames.at(-1)?.frame) {
                const x = (await read('X')).lists.X.items;
                const y = (await read('Y')).lists.Y.items;
                frames.push({frame, x, y});
            }
            if (state === 3 || state === 4) return {frames, state, frame};
            await new Promise(requestAnimationFrame);
        }
        throw Error('Original ride did not reach a result');
    });
}

try {
    await session.openFile(resolve('[AI] Line Rider.sb3'));
    await session.call('green_flag');
    await until('original renderer', async () => await scalar('Canvas bottom') === -153);
    const course = await list('LX');
    const recorded = observeOriginal(session.requirePage());
    await click(315, 56);
    const original = await recorded;
    assert.equal(original.state, 4);
    assert.ok(original.frames.length > 0.95 * original.frame);

    await session.loadCurrentFile(resolve('dist/[AI] Line Rider - Timeline.sb3'));
    await session.call('green_flag');
    await until('full timeline', ready);
    assert.deepEqual(await list('LX'), course);
    const end = await scalar('Timeline end');
    assert.equal(end, original.frame);
    assert.equal(+(await list('Timeline Ride result')).at(-1), 4);
    const points = (await list('Initial X')).length;
    const x = await list('Timeline X');
    const y = await list('Timeline Y');
    for (const pose of original.frames) {
        const offset = pose.frame * points;
        assert.deepEqual(x.slice(offset, offset + points), pose.x, 'X at frame ' + pose.frame);
        assert.deepEqual(y.slice(offset, offset + points), pose.y, 'Y at frame ' + pose.frame);
    }
    console.log('PASS original mounted physics at', original.frames.length, 'observed frames, including finish', end);

    const selected = await seek(90, end);
    assert.equal(await scalar('Editing'), 1);
    assert.equal(await scalar('Playing'), 0);
    assert.deepEqual(await list('X'), x.slice(selected * points, (selected + 1) * points));
    await click(425, 20);
    await until('paused Play', async () => await scalar('Editing') === 0);
    await key('n');
    await until('one cached step', async () => await scalar('Frame') === selected + 1);
    await click(331, 20);
    await until('return to Edit', async () => await scalar('Editing') === 1);
    assert.equal(await scalar('Frame'), selected + 1);

    await key('f');
    await key('6');
    const zoom = await scalar('Zoom');
    const goalX = x[40 * points + 4];
    const goalY = y[40 * points + 4];
    await session.clickStage((goalX - await scalar('Camera X')) * zoom, -20 - (goalY - await scalar('Camera Y')) * zoom);
    await until('earlier goal', async () => await ready() && await scalar('Timeline end') < selected);
    const earlyEnd = await scalar('Timeline end');
    assert.equal(await scalar('State'), 4);
    assert.equal(await scalar('Frame'), earlyEnd);
    await key('z');
    await until('restored frame and goal', async () => await ready() &&
        await scalar('Timeline end') === end && await scalar('Frame') === selected + 1);
    assert.deepEqual(await list('X'), x.slice((selected + 1) * points, (selected + 2) * points));
    console.log('PASS the earlier goal clamps the playhead to frame', earlyEnd, 'and Undo restores the selected time');

    await key('h');
    await key('5');
    const spawnX = await scalar('Spawn X');
    const spawnY = await scalar('Spawn Y');
    const homeZoom = await scalar('Zoom');
    await session.clickStage(
        (spawnX + 12 - await scalar('Camera X')) * homeZoom,
        -20 - (spawnY + 3 - await scalar('Camera Y')) * homeZoom,
    );
    await until('moved start', async () => await scalar('Spawn X') !== spawnX && await ready());
    assert.equal(await scalar('Frame'), selected + 1);
    assert.notDeepEqual(await list('X'), x.slice((selected + 1) * points, (selected + 2) * points));
    await key('z');
    await until('restored start', async () => await ready() && await scalar('Spawn X') === spawnX);
    console.log('PASS moving the start updates the rider while retaining the frame');

    await click(425, 20);
    await until('Play preview', async () => await scalar('Editing') === 0);
    await key('x');
    await until('terminal crash', async () => await ready() && await scalar('State') === 3);
    assert.equal(await scalar('Timeline end'), selected + 2);
    assert.equal(await scalar('Frame'), selected + 2);
    assert.equal(await scalar('Playing'), 0);
    assert.equal(+(await list('Timeline Mounted')).at(-1), 0);
    const crash = await scalar('Frame');
    await key('n');
    assert.equal(await scalar('Frame'), crash);
    await seek(0, crash);
    assert.equal(await scalar('State'), 2);
    console.log('PASS the crash is the final frame and can be scrubbed backward');
} finally {
    await session.close();
}
