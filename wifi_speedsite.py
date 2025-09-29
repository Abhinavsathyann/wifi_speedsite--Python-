from flask import Flask, jsonify, request
import speedtest
import time
import threading

app = Flask(__name__)

# In-memory history storage
test_history = []
HISTORY_LIMIT = 10
SPEEDTEST_TIMEOUT = 120  # seconds

# HTML (frontend) template — contains placeholder "SPEEDTEST_TIMEOUT_VALUE"
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>WiFi Speed Test</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
  <style>
    body {
      background: linear-gradient(135deg, #1e3a8a, #9333ea, #f59e0b);
      background-size: 600% 600%;
      animation: gradientBG 20s ease infinite;
    }
    @keyframes gradientBG {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    .glass {
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      background-color: rgba(255, 255, 255, 0.2);
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.3);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
    }
  </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center text-white">
  <div class="glass p-6 w-11/12 max-w-4xl text-center">
    <h1 class="text-3xl font-bold mb-4">🚀 WiFi Speed Test</h1>
    <svg id="gauge" width="200" height="200" class="mx-auto my-6">
      <circle cx="100" cy="100" r="90" stroke="#444" stroke-width="20" fill="none"/>
      <circle id="progress" cx="100" cy="100" r="90" stroke="#10b981" stroke-width="20" fill="none"
        stroke-dasharray="565" stroke-dashoffset="565" transform="rotate(-90 100 100)" />
      <text id="speedText" x="100" y="110" text-anchor="middle" font-size="24" fill="white">0 Mbps</text>
    </svg>
    <button id="startBtn" class="px-6 py-3 bg-indigo-600 rounded-lg shadow-md hover:bg-indigo-700 transition">
      Start Test
    </button>
    <p id="status" class="mt-4"></p>
    <div class="mt-6">
      <canvas id="historyChart" height="100"></canvas>
    </div>
  </div>

  <script>
    const startBtn = document.getElementById('startBtn');
    const statusEl = document.getElementById('status');
    const speedText = document.getElementById('speedText');
    const progressCircle = document.getElementById('progress');
    const chartCtx = document.getElementById('historyChart').getContext('2d');

    let historyData = [];

    const chart = new Chart(chartCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Download Speed (Mbps)',
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16,185,129,0.2)',
          tension: 0.3,
          fill: true
        }]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });

    function animateGauge(value) {
      const maxVal = 200; // scale for gauge
      const offset = 565 - (565 * Math.min(value, maxVal) / maxVal);
      anime({ targets: progressCircle, strokeDashoffset: offset, duration: 1000, easing: 'easeInOutQuad' });
      speedText.textContent = value.toFixed(2) + " Mbps";
    }

    startBtn.addEventListener('click', () => {
      statusEl.textContent = "Running test...";
      startBtn.disabled = true;

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), SPEEDTEST_TIMEOUT_VALUE * 1000);

      fetch('/api/speedtest', { method: 'POST', signal: controller.signal })
        .then(res => res.json())
        .then(data => {
          clearTimeout(timeout);
          startBtn.disabled = false;
          if (data.error) {
            statusEl.textContent = "❌ Error: " + data.error;
          } else {
            statusEl.textContent = `✅ Ping: ${data.ping.toFixed(0)} ms | Download: ${data.download.toFixed(2)} Mbps | Upload: ${data.upload.toFixed(2)} Mbps`;
            animateGauge(data.download);
            const now = new Date().toLocaleTimeString();
            historyData.push({ time: now, speed: data.download });
            if (historyData.length > 10) historyData.shift();
            chart.data.labels = historyData.map(d => d.time);
            chart.data.datasets[0].data = historyData.map(d => d.speed);
            chart.update();
          }
        })
        .catch(err => {
          startBtn.disabled = false;
          statusEl.textContent = "❌ Request failed: " + err.message;
        });
    });
  </script>
</body>
</html>
"""

# Replace placeholder with actual timeout value
INDEX_HTML = INDEX_HTML.replace("SPEEDTEST_TIMEOUT_VALUE", str(SPEEDTEST_TIMEOUT))

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
