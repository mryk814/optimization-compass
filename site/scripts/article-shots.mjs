#!/usr/bin/env node
/**
 * Review contact sheet for articles (the owner reviews on the rendered screen, not in Markdown).
 *
 *   npm --prefix site run shots -- concept.linear-least-squares gradient-descent [--base URL] [--out dir]
 *
 * Per content id it writes <out>/<id>/: full-page PNGs at 1280 / 375 / 320 wide, one still per
 * guided-scene beat of every explorable on the page (each with its caption), and index.html
 * putting them side by side. <out>/index.html links every article processed.
 *
 * Beats come from the live record page (`window.__ocScene.beats`, the same mechanism as
 * record-scene.mjs), so this works wherever the explorable metadata is stored.
 * The default base is the dev server (`npm --prefix site run dev`); for a built site use
 * `npx vite preview --port N` and pass --base http://127.0.0.1:N/optimization-compass/.
 */
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { chromium } from "@playwright/test";

const siteRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const WIDTHS = [1280, 375, 320];
const VIEW_H = 900;

const { values, positionals: ids } = parseArgs({
  allowPositionals: true,
  options: { base: { type: "string", default: "http://localhost:5199/optimization-compass/" }, out: { type: "string" } },
});
if (ids.length === 0) {
  console.error("usage: npm --prefix site run shots -- <content-id> [<content-id> ...] [--base URL] [--out dir]");
  process.exit(2);
}
const base = values.base.endsWith("/") ? values.base : `${values.base}/`;
const outRoot = resolve(values.out ?? join(siteRoot, ".review-shots"));

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ESC[c]);
const slug = (id) => id.replace(/[^A-Za-z0-9._-]/g, "_");

async function reachable() {
  try {
    return (await fetch(base)).ok;
  } catch {
    return false;
  }
}

/** Waits for the redirect off /learn/, the article body, fonts and math, then wakes lazy mounts. */
async function loadArticle(page, id) {
  await page.goto(`${base}#/learn/${id}`);
  await page.waitForSelector("main h1", { timeout: 30_000 });
  // Some pages redirect to /methods/ or /formulations/, others render in place under /learn/.
  await page.waitForFunction(() => !location.hash.startsWith("#/learn/"), undefined, { timeout: 2_500 }).catch(() => {});
  await page.waitForSelector("main h1", { timeout: 30_000 });
  if ((await page.textContent("main h1"))?.includes("ページが見つかりません")) throw new Error(`content id not found: ${id}`);
  await page.evaluate(() => document.fonts.ready);
  // Scroll down in steps so anything mounted on intersection renders, then return to the top.
  await page.evaluate(async () => {
    const step = Math.max(300, innerHeight * 0.8);
    for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
      scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 120));
    }
    scrollTo(0, 0);
  });
  await page
    .waitForFunction(
      () => [...document.querySelectorAll("figure[data-explorable-id]")].every((f) => f.querySelector("svg, canvas")),
      undefined,
      { timeout: 15_000 },
    )
    .catch(() => {});
  await page.waitForTimeout(500);
}

async function shootArticle(browser, id) {
  const dir = join(outRoot, slug(id));
  await mkdir(dir, { recursive: true });
  const result = { id, dir, finalHash: "", shots: [], explorables: [], errors: [], beatSets: [] };

  for (const width of WIDTHS) {
    const context = await browser.newContext({ viewport: { width, height: VIEW_H }, locale: "ja-JP", reducedMotion: "no-preference" });
    const page = await context.newPage();
    try {
      await loadArticle(page, id);
      const info = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        hash: location.hash,
        title: document.querySelector("main h1")?.textContent ?? "",
        explorables: [...document.querySelectorAll("figure[data-explorable-id]")].map((f) => f.getAttribute("data-explorable-id")),
      }));
      const file = `w${width}.png`;
      await page.screenshot({ path: join(dir, file), fullPage: true });
      result.shots.push({ width, file, overflow: info.overflow, scrollWidth: info.scrollWidth, clientWidth: info.clientWidth });
      if (width === WIDTHS[0]) {
        result.finalHash = info.hash;
        result.title = info.title;
        result.explorables = [...new Set(info.explorables)];
      }
    } catch (error) {
      result.errors.push(`${width}px: ${error.message.split("\n")[0]}`);
    } finally {
      await context.close();
    }
  }

  for (const exId of result.explorables) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, locale: "ja-JP", reducedMotion: "no-preference" });
    const page = await context.newPage();
    try {
      await page.goto(`${base}#/record/${exId}`);
      const ready = await page.waitForFunction(() => Boolean(window.__ocScene), undefined, { timeout: 8_000 }).then(
        () => true,
        () => false,
      );
      if (!ready) {
        result.beatSets.push({ id: exId, beats: [] });
        continue;
      }
      await page.evaluate(() => document.fonts.ready);
      const beats = await page.evaluate(() =>
        window.__ocScene.beats.map((b) => ({ durationS: b.durationS, captionJa: b.captionJa, narrationJa: b.narrationJa })),
      );
      const stills = [];
      let end = 0;
      for (let i = 0; i < beats.length; i += 1) {
        end += beats[i].durationS;
        // Just inside the beat: a boundary belongs to the next beat (scene.ts sceneAt).
        const t = i === beats.length - 1 ? end : end - 0.001;
        await page.evaluate((time) => window.__ocScene.seek(time), t);
        const file = `beat-${slug(exId)}-${String(i + 1).padStart(2, "0")}.png`;
        await page.screenshot({ path: join(dir, file), type: "png" });
        stills.push({ file, caption: beats[i].captionJa, narration: beats[i].narrationJa, t });
      }
      result.beatSets.push({ id: exId, beats: stills });
    } catch (error) {
      result.errors.push(`explorable ${exId}: ${error.message.split("\n")[0]}`);
    } finally {
      await context.close();
    }
  }
  return result;
}

