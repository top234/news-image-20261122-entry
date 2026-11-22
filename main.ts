// news-image-20261122 v2 — "The Dawn Ledger"
// Entrypoint: places the pre-rendered entry.png into the grader output
// directory. Node 22 standard library only; no network, no dependencies.
//
// Safety rules baked in:
//  - An empty or missing source is refused instead of producing a blank
//    zero-byte entry the grader would score as nothing.
//  - The destination directory is only created when absent (recursive
//    mkdir). It is NEVER deleted or recreated: in the grader /output is
//    a mount point, and removing it would fail the run.
//  - After copying, the output is checked three ways: its byte count must
//    equal the source, its first 8 bytes must be the PNG signature, and
//    its SHA-256 hash must match the source byte for byte.
//  - OUTPUT_DIR may override the destination (used for local testing).
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_SIGNATURE = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);

function fail(message: string): never {
  throw new Error(`main.ts: ${message}`);
}

function sha256Of(filePath: string): string {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

const scriptDir = dirname(fileURLToPath(import.meta.url));
const sourcePath = join(scriptDir, "entry.png");
const targetDir = process.env.OUTPUT_DIR ?? "/output";
const targetPath = join(targetDir, "entry.png");

if (!existsSync(sourcePath)) {
  fail(`source image missing: ${sourcePath}`);
}

const sourceInfo = statSync(sourcePath);
if (sourceInfo.size === 0) {
  fail(`refusing to copy empty source image: ${sourcePath}`);
}

const sourceHead = readFileSync(sourcePath).subarray(0, 8);
if (!sourceHead.equals(PNG_SIGNATURE)) {
  fail(`source image is not a PNG: ${sourcePath}`);
}

mkdirSync(targetDir, { recursive: true });
copyFileSync(sourcePath, targetPath);

const targetInfo = statSync(targetPath);
if (targetInfo.size !== sourceInfo.size) {
  fail(
    `copy size mismatch: source ${sourceInfo.size} bytes, ` +
      `output ${targetInfo.size} bytes`,
  );
}

const targetHead = readFileSync(targetPath).subarray(0, 8);
if (!targetHead.equals(PNG_SIGNATURE)) {
  fail(`copied output is not a valid PNG: ${targetPath}`);
}

const sourceHash = sha256Of(sourcePath);
const targetHash = sha256Of(targetPath);
if (sourceHash !== targetHash) {
  fail(
    `copy hash mismatch: source sha256 ${sourceHash}, ` +
      `output sha256 ${targetHash}`,
  );
}

console.log(
  `Verified copy: source ${sourceInfo.size} bytes, ` +
    `output ${targetInfo.size} bytes, sha256 ${targetHash}`,
);

console.log(
  `Copied ${sourcePath} -> ${targetPath} (${targetInfo.size} bytes, PNG verified)`,
);
