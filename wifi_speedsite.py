from flask import Flask, jsonify, request
import speedtest
import threading

app = Flask(__name__)

# In-memory history storage
test_history = []
HISTORY_LIMIT = 10
SPEEDTEST_TIMEOUT = 120  # seconds

# ----------------- FRONTEND TEMPLATE -----------------
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🚀 Advanced WiFi Speed Test</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
  <style>
    body {
      background-color: #ffffff;
      color: #111827;
    }
    .glass {
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      background-color: rgba(255, 255, 255, 0.9);
      border-radius: 20px;
      border: 1px solid rgba(0, 0, 0, 0.1);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    .flip-card { perspective: 1000px; }
    .flip-card-inner {
      transition: transform 0.8s;
      transform-style: preserve-3d;
    }
    .flip-card:hover .flip-card-inner { transform: rotateY(180deg); }
    .flip-card-front, .flip-card-back {
      position: absolute;
      width: 100%;
      height: 100%;
      backface-visibility: hidden;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.25rem; font-weight: bold;
    }
    .flip-card-back { transform: rotateY(180deg); }
  </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center">
  <div class="glass p-6 w-11/12 max-w-5xl text-center">
    <h1 class="text-4xl font-extrabold mb-4">🚀 Advanced WiFi Speed Test</h1>
    
    <!-- Animated Gauge -->
    <svg id="gauge" width="220" height="220" class="mx-auto my-6">
      <circle cx="110" cy="110" r="100" stroke="#ddd" stroke-width="20" fill="none"/>
      <circle id="progress" cx="110" cy="110" r="100" stroke="#10b981" stroke-width="20" fill="none"
        stroke-dasharray="628" stroke-dashoffset="628" transform="rotate(-90 110 110)" />
      <text id="speedText" x="110" y="120" text-anchor="middle" font-size="26" fill="#111827">0 Mbps</text>
    </svg>

    <button id="startBtn" class="px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md hover:bg-indigo-700 transition">
      ▶ Start Test
    </button>
    <p id="status" class="mt-4"></p>

    <!-- Result Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
      <div class="flip-card h-32">
        <div class="flip-card-inner relative h-full glass">
          <div class="flip-card-front">Ping</div>
          <div class="flip-card-back" id="pingVal">0 ms</div>
        </div>
      </div>
      <div class="flip-card h-32">
        <div class="flip-card-inner relative h-full glass">
          <div class="flip-card-front">Download</div>
          <div class="flip-card-back" id="downloadVal">0 Mbps</div>
        </div>
      </div>
      <div class="flip-card h-32">
        <div class="flip-card-inner relative h-full glass">
          <div class="flip-card-front">Upload</div>
          <div class="flip-card-back" id="uploadVal">0 Mbps</div>
        </div>
      </div>
    </div>

    <!-- Chart -->
    <div class="mt-6 glass p-4">
      <div class="flex justify-between">
        <h2 class="text-lg font-bold">History</h2>
        <div>
          <button id="exportCSV" class="px-2 py-1 bg-green-600 text-white rounded">⬇ CSV</button>
          <button id="exportJSON" class="px-2 py-1 bg-blue-600 text-white rounded">⬇ JSON</button>
        </div>
      </div>
      <canvas id="historyChart" height="120"></canvas>
    </div>
  </div>

  <script>
    const startBtn = document.getElementById('startBtn');
    const statusEl = document.getElementById('status');
    const speedText = document.getElementById('speedText');
    const progressCircle = document.getElementById('progress');
    const chartCtx = document.getElementById('historyChart').getContext('2d');
    const pingVal = document.getElementById('pingVal');
    const downloadVal = document.getElementById('downloadVal');
    const uploadVal = document.getElementById('uploadVal');

    let historyData = [];

    const chart = new Chart(chartCtx, {
      type: 'line',
      data: { labels: [], datasets: [
        { label: 'Download (Mbps)', data: [], borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.2)', fill: true, tension: 0.3 },
        { label: 'Upload (Mbps)', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.2)', fill: true, tension: 0.3 }
      ]},
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });

    function animateGauge(value) {
      const maxVal = 200;
      const offset = 628 - (628 * Math.min(value, maxVal) / maxVal);
      anime({ targets: progressCircle, strokeDashoffset: offset, duration: 1000, easing: 'easeInOutQuad' });
      speedText.textContent = value.toFixed(2) + " Mbps";
    }

    function updateResults(data) {
      pingVal.textContent = data.ping.toFixed(0) + " ms";
      downloadVal.textContent = data.download.toFixed(2) + " Mbps";
      uploadVal.textContent = data.upload.toFixed(2) + " Mbps";
      animateGauge(data.download);

      const now = new Date().toLocaleTimeString();
      historyData.push({ time: now, download: data.download, upload: data.upload });
      if (historyData.length > 10) historyData.shift();

      chart.data.labels = historyData.map(d => d.time);
      chart.data.datasets[0].data = historyData.map(d => d.download);
      chart.data.datasets[1].data = historyData.map(d => d.upload);
      chart.update();
    }

    startBtn.addEventListener('click', () => {
      statusEl.textContent = "Running test...";
      startBtn.disabled = true;
      fetch('/api/speedtest', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
          startBtn.disabled = false;
          if (data.error) statusEl.textContent = "❌ Error: " + data.error;
          else {
            statusEl.textContent = "✅ Test Completed!";
            updateResults(data);
          }
        })
        .catch(err => { statusEl.textContent = "❌ Failed: " + err.message; startBtn.disabled = false; });
    });

    document.getElementById('exportCSV').addEventListener('click', () => {
      let csv = "Time,Download,Upload\\n";
      historyData.forEach(d => csv += `${d.time},${d.download},${d.upload}\\n`);
      let blob = new Blob([csv], { type: 'text/csv' });
      let url = URL.createObjectURL(blob);
      let a = document.createElement('a'); a.href = url; a.download = "speedtest.csv"; a.click();
    });

    document.getElementById('exportJSON').addEventListener('click', () => {
      let blob = new Blob([JSON.stringify(historyData, null, 2)], { type: 'application/json' });
      let url = URL.createObjectURL(blob);
      let a = document.createElement('a'); a.href = url; a.download = "speedtest.json"; a.click();
    });
  </script>
</body>
</html>
"""

# ----------------- BACKEND -----------------
@app.route("/")
def index():
    return INDEX_HTML

@app.route("/api/speedtest", methods=["POST"])
def run_speedtest():
    result = {}

    def do_test():
        nonlocal result
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            ping = st.results.ping
            result = {"ping": ping, "download": download, "upload": upload}
        except Exception as e:
            result = {"error": str(e)}

    thread = threading.Thread(target=do_test)
    thread.start()
    thread.join(timeout=SPEEDTEST_TIMEOUT)

    if thread.is_alive():
        result = {"error": "Speedtest timed out."}

    if "error" not in result:
        test_history.append(result)
        if len(test_history) > HISTORY_LIMIT:
            test_history.pop(0)

    return jsonify(result)

@app.route("/api/history")
def history():
    return jsonify(test_history)

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