const CSS = `
body{font:14px/1.5 system-ui,"Yu Gothic",sans-serif;margin:16px;color:#1b1f24;background:#f6f7f9}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:24px 0 8px}
a{color:#0b5cad}.meta{color:#566;font-size:12px}
.warn{background:#fff1c9;border:1px solid #d9a400;padding:6px 10px;border-radius:4px;margin:8px 0}
.err{background:#fde0e0;border:1px solid #c33;padding:6px 10px;border-radius:4px;margin:8px 0}
.row{display:flex;gap:16px;align-items:flex-start;overflow-x:auto;padding-bottom:8px}
.row figure{margin:0;flex:none}.row figcaption{font-size:12px;color:#445;margin-bottom:4px}
.row img{display:block;border:1px solid #ccd;background:#fff}
.film{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px}
.film figure{margin:0;flex:none;width:320px}.film img{width:320px;border:1px solid #ccd;background:#fff;display:block}
.film figcaption{font-size:12px;margin-top:4px}
`;

async function writeSheet(r) {
  const MAX_H = 1400; // display height cap for the scaled-down full-page shots
  const pngSize = async (file) => {
    const buf = await readFile(join(r.dir, file));
    return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  };
  const cols = [];
  for (const s of r.shots) {
    const { w, h } = await pngSize(s.file);
    const scale = Math.min(1, MAX_H / h, 560 / w);
    cols.push(`<figure><figcaption>${s.width}px${s.overflow ? ` <b>横あふれ ${s.scrollWidth}&gt;${s.clientWidth}</b>` : ""} (${w}x${h})</figcaption>
<a href="${s.file}" target="_blank"><img src="${s.file}" width="${Math.round(w * scale)}" loading="lazy" alt="${s.width}px"></a></figure>`);
  }
  const overflow = r.shots.filter((s) => s.overflow).map((s) => `${s.width}px (scrollWidth ${s.scrollWidth} &gt; clientWidth ${s.clientWidth})`);
  const films = r.beatSets
    .map(
      (set) => `<h2>${esc(set.id)}${set.beats.length ? ` — ${set.beats.length} 場面` : " — 解説付きの場面なし"}</h2>
<div class="film">${set.beats
        .map(
          (b, i) => `<figure><a href="${b.file}" target="_blank"><img src="${b.file}" loading="lazy" alt="beat ${i + 1}"></a>
<figcaption><b>${i + 1}.</b> ${esc(b.caption)}<br><span class="meta">${esc(b.narration)}</span></figcaption></figure>`,
        )
        .join("")}</div>`,
    )
    .join("\n");
  const html = `<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(r.id)}</title><style>${CSS}</style>
<p><a href="../index.html">&larr; 一覧</a></p>
<h1>${esc(r.title ?? r.id)}</h1><div class="meta">${esc(r.id)} &rarr; ${esc(r.finalHash)} · explorable ${r.explorables.length} 件</div>
${overflow.length ? `<div class="warn"><b>横スクロールが出ています:</b> ${overflow.join(" / ")}</div>` : ""}
${r.errors.map((e) => `<div class="err">${esc(e)}</div>`).join("")}
<div class="row">${cols.join("\n")}</div>
${films}
</html>`;
  await writeFile(join(r.dir, "index.html"), html, "utf8");
}

async function writeIndex() {
  // Rebuild from every article folder so earlier runs stay listed.
  const rows = [];
  for (const entry of await readdir(outRoot, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    try {
      const html = await readFile(join(outRoot, entry.name, "index.html"), "utf8");
      const title = /<h1>(.*?)<\/h1>/u.exec(html)?.[1] ?? entry.name;
      const warn = html.includes('class="warn"') ? " <b>⚠ 横あふれ</b>" : "";
      const err = html.includes('class="err"') ? " <b>⚠ エラー</b>" : "";
      rows.push(`<li><a href="${entry.name}/index.html">${title}</a> <span class="meta">${esc(entry.name)}</span>${warn}${err}</li>`);
    } catch {
      // not an article folder
    }
  }
  await writeFile(
    join(outRoot, "index.html"),
    `<!doctype html><html lang="ja"><meta charset="utf-8"><title>記事レビュー</title><style>${CSS}</style><h1>記事レビュー</h1><ul>${rows.join("\n")}</ul></html>`,
    "utf8",
  );
}

async function main() {
  if (!(await reachable())) {
    console.error(
      `サーバーに届きません: ${base}\n` +
        "  開発サーバー:  npm --prefix site run dev   (http://localhost:5199/optimization-compass/)\n" +
        "  ビルド済み:    cd site && npm run build && npx vite preview --port 4245\n" +
        "                 そのうえで --base http://127.0.0.1:4245/optimization-compass/ を付ける",
    );
    process.exit(1);
  }
  await mkdir(outRoot, { recursive: true });
  const browser = await chromium.launch();
  try {
    for (const id of ids) {
      const r = await shootArticle(browser, id);
      await writeSheet(r);
      const flags = [...r.shots.filter((s) => s.overflow).map((s) => `横あふれ@${s.width}`), ...r.errors.map((e) => `ERR ${e}`)];
      const beatCount = r.beatSets.reduce((n, s) => n + s.beats.length, 0);
      console.log(`${id}: ${r.shots.length} shots, ${beatCount} beat stills${flags.length ? ` [${flags.join("; ")}]` : ""}\n  ${join(r.dir, "index.html")}`);
    }
    await writeIndex();
    console.log(`index: ${join(outRoot, "index.html")}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
