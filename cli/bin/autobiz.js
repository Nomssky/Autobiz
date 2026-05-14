#!/usr/bin/env node
/**
 * AutoBiz CLI — Cross-platform AI Business Builder
 * Usage: autobiz [idea] [options]
 *        autobiz                   → Interactive mode
 *        autobiz "my idea"         → Quick create
 *        autobiz --web             → Open web dashboard
 *        autobiz --help            → Show help
 */

const http = require('http');
const { spawn, execSync } = require('child_process');
const { existsSync, readFileSync, mkdirSync, realpathSync } = require('fs');
const { join, dirname } = require('path');
const os = require('os');
const readline = require('readline');

const PKG = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'));
const VERSION = PKG.version;
const API_URL = process.env.AUTOBIZ_API_URL || 'http://localhost:8000/api/v1';
const WEB_URL = process.env.AUTOBIZ_WEB_URL || 'http://localhost:3000';

// Auto-detect project root (resolve symlinks for global install)
const PKG_DIR = realpathSync(join(__dirname, '..'));
function findBackend(from) {
  for (let i = 0; i < 5; i++) {
    const candidate = join(from, 'backend', 'app', 'main.py');
    if (existsSync(candidate)) return join(from, 'backend');
    from = join(from, '..');
  }
  return null;
}
const BACKEND_DIR = process.env.AUTOBIZ_BACKEND_DIR
  ? join(process.env.AUTOBIZ_BACKEND_DIR)
  : findBackend(PKG_DIR);

const AUTOBIZ_DIR = join(os.homedir(), '.autobiz');
const VENV_DIR = join(AUTOBIZ_DIR, 'venv');
const REQS_PATH = BACKEND_DIR ? join(BACKEND_DIR, 'requirements.txt') : null;

let pc;
try { pc = require('picocolors'); } catch {
  pc = { bold: s => s, dim: s => s, green: s => s, red: s => s, yellow: s => s, cyan: s => s, gray: s => s };
}

// ─── Spinner ──────────────────────────────────────────

function createSpinner(text) {
  const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  let i = 0;
  const interval = setInterval(() => {
    process.stdout.write(`\r  ${frames[i]} ${text}`);
    i = (i + 1) % frames.length;
  }, 100);
  return {
    stop(msg) { clearInterval(interval); process.stdout.write(`\r  ${pc.green('✓')} ${msg || text}\n`); },
    fail(msg) { clearInterval(interval); process.stdout.write(`\r  ${pc.red('✗')} ${msg || text}\n`); },
  };
}

// ─── Auto Venv ────────────────────────────────────────

function ensurePython() {
  const names = process.platform === 'win32'
    ? ['python', 'python', 'py']
    : ['python', 'python3'];

  for (const name of names) {
    try {
      const r = execSync(`${name} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`, { stdio: 'pipe', encoding: 'utf-8' });
      const ver = r.trim();
      if (ver && parseFloat(ver) >= 3.9) return name;
    } catch (e) {
      continue;
    }
  }

  // Last resort: try `python --version` directly
  try {
    execSync('python --version', { stdio: 'pipe' });
    return 'python';
  } catch {}

  throw new Error(
    'Python 3.9+ is required.\n' +
    '  Download from: https://www.python.org/downloads/\n' +
    '  Make sure Python is in your PATH.'
  );
}

