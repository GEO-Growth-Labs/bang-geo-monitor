import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "docs", "assets", "bang-demo.png");
const platforms = ["豆包", "DeepSeek", "元宝", "千问", "Kimi"];
const colors = { 5: "#FCE2E2", 4: "#FCE8D6", 3: "#EADCF8", 2: "#DDEBFF", 1: "#DDF2E3" };

const sourcePool = [
  ["示例资讯 A", 5], ["示例社区 B", 5], ["示例观察 C", 4], ["示例指南 D", 4],
  ["示例媒体 E", 3], ["示例知识 F", 3], ["示例评测 G", 3], ["示例行业 H", 2],
  ["示例生活 I", 2], ["示例百科 J", 2], ["示例频道 K", 1], ["示例日报 L", 1],
  ["示例网络 M", 1], ["示例焦点 N", 1], ["示例发布 O", 1], ["示例参考 P", 1],
  ["示例数据 Q", 1], ["示例市场 R", 1], ["示例消费 S", 1], ["示例研究 T", 1],
];

function sourcesFor(platformIndex) {
  return sourcePool
    .filter(([, appearances], index) => appearances === 5 || (index + platformIndex) % 5 < appearances)
    .slice(0, 20)
    .map(([name, appearances], index) => ({
      name,
      appearances,
      count: 18640 - platformIndex * 1310 - index * 647,
    }));
}

const sources = platforms.map((_, index) => sourcesFor(index));
const maxRows = 20;
const weak = Array.from({ length: maxRows }, (_, index) => ({
  keyword: `示例选购问题 ${String(index + 1).padStart(2, "0")}`,
  gap: 0.4769 - index * 0.0127,
}));

const header = `
  <tr class="group"><th colspan="2" class="keyword-head">薄弱关键词</th><th colspan="15" class="source-head">信源池</th></tr>
  <tr class="platform"><th>关键词</th><th>差值</th>${platforms.map(p => `<th colspan="3">${p}</th>`).join("")}</tr>
  <tr class="sub"><td></td><td></td>${platforms.map(() => "<th>信源平台</th><th>引用数</th><th>平台占比</th>").join("")}</tr>`;

const body = Array.from({ length: maxRows }, (_, row) => {
  const cells = platforms.map((_, platformIndex) => {
    const item = sources[platformIndex][row] || {
      name: `示例长尾 ${platformIndex + 1}-${row + 1}`,
      appearances: 1,
      count: Math.max(120, 4860 - row * 183 - platformIndex * 107),
    };
    const total = sources[platformIndex].reduce((sum, current) => sum + current.count, 0) || 1;
    return `<td class="source-name" style="background:${colors[item.appearances]}">${item.name}</td><td class="number">${item.count.toLocaleString("en-US")}</td><td class="number">${(item.count / total * 100).toFixed(2)}%</td>`;
  }).join("");
  return `<tr><td class="keyword">${weak[row].keyword}</td><td class="number">${(weak[row].gap * 100).toFixed(2)}%</td>${cells}</tr>`;
}).join("");

const html = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
* { box-sizing: border-box; }
html, body { width: 2000px; height: 710px; margin: 0; overflow: hidden; background: #ffffff; }
body { padding: 12px; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; color: #20242a; }
table { width: 1976px; table-layout: fixed; border-collapse: collapse; font-size: 12px; }
col.keyword { width: 360px; } col.gap { width: 90px; } col.source { width: 104px; } col.count { width: 72px; } col.share { width: 72px; }
th, td { height: 27px; padding: 4px 7px; border: 1px solid #dfe3e8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
th { font-weight: 650; text-align: center; background: #f7f8fa; }
.group th { height: 31px; font-size: 13px; }
.keyword-head { background: #d9f3f0; }
.source-head { background: #eaf2ff; }
.platform th { height: 28px; background: #f6f7f9; }
.sub td, .sub th { height: 27px; background: #fafbfc; }
.keyword { text-align: left; }
.number { text-align: right; font-variant-numeric: tabular-nums; }
.source-name { text-align: center; font-weight: 520; }
</style></head><body>
<table><colgroup><col class="keyword"><col class="gap">${platforms.map(() => '<col class="source"><col class="count"><col class="share">').join("")}</colgroup>
<thead>${header}</thead><tbody>${body}</tbody></table>
</body></html>`;

await fs.mkdir(path.dirname(output), { recursive: true });
const launchOptions = { headless: true };
const macChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
if (process.env.CHROME_PATH) {
  launchOptions.executablePath = process.env.CHROME_PATH;
} else {
  try {
    await fs.access(macChrome);
    launchOptions.executablePath = macChrome;
  } catch {
    // Use the browser installed by Playwright on non-macOS development hosts.
  }
}
const browser = await chromium.launch(launchOptions);
const page = await browser.newPage({ viewport: { width: 2000, height: 710 }, deviceScaleFactor: 2 });
await page.setContent(html, { waitUntil: "load" });
await page.screenshot({ path: output, fullPage: false });
await browser.close();
console.log(output);
