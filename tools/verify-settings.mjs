import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const session = new EditorSession();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const state = () => session.call('get_variable_list_data');
const value = async name => Number((await state()).variables[name]);
const segments = async () => (await state()).lists.LX.items.length;
const distinctLines = async () => new Set((await state()).lists.LY.items.map(y => Number(y).toFixed(1))).size;

async function until(label, check) {
    const deadline = Date.now() + 30_000;
    while (Date.now() < deadline) {
        if (await check()) return;
        await wait(30);
    }
    throw Error('Timed out waiting for ' + label);
}

// Screen coordinates as used by the header and dropdown rows (y downward from the top of the stage).
const click = (x, y) => session.clickStage(x - 240, 180 - y);
const key = k => session.pressKeys([{key: k, hold_duration_ms: 60, time_after_last_key_press_ms: 60}]);
const setValues = values => session.call('set_variable_values', {values});
const ready = () => until('timeline ready', async () =>
    await value('Timeline ready') === 1 && await value('Timeline loading') === 0);

// Dropdown row centres for the Settings menu (header Settings at screen x 246).
const SETTINGS_HEADER = [246, 20];
const ROWS = {smooth: 55, sweep: 81, large: 107};
const SETTING_VARIABLE = {smooth: 'Setting smooth draw', sweep: 'Setting sweep erase', large: 'Setting large eraser'};

async function toggle(row) {
    await click(...SETTINGS_HEADER);
    await until('settings menu open', async () => await value('Menu') === 7);
    const before = await value(SETTING_VARIABLE[row]);
    await click(300, ROWS[row]);
    await until(row + ' toggled', async () => await value(SETTING_VARIABLE[row]) === 1 - before && await value('Menu') === 0);
}

async function newTrack() {
    await click(32, 20);
    await until('track menu', async () => await value('Menu') === 1);
    await click(60, 55);
    await until('new track', async () => await segments() === 0 && await value('Menu') === 0);
    await ready();
}

// Pencil drag with small per-frame jitter (under the 8 px lazy radius) along a horizontal line.
async function drawJitter(y) {
    const points = [];
    for (let i = 0; i < 60; i++) points.push([-150 + 2.5 * i, y + (i % 2 ? 5 : -5)]);
    const from = await segments();
    await session.dragStage(points, 90);
    await wait(150);
    await ready();
    return [from, await segments()];
}

// Mean change of orientation between consecutive stroke segments (orientation is modulo 180 degrees).
async function meanTurn(from, to) {
    const v = await state();
    const dx = v.lists.DX.items.slice(from, to).map(Number);
    const dy = v.lists.DY.items.slice(from, to).map(Number);
    let total = 0, count = 0, previous = null;
    for (let i = 0; i < dx.length; i++) {
        if (Math.hypot(dx[i], dy[i]) < 0.05) continue;
        const angle = Math.atan2(dy[i], dx[i]);
        if (previous !== null) {
            let turn = angle - previous;
            while (turn > Math.PI / 2) turn -= Math.PI;
            while (turn < -Math.PI / 2) turn += Math.PI;
            total += Math.abs(turn);
            count++;
        }
        previous = angle;
    }
    return {mean: total / count, count};
}

async function verifyMenu() {
    await ready();
    const undo = (await state()).lists['Undo Count'].items.length;
    const dirty = await value('Dirty');
    for (const row of ['smooth', 'sweep', 'large']) {
        const start = await value(SETTING_VARIABLE[row]);
        await toggle(row);
        assert.equal(await value(SETTING_VARIABLE[row]), 1 - start);
        await toggle(row);
        assert.equal(await value(SETTING_VARIABLE[row]), start);
    }
    assert.equal((await state()).lists['Undo Count'].items.length, undo, 'Settings must not add undo entries');
    assert.equal(await value('Dirty'), dirty, 'Settings must not set the Dirty flag');
    console.log('PASS Settings menu opens from the header and each toggle flips its variable');
}

async function verifyModes() {
    await setValues({'Setting smooth draw': 0, 'Setting sweep erase': 0, 'Setting large eraser': 1});
    await click(425, 20);
    await until('play mode', async () => await value('Editing') === 0);
    assert.equal(await value('Setting smooth draw'), 0);
    assert.equal(await value('Setting sweep erase'), 0);
    assert.equal(await value('Setting large eraser'), 1);
    await toggle('smooth');
    assert.equal(await value('Setting smooth draw'), 1, 'Settings toggle from Play mode');
    await click(331, 20);
    await until('edit mode', async () => await value('Editing') === 1);
    assert.equal(await value('Setting smooth draw'), 1);
    assert.equal(await value('Setting sweep erase'), 0);
    assert.equal(await value('Setting large eraser'), 1);
    await session.call('green_flag');
    await until('restart', async () => await value('Editing') === 1);
    await wait(200);
    assert.equal(await value('Setting smooth draw'), 1, 'Green flag must keep settings');
    assert.equal(await value('Setting sweep erase'), 0, 'Green flag must keep settings');
    assert.equal(await value('Setting large eraser'), 1, 'Green flag must keep settings');
    console.log('PASS settings survive Edit/Play switches, a toggle in Play, and the green flag');
    await setValues({'Setting smooth draw': 1, 'Setting sweep erase': 1, 'Setting large eraser': 0});
    await ready();
}

