# Sprite guide

| Sprite | Responsibility |
| --- | --- |
| Game controller | The only frame loop, input dispatch, Edit/Play transitions, camera and playback controls. |
| Physics | Sled and rider points, collisions, spatial grid, run results and timeline snapshots. |
| Track editor | Pencil, line, eraser, mobile gap repair, flags, saved slot, undo/redo and track operations. |
| Menus | Dropdown input, toolbar actions, keyboard navigation and mode-change confirmations. |
| Track codes | LR1 encoding, validation, staged import and Scratch's native answer prompt. |
| Renderer | Terrain, rider, controls, text and overlays. Owns the pen layer and all drawing costumes. |
| Prompt history | Hidden documentation sprite containing the sanitized user prompts. |

Stage retains the variables and lists shared by these systems. Its short input scripts queue clicks and keys. The Game controller consumes that queue and waits for each operation to finish before starting another, so temporary variables cannot be overwritten by concurrent subsystem operations.

## Calls and frame order

Custom blocks remain local to their sprite. A call to a procedure in another sprite becomes `broadcast and wait`, with a message named after its destination and procedure, such as `Physics / update timeline`. Each exported procedure has its own receiver. The receiver calls the local implementation.

Each tick handles input and track changes, computes any pending timeline frames in a short batch, then reads the selected pose and updates the camera. The solver retains its own state between batches. A change to track geometry or flags invalidates the cache. The selected frame number survives that rebuild. Playback advances through cached frames. Renderer clears the shared pen layer once, draws the scene and controls, and finishes with overlays. Rendering supplies the redraw boundary.

The solver iterations, collision queries, track serialization loops and drawing operations run inside local custom blocks with "run without screen refresh" enabled. Wrappers that wait for another sprite have that option disabled. The compiler outlines consecutive local operations into warp batches so large loops still finish within one operation. Keeping a message wait inside a warp procedure can stall the receiver; disabling warp on the entire operation can make a large loop take one display frame per iteration.

## Rebuilding and checking

`tools/split_sprites.py` defines ownership in `ROLES`, moves procedures after cleanup, generates request receivers, separates waits from local batches, and arranges scripts into columns. It rejects unassigned procedures, missing local calls, invalid block references and orphaned blocks. `dist/build-report.json` records the resulting sprite sizes and message counts.

Run `python tools/build.py` after changing the generator. Every build also archives its native code, assets and generator. `node tools/verify-sprite-split.mjs` loads the delivered file in Scratch, verifies sprite ownership and local calls, captures the editor and stage, and checks native simulation performance. The existing physics, track-code, mobile, confirmation and release checks exercise behavior across the new message boundaries.
