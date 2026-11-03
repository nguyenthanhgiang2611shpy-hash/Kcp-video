// Render từng khung bằng Chromium headless -> ffmpeg.  node render.js [out.mp4] [test]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = __dirname, FPS = 25;
const out = process.argv[2] || path.join(ROOT, 'out.mp4'), test = process.argv[3] === 'test';
const types = { '.html': 'text/html', '.js': 'text/javascript' };
const srv = http.createServer((q, r) => {
  const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; }
    r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
}).listen(0, async () => {
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', m => console.log('page:', m.text())); page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto(`http://127.0.0.1:${port}/scene.html`);
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
  const dur = await page.evaluate('window.DUR');
  if (test) {
    const ts = process.argv.slice(4).map(Number);
    for (const t of ts) { await page.evaluate(`renderAt(${t})`);
      await page.screenshot({ path: path.join(path.dirname(out), `t_${t}.png`) }); }
    await browser.close(); srv.close(); return;
  }
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * FPS), t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(`renderAt(${i / FPS})`);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 100 === 0) console.log(`frame ${i}/${n} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close(); srv.close(); console.log('done');
});
