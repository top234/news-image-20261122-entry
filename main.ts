// news-image-20261122 v3 — "The World in One Day"
// Entrypoint for the grader: copies the pre-rendered entry.png into the
// output directory and proves the copy is intact.
//
// Node 22 standard library only. No network, no dependencies, no clock,
// no randomness — the same input always produces the same output file.
//
// The output directory is created when missing (recursive mkdir). It is
// NEVER removed: under the grader /output is a mount point, and deleting
// it would fail the run.

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function sha256Hex(bytes: Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function fail(message: string): never {
  console.error(`main.ts: ${message}`);
  process.exit(1);
}

async function run(): Promise<void> {
  const here = dirname(fileURLToPath(import.meta.url));
  const sourcePath = join(here, "entry.png");

  let source: Buffer;
  try {
    source = await readFile(sourcePath);
  } catch {
    fail(`cannot read ${sourcePath} — entry.png is missing next to main.ts`);
  }

  if (source.length === 0) {
    fail("entry.png is empty; refusing to emit a blank entry");
  }
  if (!source.subarray(0, 8).equals(PNG_MAGIC)) {
    fail("entry.png does not start with the PNG magic bytes");
  }
  // The competition requires a 1024x1024 image: read width/height straight
  // out of the IHDR chunk (bytes 16-23, big-endian) and refuse anything else.
  if (source.length < 24 || source.subarray(12, 16).toString("ascii") !== "IHDR") {
    fail("entry.png has no IHDR chunk where a PNG must have one");
  }
  const width = source.readUInt32BE(16);
  const height = source.readUInt32BE(20);
  if (width !== 1024 || height !== 1024) {
    fail(`entry.png is ${width}x${height}; the entry must be 1024x1024`);
  }
  const expectedDigest = sha256Hex(source);

  const outDir = process.env.OUTPUT_DIR ?? "/output";
  const destPath = join(outDir, "entry.png");

  await mkdir(outDir, { recursive: true });
  await writeFile(destPath, source);

  // Verify the copy on disk: same bytes, same digest, same size.
  const copy = await readFile(destPath);
  if (copy.length !== source.length) {
    fail(
      `copied size mismatch: wrote ${source.length} bytes, ` +
        `read back ${copy.length} bytes`,
    );
  }
  const actualDigest = sha256Hex(copy);
  if (actualDigest !== expectedDigest) {
    fail(
      `copied digest mismatch: expected ${expectedDigest}, ` +
        `got ${actualDigest}`,
    );
  }

  console.log(`wrote ${destPath}`);
  console.log(`dimensions: ${width}x${height}`);
  console.log(`bytes: ${copy.length}`);
  console.log(`sha256: ${actualDigest}`);
  console.log("verify: OK (magic bytes, IHDR 1024x1024, size, sha256 all match)");
}

await run();
