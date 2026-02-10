
let session = null;
let sessionActive = false;

const consentEl = document.getElementById('consent');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusEl = document.getElementById('status');

function setStatus(msg) {
  statusEl.textContent = msg || '';
}

function updateButtons() {
  const consent = consentEl.checked;
  if (!consent) {
    stopBtn.disabled = true;
    downloadBtn.disabled = true;
    startBtn.disabled = true;
    return;
  }
  startBtn.disabled = sessionActive;
  stopBtn.disabled = !sessionActive;
  downloadBtn.disabled = sessionActive || session === null;
}

consentEl.addEventListener('change', updateButtons);

async function start() {
  setStatus('Starting session...');
  session = null;
  sessionActive = false;
  updateButtons();

  const payload = {
    username: document.getElementById('username').value.trim(),
    password: document.getElementById('password').value,
    brand: document.getElementById('brand').value,
    consent: consentEl.checked,
  };

  let response;
  try {
    response = await fetch('/api/sessions/start', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
  } catch (error) {
    setStatus('Could not start session.');
    updateButtons();
    return;
  }

  let body = {};
  try {
    body = await response.json();
  } catch {
    // ignore – fallback message below
  }

  if (!response.ok) {
    const msg = body.detail || body.error || 'Authentication failed: check credentials.';
    setStatus(msg);
    session = null;
    sessionActive = false;
    updateButtons();
    return;
  }

  session = body.session;
  sessionActive = true;
  setStatus(`Session started: ${session}`);
  updateButtons();
}

async function stop() {
  if (!session) return;
  setStatus('Stopping session...');
  stopBtn.disabled = true;

  const r = await fetch(`/api/sessions/${session}/stop`, {method:'POST'});
  const j = await r.json();
  if (!r.ok) {
    setStatus(j.detail || j.error || 'Could not stop session.');
    stopBtn.disabled = false;
    return;
  }

  setStatus('Session stopped. Ready for download.');
  sessionActive = false;
  startBtn.disabled = false;
  downloadBtn.disabled = false;
}

async function download() {
  if (!session) return;
  window.location = `/api/sessions/${session}/download`;
}

updateButtons();
