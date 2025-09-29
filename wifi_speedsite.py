"""
Advanced Flask-based Internet Speed Test Website
File: wifi_speedsite.py
Requirements:
  pip install flask speedtest-cli

Run:
  python wifi_speedsite.py
  Open http://127.0.0.1:5000 in your browser

Features:
  - Modern responsive UI with TailwindCSS (via CDN)
  - Dark/light theme toggle
  - Speed test: ping, download, upload
  - History of previous tests stored in memory (or JSON file)
  - Results displayed in cards + line chart for history (Chart.js)
  - Run multiple tests and compare
  - Clear history button

Notes:
  - For production, replace in-memory storage with database.
  - Running speedtest may take 10–40 seconds.

"""

from flask import Flask, render_template_string, jsonify, request
import speedtest
import time
import datetime

app = Flask(__name__)

# In-memory history storage
HISTORY = []

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Advanced WiFi Speed Test</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100 transition-colors">
  <div class="max-w-2xl mx-auto p-6">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">🚀 Wi-Fi Internet Speed Test</h1>
      <button id="themeToggle" class="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700">🌙</button>
    </div>

    <p class="text-sm text-gray-600 dark:text-gray-400 mb-6">Check ping, download and upload speeds using Speedtest.net servers. Your past results will be saved locally.</p>

    <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 mb-6 text-center">
      <button id="startBtn" class="bg-blue-600 text-white px-5 py-2 rounded-lg font-semibold hover:bg-blue-700">Start Test</button>
      <div id="running" class="mt-4 hidden">
        <div class="mx-auto animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="text-sm mt-2">Running test… please wait</p>
      </div>
      <div id="error" class="mt-2 text-red-500 hidden"></div>
    </div>

    <div id="result" class="hidden">
      <div class="grid grid-cols-3 gap-4 text-center">
        <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="text-xs text-gray-500">Ping</div>
          <div id="ping" class="text-lg font-bold">—</div>
        </div>
        <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="text-xs text-gray-500">Download</div>
          <div id="download" class="text-lg font-bold">—</div>
        </div>
        <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="text-xs text-gray-500">Upload</div>
          <div id="upload" class="text-lg font-bold">—</div>
        </div>
      </div>
      <p class="text-xs mt-2 text-gray-500" id="serverInfo"></p>
    </div>

    <div class="mt-6">
      <canvas id="historyChart" class="w-full h-64"></canvas>
    </div>

    <div class="mt-4 flex justify-end gap-2">
      <button id="againBtn" class="hidden bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">Run Again</button>
      <button id="clearBtn" class="hidden bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">Clear History</button>
    </div>
  </div>

<script>
const startBtn = document.getElementById('startBtn')
const againBtn = document.getElementById('againBtn')
const running = document.getElementById('running')
const result = document.getElementById('result')
const errorBox = document.getElementById('error')
const clearBtn = document.getElementById('clearBtn')

let historyChart;

startBtn.addEventListener('click', runTest)
againBtn.addEventListener('click', runTest)
clearBtn.addEventListener('click', clearHistory)

// Theme toggle
document.getElementById('themeToggle').addEventListener('click',()=>{
  document.body.classList.toggle('dark')
})

async function runTest(){
  errorBox.classList.add('hidden')
  result.classList.add('hidden')
  startBtn.disabled = true
  running.classList.remove('hidden')

  try{
    const resp = await fetch('/run_test', {method:'POST'})
    if(!resp.ok) throw new Error('Network response not ok')
    const json = await resp.json()
    if(json.error) throw new Error(json.error)

    document.getElementById('ping').innerText = json.ping + ' ms'
    document.getElementById('download').innerText = json.download_mbps.toFixed(2) + ' Mbps'
    document.getElementById('upload').innerText = json.upload_mbps.toFixed(2) + ' Mbps'
    document.getElementById('serverInfo').innerText = json.server || ''

    result.classList.remove('hidden')
    againBtn.classList.remove('hidden')
    clearBtn.classList.remove('hidden')

    updateChart(json)
  } catch(err){
    errorBox.innerText = 'Error: ' + err.message
    errorBox.classList.remove('hidden')
  } finally{
    running.classList.add('hidden')
    startBtn.disabled = false
  }
}

async function clearHistory(){
  await fetch('/clear_history',{method:'POST'})
  if(historyChart){
    historyChart.data.labels=[]
    historyChart.data.datasets.forEach(ds=>ds.data=[])
    historyChart.update()
  }
}

function updateChart(data){
  if(!historyChart){
    const ctx=document.getElementById('historyChart')
    historyChart=new Chart(ctx,{
      type:'line',
      data:{
        labels:[data.timestamp],
        datasets:[
          {label:'Download (Mbps)',data:[data.download_mbps],borderColor:'blue'},
          {label:'Upload (Mbps)',data:[data.upload_mbps],borderColor:'green'},
          {label:'Ping (ms)',data:[data.ping],borderColor:'red'}
        ]
      },
      options:{responsive:true,maintainAspectRatio:false}
    })
  } else {
    historyChart.data.labels.push(data.timestamp)
    historyChart.data.datasets[0].data.push(data.download_mbps)
    historyChart.data.datasets[1].data.push(data.upload_mbps)
    historyChart.data.datasets[2].data.push(data.ping)
    historyChart.update()
  }
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/run_test', methods=['POST'])
def run_test():
    try:
        t0 = time.time()
        s = speedtest.Speedtest()
        s.get_best_server()
        download_bps = s.download()
        upload_bps = s.upload()
        results = s.results.dict()

        download_mbps = float(download_bps)/1_000_000
        upload_mbps = float(upload_bps)/1_000_000
        ping = results.get('ping', None)
        server = results.get('server', {})
        server_info=None
        if server:
            name=server.get('name')
            country=server.get('country')
            sponsor=server.get('sponsor')
            server_info=f"{sponsor} — {name}, {country}"

        elapsed=time.time()-t0
        timestamp=datetime.datetime.now().strftime('%H:%M:%S')

        entry={
            'ping': round(ping,2) if ping is not None else None,
            'download_mbps': round(download_mbps,2),
            'upload_mbps': round(upload_mbps,2),
            'server': server_info,
            'elapsed_seconds': round(elapsed,2),
            'timestamp': timestamp
        }
        HISTORY.append(entry)

        return jsonify(entry)
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    HISTORY.clear()
    return jsonify({'status':'cleared'})

if __name__ == '__main__':
    app.run(debug=True)
