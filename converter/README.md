# Line Rider track converter

Static browser tool. Open dist/index.html in a browser, or use the deployed Site. No server or install is needed. All files are read locally.

Accepts this project's LR1 text codes and linerider.com .track.json exports, including lines, linesArray and LZ-string compressed linesArrayCompressed. Output is the native Scratch LR1 format. In Scratch choose Track > Load track code, paste, and submit.

Normal lines map to Normal and scenery to Scenery. Acceleration lines preserve their boost direction. Collision-side changes and endpoint extensions require the compatibility checkbox and are reported. Only the first rider's position is used; custom starting velocity is reported and omitted. No goal is invented for official imports. Audio/scripts are omitted. Layer metadata and custom physics are not carried over. Binary .trk and Flash .sol formats are not supported. Maximum 3,000 segments, ±1,000,000 coordinates and 120,000 code characters. Precision is 0.01 units, matching Scratch.

Run `node test.mjs` from this directory. Browser integration: `node tools/capture-converter.mjs` from the repository root, using the existing local optimizer's Puppeteer dependency.

Format references: the checked-in lr-core source and https://gist.github.com/jealouscloud/c1c9805ffa7cbf4052aa479ac257dff2 . Vendored lz-string 1.5.0 is MIT licensed: https://github.com/pieroxy/lz-string .
