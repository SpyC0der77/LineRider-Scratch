import {EditorSession} from './editor-session.mjs';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {resolve} from 'node:path';

// Usage: node tools/capture-settings.mjs before|after
// Captures the editor at startup, the Help dropdown and (after) the Settings dropdown.
process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
const phase = process.argv[2] ?? 'after';
const root = 'C:/Users/Carter/code/Scratch/Line Rider';
const s = new EditorSession();
const wait = ms => new Promise(r => setTimeout(r, ms));
const state = () => s.call('get_variable_list_data');
const value = async name => Number((await state()).variables[name]);

async function until(label, check) {
    const deadline = Date.now() + 20000;
    while (Date.now() < deadline) {
        if (await check()) return;
        await wait(30);
    }
    throw new Error('Timed out ' + label);
}

async function release() {
    await s.call('set_variable_values', {values: {'Capture hold': 0}});
    await until('capture release', async () => await value('Capture ready') === 0);
}

async function capture(name) {
    await s.call('set_variable_values', {values: {'Capture hold': 1}});
    await until('capture ready', async () => await value('Capture ready') === 1);
    const r = await s.capture();
    await fs.writeFile(root + '/artifacts/' + name + '.png', Buffer.from(r.image_base64, 'base64'));
    await release();
    console.log('captured', name);
}

try {
    await s.openFile(resolve('dist/testing/Line Rider.sb3'));
    await s.call('green_flag');
    await until('timeline ready', async () => await value('Timeline ready') === 1 && await value('Timeline loading') === 0);
    await wait(400);
    await capture(`settings-${phase}-editor`);
    // Header buttons sit at y 7-33 (stage x = screen x - 240, stage y = 180 - screen y).
    await s.clickStage(188 - 240, 180 - 20);
    await until('help menu open', async () => await value('Menu') === 4);
    await wait(200);
    await capture(`settings-${phase}-menu`);
    if (phase === 'after') {
        // Clicking another header switches dropdowns; Settings is centred at screen x 246.
        await s.clickStage(246 - 240, 180 - 20);
        await until('settings menu open', async () => await value('Menu') === 7);
        await wait(200);
        await capture(`settings-${phase}-open`);
    }
    console.log('PASS captured settings screens');
} finally {
    await s.close();
}
