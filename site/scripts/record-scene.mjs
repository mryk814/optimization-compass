#!/usr/bin/env node
/**
 * Records an explorable's guided scene to video (ADR 0018 §5).
 *
 *   node scripts/record-scene.mjs gradient-descent-valley [--fps 30] [--scale 1.5] [--out dir]
 *   node scripts/record-scene.mjs gradient-descent-valley --still 12.5   # one frame, for layout checks
 *
 * It starts the Vite dev server, opens `#/record/<id>`, and steps scene time through
 * `window.__ocScene.seek(t)` one frame at a time, so every frame is the figure's own
 * deterministic state at `t`, never wall-clock playback. Frames go straight to ffmpeg.
 * Outputs: scene.mp4 (H.264), scene.webm (VP9), poster.png, captions.vtt, transcript.txt and
 * manifest.json, whose `input_sha256` decides whether a recording is stale.
 */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { chromium } from "@playwright/test";

const siteRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = resolve(siteRoot, "..");
const WIDTH = 1280;
const HEIGHT = 720;

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    fps: { type: "string", default: "30" },
    scale: { type: "string", default: "1.5" },
    out: { type: "string" },
    port: { type: "string", default: "4198" },
    still: { type: "string" },
  },
});
const id = positionals[0];
if (!id || !/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/u.test(id)) {
  console.error("usage: node scripts/record-scene.mjs <explorable-id> [--fps 30] [--scale 1.5] [--out dir]");
  process.exit(2);
}
const fps = Number(values.fps);
const scale = Number(values.scale);
const outDir = resolve(values.out ?? join(siteRoot, ".scene-media", id));

/** Everything a frame depends on: the registry and the figure's source. */
async function inputHash() {
  const hash = createHash("sha256");
  const files = [join(repoRoot, "src", "optimization_compass", "resources", "explorables.json")];
  const walk = async (dir) => {
    for (const entry of (await readdir(dir, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) await walk(path);
      else if (!/\.test\.tsx?$/u.test(entry.name)) files.push(path);
    }
  };
  await walk(join(siteRoot, "src", "features", "explorable"));
  for (const file of files) {
    hash.update(relative(repoRoot, file).replaceAll("\\", "/"));
    hash.update("\0");
    // Normalize line endings so a Windows checkout hashes like CI.
    hash.update((await readFile(file, "utf8")).replaceAll("\r\n", "\n"));
    hash.update("\0");
  }
  return hash.digest("hex");
}

function run(command, args, { input } = {}) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(command, args, { stdio: [input ? "pipe" : "ignore", "ignore", "pipe"] });
    let stderr = "";
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => (code === 0 ? resolvePromise() : reject(new Error(`${command} exited ${code}\n${stderr.slice(-2000)}`))));
    if (input) input(child.stdin);
  });
}

async function startDevServer(port) {
  // One command string: Windows needs a shell to find npx, and `port` is validated as a number.
  const server = spawn(`npx vite --host 127.0.0.1 --port ${Number(port)} --strictPort`, {
    cwd: siteRoot,
    shell: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  const url = `http://127.0.0.1:${port}/optimization-compass/`;
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try {
      if ((await fetch(url)).ok) return { server, url };
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  server.kill();
  throw new Error(`dev server did not start on ${url}`);
}

function stopServer(server) {
  if (process.platform === "win32") spawn("taskkill", ["/pid", String(server.pid), "/T", "/F"], { stdio: "ignore" });
  else server.kill();
}

async function sha256File(path) {
  return createHash("sha256").update(await readFile(path)).digest("hex");
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const { server, url } = await startDevServer(values.port);
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({
      viewport: { width: WIDTH, height: HEIGHT },
      deviceScaleFactor: scale,
      reducedMotion: "no-preference",
      locale: "ja-JP",
    });
    await page.goto(`${url}#/record/${id}`);
    await page.waitForFunction(() => Boolean(window.__ocScene), undefined, { timeout: 30_000 });
    await page.evaluate(() => document.fonts.ready);
    const scene = await page.evaluate(() => ({
      durationS: window.__ocScene.durationS,
      beats: window.__ocScene.beats,
      webVtt: window.__ocScene.webVtt,
    }));
    if (values.still !== undefined) {
      const path = join(outDir, `still-${values.still}.png`);
      await page.evaluate((t) => window.__ocScene.seek(t), Number(values.still));
      await page.screenshot({ path, type: "png" });
      console.log(path);
      return;
    }
    const frames = Math.round(scene.durationS * fps) + 1;
    const mp4 = join(outDir, "scene.mp4");
    console.log(`recording ${id}: ${scene.beats.length} beats, ${scene.durationS}s, ${frames} frames → ${outDir}`);

    await run("ffmpeg", [
      "-y", "-loglevel", "error",
      "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
      "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
      "-movflags", "+faststart", mp4,
    ], {
      input: async (stdin) => {
        try {
          for (let frame = 0; frame < frames; frame += 1) {
            await page.evaluate((t) => window.__ocScene.seek(t), Math.min(frame / fps, scene.durationS));
            const png = await page.screenshot({ type: "png" });
            if (!stdin.write(png)) await new Promise((r) => stdin.once("drain", r));
            if (frame % fps === 0) process.stdout.write(`\r  ${frame}/${frames}`);
          }
          process.stdout.write(`\r  ${frames}/${frames}\n`);
        } finally {
          stdin.end();
        }
      },
    });

    await page.evaluate((t) => window.__ocScene.seek(t), scene.durationS);
    await page.screenshot({ path: join(outDir, "poster.png"), type: "png" });
    await run("ffmpeg", [
      "-y", "-loglevel", "error", "-i", mp4,
      "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36", "-row-mt", "1", join(outDir, "scene.webm"),
    ]);
    await writeFile(join(outDir, "captions.vtt"), scene.webVtt, "utf8");
    await writeFile(
      join(outDir, "transcript.txt"),
      `${scene.beats.map((beat, index) => `${index + 1}. ${beat.narrationJa}`).join("\n")}\n`,
      "utf8",
    );

    const outputs = {};
    for (const name of ["scene.mp4", "scene.webm", "poster.png", "captions.vtt", "transcript.txt"]) {
      const path = join(outDir, name);
      outputs[name] = { bytes: (await stat(path)).size, sha256: await sha256File(path) };
    }
    const manifest = {
      schema_version: 1,
      explorable_id: id,
      input_sha256: await inputHash(),
      duration_s: scene.durationS,
      fps,
      frame_size: [Math.round(WIDTH * scale), Math.round(HEIGHT * scale)],
      beats: scene.beats.length,
      narration: null,
      outputs,
    };
    await writeFile(join(outDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
    for (const [name, { bytes }] of Object.entries(outputs)) console.log(`  ${name.padEnd(15)} ${(bytes / 1024).toFixed(0)} KB`);
  } finally {
    await browser.close();
    stopServer(server);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
