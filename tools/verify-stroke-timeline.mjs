import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const session = new EditorSession();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const read = item_name => session.call('get_variable_list_data', {item_name});
const value = async name => Number((await read(name)).variables[name]);
const segments = async () => (await read('LX')).lists.LX.length;

async function until(label, check) {
    const deadline = Date.now() + 30_000;
    while (Date.now() < deadline) {
        if (await check()) return;
        await wait(30);
    }
    throw Error('Timed out waiting for ' + label);
}

async function move(x, y) {
    const point = await session.stagePoint(x, y);
    await session.requirePage().mouse.move(point.x, point.y);
}

const ready = async () => await value('Timeline ready') === 1 && await value('Timeline loading') === 0;

async function verifyStroke() {
    await session.call('green_flag');
    await until('initial timeline', ready);
    const end = await value('Timeline end');
    const page = session.requirePage();
    await session.call('set_variable_values', {values: {Brush: 3}});
    const frame = Math.round(114 * end / 294);
    await session.clickStage(-112, -142);
    await until('selected frame', async () => await value('Frame') === frame);

    const startingSegments = await segments();
    await move(-150, -18);
    await page.mouse.down();
    await until('pencil held down', async () => await value('Drawing') === 1);
    for (const [x, y] of [[-118, -31], [-85, -46], [-55, -65], [-24, -89]]) {
        const previous = await segments();
        await move(x, y);
        await until('visible pencil segments', async () => await segments() > previous);
        await wait(110);
        assert.equal(await value('Drawing'), 1);
        assert.equal(await value('Grid ready'), 0, 'Collision grid must stay dirty until release');
        assert.equal(await value('Physics Frame'), end, 'Solver ran during the stroke');
        assert.equal(await value('Timeline end'), end);
        assert.equal(await value('Timeline ready'), 1);
        assert.equal(await value('Timeline loading'), 0);
        assert.equal(await value('Frame'), frame);
    }
    await page.mouse.up();
    await until('release shows loading', async () =>
        await value('Drawing') === 0 && await value('Timeline loading') === 1);
    await until('released stroke starts one new calculation', async () =>
        await value('Timeline ready') === 0 && await value('Physics Frame') < end);
    assert.equal(await value('Grid ready'), 1);
    await until('stroke timeline finishes', ready);
    assert.equal(await value('Timeline end'), end, 'Scenery keeps the original finish');
    assert.equal(await value('Frame'), frame);
    assert.ok(await segments() > startingSegments);

    const finalSegments = await segments();
    await session.clickStage(-220, 85);
    assert.equal(await segments(), finalSegments);
    assert.equal(await value('Timeline loading'), 0, 'A pencil tap with no line must not rebuild');
    assert.equal(await value('Grid ready'), 1);
}

try {
    await session.openFile(resolve('dist/Line Rider.sb3'));
    await verifyStroke();
    console.log('PASS live pencil, deferred rebuild, loading, retained frame, and no-op tap');
} finally {
    await session.close();
}
