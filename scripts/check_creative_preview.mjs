#!/usr/bin/env node
// Synthetic loopback preview tests. Never load live creative with this harness.
import { spawn } from 'node:child_process';
import { createServer, request as httpRequest } from 'node:http';
import { connect } from 'node:net';
import { mkdtemp, readFile, rm, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { once } from 'node:events';
import { assessNotifications } from './creative_preview_observations.mjs';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const attempts = {
  'fetch-get': `fetch(url).catch(() => {})`,
  'fetch-head': `fetch(url, {method: 'HEAD'}).catch(() => {})`,
  'fetch-post': `fetch(url, {method: 'POST', body: 'synthetic'}).catch(() => {})`,
  beacon: `navigator.sendBeacon(url, 'synthetic')`,
  xhr: `const x = new XMLHttpRequest(); x.open('GET', url); x.send()`,
  image: `const x = new Image(); x.src = url; document.body.append(x)`,
  script: `const x = document.createElement('script'); x.src = url; document.body.append(x)`,
  iframe: `const x = document.createElement('iframe'); x.src = url; document.body.append(x)`,
  'css-image': `const x = document.createElement('div'); x.style.cssText = 'width:40px;height:40px;background-image:url(' + url + ')'; document.body.append(x)`,
  'video-poster': `const x = document.createElement('video'); x.poster = url; document.body.append(x)`,
  form: `const x = document.createElement('form'); x.method = 'POST'; x.action = url; document.body.append(x); x.submit()`,
  navigation: `location.href = url`,
  websocket: `const x = new WebSocket(url.replace('http:', 'ws:')); x.onerror = () => {}`,
};
const jsonMode = process.argv.includes('--json');
const injectCanary = process.argv.includes('--inject-notification-canary');
const csp = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'";
const escapeAttribute = value => value.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;');
let base;
const received = [];
const gateBlocked = [];
let allowedRequests = new Set();
let allowControlTunnel = false;
// A separate HTTP proxy enforces the fixture policy across renderer changes.
// CSP and target-scoped interception alone missed a navigation in testing.
const gate = createServer((request, response) => {
  let url;
  try { url = new URL(request.url); } catch { response.writeHead(400).end(); return; }
  if (url.origin !== base || !allowedRequests.has(request.method + ' ' + url.href)) {
    gateBlocked.push({method: request.method, url: url.href});
    response.writeHead(403).end(); return;
  }
  const upstream = httpRequest(url, {method: request.method, headers: request.headers}, result => {
    response.writeHead(result.statusCode, result.headers); result.pipe(response);
  });
  upstream.on('error', () => response.writeHead(502).end());
  request.pipe(upstream);
});
gate.on('connect', (request, socket, head) => {
  if (allowControlTunnel && request.url === new URL(base).host) {
    const upstream = connect(server.address().port, '127.0.0.1', () => {
      socket.write('HTTP/1.1 200 Connection Established\r\n\r\n');
      if (head.length) upstream.write(head);
      socket.pipe(upstream); upstream.pipe(socket);
    });
    upstream.on('error', () => socket.destroy()); socket.on('error', () => upstream.destroy());
    socket.on('close', () => upstream.destroy());
    return;
  }
  gateBlocked.push({method: 'CONNECT', url: request.url});
  socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');
});
gate.on('upgrade', (request, socket, head) => {
  let url;
  try { url = new URL(request.url); } catch { socket.destroy(); return; }
  // WebSocket proxy requests use ws: while the fixture allowlist uses http:.
  const normalized = url.href.replace(/^ws:/, 'http:');
  if (!normalized.startsWith(base + '/') || !allowedRequests.has('UPGRADE ' + normalized)) {
    gateBlocked.push({method: 'UPGRADE', url: url.href});
    socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'); return;
  }
  const upstream = connect(server.address().port, '127.0.0.1', () => {
    upstream.write(request.method + ' ' + url.pathname + ' HTTP/1.1\r\n' +
      Object.entries(request.headers).map(([key, value]) => key + ': ' + value).join('\r\n') + '\r\n\r\n');
    if (head.length) upstream.write(head);
    socket.pipe(upstream); upstream.pipe(socket);
  });
  upstream.on('error', () => socket.destroy()); socket.on('error', () => upstream.destroy());
  socket.on('close', () => upstream.destroy());
});
const server = createServer((request, response) => {
  const url = new URL(request.url, base);
  if (url.pathname === '/preview') {
    const id = url.searchParams.get('case');
    const isolated = url.searchParams.get('mode') === 'isolated';
    const operation = attempts[id];
    if (!operation) { response.writeHead(400).end(); return; }
    const eventUrl = base + '/events/' + id;
    const frame = `<!doctype html><meta charset="utf-8">${isolated ? `<meta http-equiv="Content-Security-Policy" content="${csp}">` : ''}<body><script>
      const url = ${JSON.stringify(eventUrl)};
      addEventListener('securitypolicyviolation', event => parent.postMessage({violation: event.violatedDirective}, '*'));
      try { ${operation}; } catch (error) { parent.postMessage({error: error.name}, '*'); }
      parent.postMessage({attempted: ${JSON.stringify(id)}}, '*');
    </script></body>`;
    const html = `<!doctype html><meta charset="utf-8"><title>Synthetic creative inspection</title>
      <script>window.fixtureMessages = []; addEventListener('message', e => { if(e.source === document.querySelector('iframe')?.contentWindow) fixtureMessages.push(e.data); });</script>
      <iframe ${isolated ? 'sandbox="allow-scripts"' : ''} srcdoc="${escapeAttribute(frame)}"></iframe>`;
    response.writeHead(200, { 'Content-Type': 'text/html', 'Cache-Control': 'no-store' });
    response.end(html);
  } else if (url.pathname.startsWith('/events/')) {
    received.push({ method: request.method, path: url.pathname, url: url.href });
    response.writeHead(200, { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'text/plain', 'Cache-Control': 'no-store' });
    response.end('synthetic notification trap');
  } else {
    response.writeHead(404).end();
  }
});
server.on('upgrade', (request, socket) => {
  const url = new URL(request.url, base);
  received.push({ method: 'UPGRADE', path: url.pathname, url: url.href });
  socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');
});

class CDP {
  constructor(socket) {
    this.socket = socket; this.id = 0; this.pending = new Map(); this.handlers = [];
    socket.addEventListener('message', ({data}) => {
      const message = JSON.parse(data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id); clearTimeout(pending.timer);
        if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
        else pending.resolve(message.result);
      } else for (const handler of this.handlers) handler(message);
    });
  }
  call(method, params = {}, sessionId) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error('CDP timed out: ' + method)); }, 10000);
      this.pending.set(id, {resolve, reject, timer});
      this.socket.send(JSON.stringify({ id, method, params, ...(sessionId ? {sessionId} : {}) }));
    });
  }
  close() { this.socket.close(); }
}

