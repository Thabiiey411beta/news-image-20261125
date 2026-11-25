// Entry program for make.fun news-image-20261125.
// The image was rendered offline (see README.md) and is held in this
// repository as entry.png. This program verifies it and copies it to
// the output directory. It uses no network and is fully deterministic:
// the same input bytes always produce the same output bytes.

import { copyFileSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const MAX_BYTES = 1024 * 1024;
const EXPECTED_WIDTH = 1024;
const EXPECTED_HEIGHT = 1024;

const input = join(import.meta.dirname, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const output = join(outDir, "entry.png");

const data = readFileSync(input);

// The file must be a PNG.
if (data.length < 33 || !data.subarray(0, 8).equals(PNG_MAGIC)) {
  throw new Error("entry.png is not a PNG file");
}

// It must fit the bounty size cap.
if (data.length > MAX_BYTES) {
  throw new Error(`entry.png is ${data.length} bytes, over the 1 MiB limit`);
}

// The file must end with a proper IEND chunk, so a truncated PNG
// is rejected instead of being copied out half-written.
const tail = data.subarray(data.length - 12);
if (tail.readUInt32BE(0) !== 0 || tail.subarray(4, 8).toString("ascii") !== "IEND") {
  throw new Error("entry.png is truncated: missing IEND chunk");
}

// The first chunk must be IHDR, and the image must be exactly 1024x1024.
const chunkType = data.subarray(12, 16).toString("ascii");
if (chunkType !== "IHDR") {
  throw new Error(`entry.png first chunk is ${chunkType}, expected IHDR`);
}
const width = data.readUInt32BE(16);
const height = data.readUInt32BE(20);
if (width !== EXPECTED_WIDTH || height !== EXPECTED_HEIGHT) {
  throw new Error(
    `entry.png is ${width}x${height}, expected ${EXPECTED_WIDTH}x${EXPECTED_HEIGHT}`,
  );
}

mkdirSync(outDir, { recursive: true });
copyFileSync(input, output);

const written = statSync(output).size;
console.log(`wrote ${written} bytes to ${output}`);
