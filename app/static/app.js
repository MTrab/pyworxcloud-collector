
let sessionId = null;

const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const downloadBtn = document.getElementById("download");

function updateButtons() {
  startBtn.disabled = sessionId !== null;
  stopBtn.disabled = sessionId === null;
  downloadBtn.disabled = sessionId !== null;
}

updateButtons();

startBtn.onclick = async () => {
  const res = await fetch("/api/sessions/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email.value,
      password: password.value,
      brand: brand.value
    })
  });
  const data = await res.json();
  sessionId = data.session_id;
  updateButtons();
};

stopBtn.onclick = async () => {
  await fetch(`/api/sessions/${sessionId}/stop`, { method: "POST" });
  updateButtons();
};

downloadBtn.onclick = () => {
  window.location = `/api/sessions/${sessionId}/download`;
  sessionId = null;
  updateButtons();
};