async function verifySmoothing() {
    await newTrack();
    await key('1');
    await setValues({'Setting smooth draw': 0});
    const [offFrom, offTo] = await drawJitter(-80);
    const off = await meanTurn(offFrom, offTo);
    await setValues({'Setting smooth draw': 1});
    const [onFrom, onTo] = await drawJitter(40);
    const on = await meanTurn(onFrom, onTo);
    console.log(`  mean turn: smoothing off ${off.mean.toFixed(3)} rad (${off.count} joints), on ${on.mean.toFixed(3)} rad (${on.count} joints)`);
    assert.ok(off.count > 20 && on.count > 20, 'Both strokes should contain segments');
    assert.ok(on.mean < off.mean * 0.5, 'Smoothing should remove most of the jitter turns');
    console.log('PASS smoothing produces a far straighter stroke from the same jittery pointer path');
}

async function drawLines(ys) {
    await key('1');
    await until('pencil tool', async () => await value('Tool') === 0);
    await setValues({'Setting smooth draw': 0});
    for (const y of ys) {
        await session.dragStage([[-120, y], [120, y]], 90);
        await wait(100);
        await ready();
    }
    await setValues({'Setting smooth draw': 1});
}

// Segments still covering the world x of the vertical swipe (stage x 0 is the camera centre).
async function crossings() {
    const v = await state();
    const cx = Number(v.variables['Camera X']);
    let count = 0;
    for (let i = 0; i < v.lists.LX.items.length; i++) {
        const a = Number(v.lists.LX.items[i]), b = a + Number(v.lists.DX.items[i]);
        if (Math.min(a, b) - 2 <= cx && cx <= Math.max(a, b) + 2) count++;
    }
    return count;
}

async function verifySweep() {
    await newTrack();
    await drawLines([-20, -50, -80, -110]);
    assert.equal(await distinctLines(), 4, 'Four parallel lines should be drawn');
    await key('3');
    await until('eraser tool', async () => await value('Tool') === 2);

    await setValues({'Setting sweep erase': 0});
    await session.dragStage([[0, -10], [0, -124]], 90);
    await wait(150);
    await ready();
    const withoutSweep = await crossings();

    await setValues({'Setting sweep erase': 1});
    await session.dragStage([[0, -10], [0, -124]], 90);
    await wait(150);
    await ready();
    const withSweep = await crossings();
    console.log(`  remaining segments at the swipe: sweep off ${withoutSweep}, sweep on ${withSweep}`);
    assert.ok(withoutSweep >= 4, 'A single pointer step without sweeping should not reach the lines');
    assert.equal(withSweep, 0, 'Continuous erasing should remove every crossed line');
    console.log('PASS continuous erasing removes every crossed line from one fast swipe; the single-point eraser removes none');
}

async function verifyLargeEraser() {
    await newTrack();
    await drawLines([-60]);
    assert.equal(await distinctLines(), 1, 'The test line should be drawn');
    await key('3');
    await until('eraser tool', async () => await value('Tool') === 2);
    await setValues({'Setting sweep erase': 1, 'Setting large eraser': 0});
    await session.dragStage([[-150, -46], [150, -46]], 90);
    await wait(150);
    await ready();
    assert.equal(await distinctLines(), 1, 'The 9 px eraser should miss a line 14 px away');

    await setValues({'Setting large eraser': 1});
    await session.dragStage([[-150, -46], [150, -46]], 90);
    await wait(150);
    await ready();
    assert.equal(await distinctLines(), 0, 'The 18 px eraser should remove a line 14 px away');
    console.log('PASS large eraser removes a line 14 px away that the normal eraser misses');
    await setValues({'Setting large eraser': 0});
}

try {
    await session.openFile(resolve('dist/Line Rider.sb3'));
    await session.call('green_flag');
    await until('startup', async () => await value('Editing') === 1);
    await ready();
    await key('a');
    await verifyMenu();
    await verifyModes();
    await verifySmoothing();
    await verifySweep();
    await verifyLargeEraser();
    await setValues({'Setting smooth draw': 1, 'Setting sweep erase': 1, 'Setting large eraser': 0});
    console.log('PASS settings verification complete');
} finally {
    await session.close();
}