function ensureVenv(python) {
  const pip = process.platform === 'win32'
    ? join(VENV_DIR, 'Scripts', 'pip')
    : join(VENV_DIR, 'bin', 'pip');
  const py = process.platform === 'win32'
    ? join(VENV_DIR, 'Scripts', 'python')
    : join(VENV_DIR, 'bin', 'python');

  // Create venv if not exists
  if (!existsSync(py)) {
    const s = createSpinner('Creating Python virtual environment...');
    mkdirSync(AUTOBIZ_DIR, { recursive: true });
    execSync(`${python} -m venv ${VENV_DIR}`, { stdio: 'pipe' });
    s.stop('Virtual environment created');
  }

  // Install requirements if not yet
  const marker = join(VENV_DIR, '.installed');
  if (!existsSync(marker) && REQS_PATH) {
    const s = createSpinner('Installing backend dependencies (first run)...');
    execSync(`${pip} install -r ${REQS_PATH}`, { stdio: 'pipe', cwd: BACKEND_DIR, env: { ...process.env, PIP_NO_INPUT: '1' } });
    // Mark installed
    try {
      readFileSync(REQS_PATH).toString().split('\n').sort().join('\n');
      execSync(`echo "installed" > "${marker}"`);
    } catch {}
    s.stop('Dependencies installed');
  }

  return { python: py, pip };
}

// ─── Helpers ──────────────────────────────────────────

function httpRequest(method, path, body, token) {
  return new Promise((resolve, reject) => {
    const url = new URL(API_URL + path);
    const opts = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method,
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000,
    };
    if (token) opts.headers['Authorization'] = `Bearer ${token}`;

    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, data }); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timed out')); });
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function rlQuestion(query) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => rl.question(query, a => { rl.close(); resolve(a); }));
}

function rlPassword(query) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
  return new Promise(resolve => {
    rl.question(query, a => { rl.close(); resolve(a); });
    if (rl.terminal && process.stdin.setRawMode) {
      const stdin = process.stdin;
      const onData = c => {
        const str = String(c);
        if (str === '\x03') { rl.close(); process.exit(0); }
        if (str === '\x7f') rl.line = rl.line.slice(0, -1);
        else if (str.length === 1) rl.line += str;
        rl._refreshLine();
      };
      stdin.on('data', onData);
      rl.on('close', () => stdin.removeListener('data', onData));
    }
  });
}

