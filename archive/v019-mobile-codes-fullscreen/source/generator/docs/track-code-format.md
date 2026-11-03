# LR1 track codes

`LR1` is a compact text format implemented in native Scratch blocks in `tools/track_code.py`. It retains track geometry and flags, independently of the editor or saved slot.

The default course has 140 segments and produces 898 characters. Its equivalent segment-array JSON uses 6,862 characters, an 86.9% reduction.

## Alphabet and integers

The alphabet is `0123456789ABCDEFGHJKMNPQRSTVWXYZ`. The prefix is the literal `LR1`. Loading ignores spaces, tabs, CR/LF and hyphens, and accepts lowercase.

Each base-32 digit carries four payload bits. Values 16 through 31 indicate that another digit follows. Payloads are least significant first. For example, unsigned 16 is `G1`. The last payload must be nonzero when the integer uses more than one digit. An integer occupies at most eight digits and cannot exceed 400,000,000.

Signed integers use zigzag encoding: nonnegative `n` becomes `2*n`; negative `n` becomes `-2*n-1`.

Coordinates are quantized once with `floor(value*100 + 0.5)`, matching Scratch and JavaScript rounding. Stored coordinates therefore use hundredths of a world unit. Quantize both endpoints before taking differences; this preserves connections. Normals, inverse lengths, spatial grid and bounds are recomputed after loading.

## Body layout

All fields following the three-character prefix are variable-length integers.

| Field | Encoding |
| --- | --- |
| Segment count | Unsigned, 0 through 3,000 |
| Goal enabled | Unsigned, 0 or 1 |
| Start flag X, Y | Two signed quantized coordinates |
| Goal flag X, Y | Two signed quantized coordinates, retained even when the goal is disabled |
| Segment records | Exactly the declared number, in original order |
| Checksum | Unsigned, computed over every preceding body digit |

A segment record begins with `material*2 + connected`. Materials are 0 Normal, 1 Grip, 2 Ice and 3 Scenery. `connected` is 1 when the quantized start equals the preceding segment's quantized end. Before the first segment, the preceding end is `(0, 0)`.

When `connected` is 0, two signed integers store the segment start minus the preceding end. These are omitted when `connected` is 1. Two signed integers then store the segment end minus its start. Update the preceding end after each record.

Segments follow the editor's left-to-right orientation. Vertical segments retain their original Y direction. The decoder rejects reversed X direction, zero-length lines and coordinates outside +/-1,000,000 world units.

## Checksum and loading

Start the checksum at 1. For each body digit before the checksum, let `d` be its index in the 32-character alphabet and update `hash = (hash*33 + d) mod 65521`. Include continuation bits. Encode the final hash as one unsigned integer without adding its own digits to the hash. Do not hash the prefix or ignored formatting characters.

The decoder rejects unexpected suffixes, invalid characters, noncanonical integers, invalid metadata/materials, too many segments, excessive coordinates, zero-length lines and mismatching checksums. Raw input is limited to 120,000 characters. It stages every record before changing the editor. Only a fully validated code creates an undo snapshot and commits the track. The saved slot is preserved.

Export assembles single-character pieces in a temporary list, then joins it once using Scratch's single-character list conversion. Temporary decode lists are cleared after use. Encoding and decoding run only on request, outside the physics loop.
