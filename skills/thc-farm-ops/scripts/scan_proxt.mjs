// Playwright scan proxy pool -> good list. Tanpa skema (thc_farm.mjs nambah "http://" sendiri).
// pakai: node scan_proxt.mjs [src] [out] [sample]
import { chromium } from "playwright";
import { readFileSync, writeFileSync } from "node:fs";

const SRC = process.argv[2] || "~/app/proxt.txt";
const OUT = process.argv[3] || "~/app/cache/scratch/thc/good_proxt.txt";
const SAMPLE = parseInt(process.argv[4] || "120", 10);

const all = readFileSync(SRC, "utf-8").split("\n").map((l) => l.trim()).filter(Boolean);
const sample = all.sort(() => Math.random() - 0.5).slice(0, SAMPLE);
console.log(`[SCAN] pool=${all.length} sample=${sample.length}`);

const b = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
const good = [];
let done = 0;
async function test(h) {
  const server = (h.startsWith("http")) ? h : "http://" + h;
  const c = await b.newContext({ proxy: { server }, locale: "en-US" });
  const pg = await c.newPage();
  try {
    await pg.goto("https://tokenharbor.ai/login?mode=signup", { waitUntil: "domcontentloaded", timeout: 20000 });
    await pg.waitForTimeout(3000);
    const hasEmail = await pg.locator('input[type=email], input[name=email]').count();
    if (hasEmail) { good.push(h.includes("@") ? h.split("//")[1] : h); }
  } catch (e) {}
  await c.close().catch(() => {});
}
for (let i = 0; i < sample.length; i += 8) {
  await Promise.all(sample.slice(i, i + 8).map(test));
  done += Math.min(8, sample.length - i);
  console.log(`...${done}/${sample.length}`);
}
writeFileSync(OUT, good.join("\n"));
console.log("=== GOOD:", good.length);
await b.close();