async function findChrome() {
  const paths = process.env.CHROME_BIN ? [process.env.CHROME_BIN] : [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ];
  for (const path of paths) { try { await access(path); return path; } catch {} }
  throw new Error('Chrome not found. Set CHROME_BIN to a Chrome/Chromium executable.');
}

let chrome, profile, browser, cdp;
const cases = [];
try {
  const executable = await findChrome();
  profile = await mkdtemp(join(process.env.CREATIVE_CACHE_DIR || tmpdir(), 'openproposal-preview-'));
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  base = 'http://127.0.0.1:' + server.address().port;
  gate.listen(0, '127.0.0.1'); await once(gate, 'listening');
  chrome = spawn(executable, ['--headless=new', '--remote-debugging-port=0', '--user-data-dir=' + profile,
    '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
    '--disable-component-update', '--disable-sync', '--disable-quic',
    '--proxy-server=http://127.0.0.1:' + gate.address().port, '--proxy-bypass-list=<-loopback>',
    'about:blank'], {stdio: 'ignore'});
  let port;
  for (let i = 0; i < 100; i++) {
    try { port = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; } catch {}
    if (chrome.exitCode !== null) throw new Error('Chrome exited before DevTools started');
    await delay(100);
  }
  if (!port) throw new Error('Chrome did not start DevTools');
  const endpoint = 'http://127.0.0.1:' + port;
  browser = await (await fetch(endpoint + '/json/version')).json();
  for (const id of Object.keys(attempts)) {
    for (const mode of ['control', 'isolated', ...(id === 'navigation' ? ['network-gate'] : [])]) {
      const target = await (await fetch(endpoint + '/json/new?about:blank', {method: 'PUT'})).json();
      const socket = new WebSocket(target.webSocketDebuggerUrl);
      await new Promise((resolve, reject) => { socket.addEventListener('open', resolve, {once:true}); socket.addEventListener('error', reject, {once:true}); });
      cdp = new CDP(socket);
      const blocked = [], protocolErrors = [], pendingEvents = new Set();
      const previewUrl = base + '/preview?case=' + id + '&mode=' + mode;
      const isolated = mode !== 'control';
      const expectedMethod = {'fetch-head':'HEAD', 'fetch-post':'POST', beacon:'POST', form:'POST', websocket:'UPGRADE'}[id] || 'GET';
      allowedRequests = new Set(['GET ' + previewUrl]);
      if (!isolated) allowedRequests.add(expectedMethod + ' ' + base + '/events/' + id);
      allowControlTunnel = id === 'websocket' && mode === 'control';
      gateBlocked.length = 0;
      async function guard(sessionId) {
        await cdp.call('Fetch.enable', {patterns: [{urlPattern: '*', requestStage: 'Request'}]}, sessionId);
        await cdp.call('Target.setAutoAttach', {autoAttach: true, waitForDebuggerOnStart: true, flatten: true}, sessionId);
      }
      cdp.handlers.push(message => {
        const work = (async () => {
          if (message.method === 'Fetch.requestPaused') {
            const {requestId, request} = message.params;
            if (request.url === previewUrl && request.method === 'GET') {
              await cdp.call('Fetch.continueRequest', {requestId}, message.sessionId);
            } else {
              blocked.push({url: request.url, method: request.method});
              await cdp.call('Fetch.failRequest', {requestId, errorReason: 'BlockedByClient'}, message.sessionId);
            }
          } else if (message.method === 'Target.attachedToTarget' && isolated) {
            await guard(message.params.sessionId);
            await cdp.call('Runtime.runIfWaitingForDebugger', {}, message.params.sessionId);
          }
        })().catch(error => protocolErrors.push(error.message));
        pendingEvents.add(work); work.finally(() => pendingEvents.delete(work));
      });
      await cdp.call('Page.enable'); await cdp.call('Runtime.enable');
      if (mode === 'isolated') await guard();
      const observationStart = received.length;
      await cdp.call('Page.navigate', {url: previewUrl});
      let messages = [];
      for (let i = 0; i < 100; i++) {
        const state = await cdp.call('Runtime.evaluate', {expression: 'window.fixtureMessages || []', returnByValue: true});
        messages = state.result.value || [];
        if (messages.some(message => message.attempted === id)) break;
        await delay(25);
      }
      // Finite observation window is reported with the receipt, not a promise
      // that arbitrary creative could not schedule traffic at a later time.
      await delay(500);
      await Promise.all([...pendingEvents]);
      const state = await cdp.call('Runtime.evaluate', {expression: 'window.fixtureMessages || []', returnByValue: true});
      messages = state.result.value || [];
      // Negative control for the assertion itself, sent by this test driver.
      // A run with this flag must fail and retain the unexpected event.
      if (injectCanary && mode === 'isolated' && id === 'fetch-get') {
        await fetch(base + '/events/unexpected-audit-canary');
      }
      const observation = assessNotifications(received.slice(observationStart), {
        isolated, expectedPath: '/events/' + id, expectedMethod,
      });
      const notifications = observation.notifications;
      const attempted = messages.some(message => message.attempted === id);
      const unexpectedScriptError = messages.some(message => message.error && message.error !== 'SecurityError');
      const passed = attempted && !unexpectedScriptError && protocolErrors.length === 0 && observation.passed;
      cases.push({id: id + '/' + mode, passed, attempted, expected_method: expectedMethod,
        server_notifications: notifications, blocked_requests: blocked,
        network_gate_blocks: gateBlocked.slice(), messages,
        protocol_errors: protocolErrors, observation_ms_after_attempt: 500});
      await fetch(endpoint + '/json/close/' + target.id);
      cdp.close(); cdp = null;
    }
  }
  const report = {profile: 'synthetic-browser-inspection-2', browser: browser.Browser,
    assertion_canary_injected: injectCanary,
    tested_at: new Date().toISOString(), passed: cases.filter(item => item.passed).length,
    total: cases.length, cases};
  if (jsonMode) console.log(JSON.stringify(report, null, 2));
  else {
    for (const item of cases) console.log((item.passed ? 'PASS ' : 'FAIL ') + item.id);
    console.log(`${report.passed}/${report.total} synthetic browser cases pass (${browser.Browser})`);
  }
  if (report.passed !== report.total) process.exitCode = 1;
} finally {
  cdp?.close();
  if (chrome && chrome.exitCode === null && chrome.signalCode === null) {
    chrome.kill('SIGTERM');
    await Promise.race([once(chrome, 'exit'), delay(3000)]);
    if (chrome.exitCode === null && chrome.signalCode === null) {
      chrome.kill('SIGKILL'); await once(chrome, 'exit');
    }
  }
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
  gate.closeAllConnections();
  await new Promise(resolve => gate.close(resolve));
  if (profile) await rm(profile, {recursive: true, force: true, maxRetries: 5, retryDelay: 100});
}
