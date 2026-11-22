// news-image-20261122 v1 — "The Sunday Ledger"
// Entrypoint: copies the pre-rendered entry.png to /output/entry.png.
// Node 22 stdlib only. No network, no dependencies.
//
// - Refuses to copy an empty or missing source instead of producing a
//   zero-byte output the grader would score as a blank entry.
// - Reports the byte count of both files and verifies the copy matches.
// - Verifies the copied output carries the PNG magic bytes.
// - Never removes or recreates the output directory: /output is a mount
//   point in the grader, so it is only created if absent (recursive
//   mkdir is a no-op when it already exists).
// - OUTPUT_DIR may override the destination (used for local testing).
import { copyFileSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "entry.png");
const outDir = process.env.OUTPUT_DIR ?? "/output";
const dst = join(outDir, "entry.png");

const srcStat = statSync(src);
if (srcStat.size === 0) {
  throw new Error(`Refusing to copy empty source file: ${src}`);
}

mkdirSync(outDir, { recursive: true });
copyFileSync(src, dst);

const dstStat = statSync(dst);
if (dstStat.size !== srcStat.size) {
  throw new Error(
    `Copy size mismatch: ${src} is ${srcStat.size} bytes but ${dst} is ${dstStat.size} bytes`,
  );
}

// Verify the copied file is really a PNG (magic bytes), not a truncated write.
const dstHead = readFileSync(dst).subarray(0, 8);
const pngMagic = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!dstHead.equals(pngMagic)) {
  throw new Error(`Output is not a valid PNG: ${dst}`);
}
console.log(`Copied ${src} -> ${dst} (${dstStat.size} bytes)`);