function isBackendRunning() {
  return new Promise(resolve => {
    const req = http.get('http://localhost:8000/health', { timeout: 2000 }, res => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

function startBackend() {
  return new Promise(async (resolve, reject) => {
    if (await isBackendRunning()) return resolve();

    // Try Docker
    try {
      execSync('docker compose ps 2>/dev/null', { cwd: PROJECT_ROOT, stdio: 'pipe' });
      log(`Starting backend with Docker...`, 'dim');
      execSync('docker compose up -d', { cwd: PROJECT_ROOT, stdio: 'pipe' });
      await waitForBackend(60, resolve, reject);
      return;
    } catch {}

    // No Docker — use auto venv
    if (!BACKEND_DIR) {
      reject(new Error(
        'Backend not found. Clone the repo:\n' +
        '  git clone https://github.com/Nomssky/Autobiz.git\n' +
        '  cd Autobiz/cli && npm link\n' +
        'Or use Docker: docker compose up -d'
      ));
      return;
    }

    try {
      const python = ensurePython();
      const venv = ensureVenv(python);
      log(`Starting backend with SQLite (dev mode)...`, 'dim');

      const proc = spawn(venv.python, ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], {
        cwd: BACKEND_DIR,
        stdio: 'pipe',
        env: {
          ...process.env,
          PYTHONPATH: BACKEND_DIR,
          DEBUG: 'true',
          DATABASE_URL: 'sqlite:///./data.db',
        },
      });
      proc.stdout.on('data', () => {});
      proc.stderr.on('data', () => {});

      process.on('exit', () => { try { proc.kill(); } catch {} });

      await waitForBackend(60, resolve, reject);
    } catch (e) {
      reject(e);
    }
  });
}

function waitForBackend(timeoutSec, resolve, reject) {
  const start = Date.now();
  const check = async () => {
    if (await isBackendRunning()) return resolve();
    if (Date.now() - start > timeoutSec * 1000) {
      return reject(new Error('Backend start timeout'));
    }
    setTimeout(check, 1500);
  };
  check();
}

// ─── Logging ──────────────────────────────────────────

function log(msg, style = '') {
  if (style && pc[style]) msg = pc[style](msg);
  console.log(`  ${msg}`);
}

function success(msg) { log(pc.green('✓') + ' ' + msg); }
function error(msg) { log(pc.red('✗') + ' ' + msg); }
function info(msg) { log(pc.dim('ℹ') + ' ' + msg); }
function header(title) {
  const line = '─'.repeat(Math.min(title.length + 4, 48));
  console.log(`\n  ${pc.bold(pc.cyan(title))}`);
  console.log(`  ${pc.dim(line)}`);
}

// ─── Main ─────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const idea = args.find(a => !a.startsWith('-'));
  const flags = args.filter(a => a.startsWith('-'));

  if (flags.includes('--help') || flags.includes('-h')) return showHelp();
  if (flags.includes('--version') || flags.includes('-v')) return console.log(VERSION);
  if (flags.includes('--web') || flags.includes('-w')) return webMode();

  if (idea) return quickMode(idea);
  return interactiveMode();
}

function showHelp() {
  console.log(pc.bold(`
  ╔══════════════════════════════════════╗
  ║       AutoBiz Engine CLI v${VERSION.padEnd(6)}║
  ╚══════════════════════════════════════╝
  `));
  console.log(`  ${pc.bold('Usage:')}`);
  console.log(`    ${pc.cyan('autobiz')}              Interactive mode`);
  console.log(`    ${pc.cyan('autobiz "idea"')}       Quick create business`);
  console.log(`    ${pc.cyan('autobiz --web')}        Open web dashboard`);
  console.log(`    ${pc.cyan('autobiz --help')}       Show this help`);
  console.log(``);
  console.log(`  ${pc.bold('Examples:')}`);
  console.log(`    ${pc.dim('# Create a business from your idea')}`);
  console.log(`    autobiz "AI-powered e-commerce platform"\n`);
}

async function webMode() {
  try { await startBackend(); } catch (e) { error(e.message); return; }
  console.log(`\n  ${pc.green('🌐  Web Dashboard:')} ${pc.bold(WEB_URL)}`);
  console.log(`  ${pc.dim(`📡  API: ${API_URL}`)}\n`);
  const url = WEB_URL;

  try {
    const platform = process.platform;
    if (platform === 'darwin') execSync(`open "${url}"`, { stdio: 'pipe' });
    else if (platform === 'win32') execSync(`start "" "${url}"`, { stdio: 'pipe' });
    else execSync(`xdg-open "${url}" 2>/dev/null || sensible-browser "${url}"`, { stdio: 'pipe' });
  } catch {
    console.log(`  ${pc.yellow('  Open the URL in your browser.')}`);
  }
}

async function quickMode(idea) {
  console.log(`\n  ${pc.bold('AutoBiz Engine')} — ${pc.dim(VERSION)}\n`);

  try { await startBackend(); } catch (e) { error(e.message); return; }

  const token = await loginFlow();
  if (!token) return;

  const biz = await httpRequest('POST', '/businesses/create', { idea }, token);
  if (biz.status !== 201) { error(biz.data.detail || 'Failed'); return; }

  success(`Created: ${pc.bold(biz.data.name)}`);
  await streamProgress(token, biz.data.id);
}

async function interactiveMode() {
  console.log(`\n  ${pc.bold('AutoBiz Engine')} — ${pc.dim(VERSION)}\n`);

  try { await startBackend(); } catch (e) { error(e.message); return; }

  const token = await loginFlow();
  if (!token) return;

  while (true) {
    header('Menu');
    console.log(`  ${pc.bold('1)')}  Create Business`);
    console.log(`  ${pc.bold('2)')}  List Businesses`);
    console.log(`  ${pc.bold('3)')}  Pending Approvals`);
    console.log(`  ${pc.bold('4)')}  Web Dashboard`);
    console.log(`  ${pc.bold('5)')}  Exit\n`);

    const ans = (await rlQuestion(`  ${pc.dim('Choose (1-5):')} `)).trim();

    if (ans === '1') {
      const idea = (await rlQuestion(`  ${pc.dim('Your business idea:')} `)).trim();
      if (!idea) continue;
      log(`Processing...`, 'dim');
      const biz = await httpRequest('POST', '/businesses/create', { idea }, token);
      if (biz.status !== 201) { error(biz.data.detail || 'Failed'); continue; }
      success(`Created: ${pc.bold(biz.data.name)}`);
      await streamProgress(token, biz.data.id);
    }

    else if (ans === '2') {
      const resp = await httpRequest('GET', '/businesses/', null, token);
      if (resp.status === 200) {
        const list = resp.data;
        if (!list.length) { info('No businesses yet'); continue; }
        for (const b of list) {
          console.log(`  ${pc.cyan(b.name.padEnd(40))} ${pc.dim(b.status.padEnd(12))} ${b.current_phase}`);
        }
      }
    }

    else if (ans === '3') {
      const resp = await httpRequest('GET', '/approvals/pending', null, token);
      if (resp.status === 200) {
        const list = resp.data;
        if (!list.length) { info('No pending approvals'); continue; }
        for (const a of list) {
          console.log(`  ${pc.yellow('⏳')} ${a.title.padEnd(40)} ${pc.dim(a.urgency.padEnd(8))} ${a.id.slice(0, 8)}`);
        }
      }
    }

    else if (ans === '4') { await webMode(); }

    else if (ans === '5' || ans === '') {
      console.log(`\n  ${pc.green('Goodbye!')}\n`);
      process.exit(0);
    }
  }
}

async function loginFlow() {
  const ans = (await rlQuestion(`  ${pc.dim('Already have an account? (y/n):')} `)).trim().toLowerCase();
  let token;

  if (ans === 'y') {
    const email = (await rlQuestion(`  ${pc.dim('Email:')} `)).trim();
    const pass = (await rlPassword(`  ${pc.dim('Password:')} `));
    const resp = await httpRequest('POST', '/auth/login', { email, password: pass });
    if (resp.status !== 200) { error(resp.data.detail || 'Login failed'); return loginFlow(); }
    token = resp.data.access_token;
    success(`Logged in as ${email}`);
  } else {
    const email = (await rlQuestion(`  ${pc.dim('Email:')} `)).trim() || `user${Date.now()}@test.com`;
    const pass = (await rlPassword(`  ${pc.dim('Password:')} `)) || 'test123';
    const name = (await rlQuestion(`  ${pc.dim('Name:')} `)).trim() || 'Test User';
    log(`Registering...`, 'dim');
    const resp = await httpRequest('POST', '/auth/register', { email, password: pass, name });
    if (resp.status !== 201) { error(resp.data.detail || 'Registration failed'); return loginFlow(); }
    token = resp.data.access_token;
    success(`Registered as ${resp.data.email}`);
  }
  return token;
}

async function streamProgress(token, businessId) {
  const done = new Set();
  log(`Tracking agents...`, 'dim');

  for (let i = 0; i < 30; i++) {
    const resp = await httpRequest('GET', `/businesses/${businessId}/timeline`, null, token);
    if (resp.status !== 200) break;

    const phases = resp.data.phases || [];
    let hasNew = false;

    for (const p of phases) {
      if (p.status === 'completed' && !done.has(p.task_type)) {
        success(`${p.role_name} — ${p.task_type}`);
        done.add(p.task_type);
        hasNew = true;
      }
      if (p.status === 'failed') {
        error(`${p.role_name} — ${p.task_type}`);
        done.add(p.task_type);
        hasNew = true;
      }
    }

    if (done.size >= phases.length && phases.length > 0) {
      console.log(`  ${pc.green('─'.repeat(40))}`);
      success(pc.bold(`All ${done.size} agents finished`));
      return;
    }

    if (!hasNew) {
      const pending = phases.length - done.size;
      process.stdout.write(`\r  ${pc.dim(`Waiting for ${pending} agent(s)...`)}`);
    }
    await sleep(3000);
  }
  console.log();
  info(`Business ID: ${businessId}`);
}

main().catch(e => {
  error(e.message);
  process.exit(1);
});
