// news-image-20261122 v4 — "The World in One Day"
//
// Grader entrypoint: places the pre-rendered entry.png into the output
// directory and proves the placed file is byte-for-byte the entry.
//
// The image is rendered ahead of time by generate.py (PIL) so this file
// needs nothing beyond the Node 22 standard library: no network, no
// dependencies, no clock, no randomness. The same entry.png always
// produces the same output file.
//
// The output directory is created when missing (recursive mkdir). It is
// NEVER deleted: under the grader /output is a mount point, and removing
// it would fail the run.

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_SIGNATURE = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);

function digest(bytes: Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function abort(reason: string): never {
  console.error(`main.ts: refusing to emit — ${reason}`);
  process.exit(1);
}

function loadEntry(): Buffer {
  const here = dirname(fileURLToPath(import.meta.url));
  const entryPath = join(here, "entry.png");
  if (!existsSync(entryPath)) {
    abort(`entry.png is missing next to main.ts (${entryPath})`);
  }
  const bytes = readFileSync(entryPath);
  if (bytes.length === 0) {
    abort("entry.png is empty");
  }
  if (!bytes.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)) {
    abort("entry.png does not start with the PNG signature");
  }
  // The competition requires a 1024x1024 image no larger than 1 MiB:
  // read the width/height straight out of the IHDR chunk (bytes 16-23,
  // big-endian) and refuse anything else before a single byte is placed.
  if (
    bytes.length < 24 ||
    bytes.subarray(12, 16).toString("ascii") !== "IHDR"
  ) {
    abort("entry.png has no IHDR chunk where a PNG must have one");
  }
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (width !== 1024 || height !== 1024) {
    abort(`entry.png is ${width}x${height}; the entry must be 1024x1024`);
  }
  if (bytes.length > 1024 * 1024) {
    abort(`entry.png is ${bytes.length} bytes; the limit is 1 MiB`);
  }
  return bytes;
}

function main(): void {
  const entry = loadEntry();
  const expected = digest(entry);

  const outDir = process.env.OUTPUT_DIR ?? "/output";
  const dest = join(outDir, "entry.png");

  mkdirSync(outDir, { recursive: true });
  writeFileSync(dest, entry);

  // Prove the copy on disk is intact: same length, same digest.
  const placed = readFileSync(dest);
  if (placed.length !== entry.length) {
    abort(
      `placed size mismatch: wrote ${entry.length} bytes, ` +
        `read back ${placed.length} bytes`,
    );
  }
  const actual = digest(placed);
  if (actual !== expected) {
    abort(`placed digest mismatch: expected ${expected}, got ${actual}`);
  }

  console.log(`wrote ${dest}`);
  console.log(`dimensions: 1024x1024 (IHDR verified)`);
  console.log(`bytes: ${placed.length}`);
  console.log(`sha256: ${actual}`);
  console.log(
    "verify: OK (PNG signature, IHDR 1024x1024, size, sha256 all match)",
  );
}

main();
