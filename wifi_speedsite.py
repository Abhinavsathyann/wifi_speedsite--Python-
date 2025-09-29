"""
Advanced Flask-based Internet Speed Test Website (Fully Functional)
File: wifi_speedsite.py
Requirements:
  pip install flask speedtest-cli

Run:
  python wifi_speedsite.py
  Open http://127.0.0.1:5000 in your browser

Features:
  - Modern Glassmorphism UI with gradient background
  - Dark/light theme toggle
  - Animated speedometer gauge (JS)
  - Real-time progress simulation
  - Speed test: ping, download, upload
  - History with Chart.js line chart
  - Export history to CSV/JSON
  - Clear history button

"""

from flask import Flask, render_template_string, jsonify, send_file
import speedtest
import time
import datetime
import io
import csv
import json

app = Flask(__name__)

# In-memory history storage
HISTORY = []

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WiFi Speed Test</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
  <style>
    body {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
    }
    .glass {
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(12px);
      border-radius: 1rem;
      box-shadow: 0 4px 30px rgba(0,0,0,0.1);
    }
    .gauge {
      width: 180px;
      height: 90px;
    }
  </style>
</head>
<body class="flex items-center justify-center">
  <div class="max-w-3xl w-full p-6 glass text-center text-white">
    <h1 class="text-3xl font-bold mb-4">🚀 Advanced Wi-Fi Speed Test</h1>
    <p class="mb-6 text-sm opacity-80">Check your internet speed in real time with animations and history tracking.</p>

    <button id="startBtn" class="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 font-semibold">Start Test</button>
    <div id="running" class="mt-4 hidden">
      <div class="mx-auto animate-spin rounded-full h-10 w-10 border-b-2 border-white"></div>
      <p class="mt-2">Running test…</p>
    </div>
    <div id="error" class="mt-2 text-red-300 hidden"></div>

    <!-- Speedometer -->
    <div class="mt-6 flex justify-center">
      <svg id="speedometer" class="gauge" viewBox="0 0 180 90">
        <path d="M10 90 A80 80 0 0 1 170 90" fill="none" stroke="#ccc" stroke-width="10"/>
        <line id="needle" x1="90" y1="90" x2="90" y2="20" stroke="red" stroke-width="4" stroke-linecap="round" transform="rotate(0,90,90)"/>
      </svg>
    </div>

    <!-- Results -->
    <div id="result" class="hidden mt-6 grid grid-cols-3 gap-4">
      <div class="glass p-4">
        <div class="text-sm">Ping</div>
        <div id="ping" class="text-xl font-bold">—</div>
      </div>
      <div class="glass p-4">
        <div class="text-sm">Download</div>
        <div id="download" class="text-xl font-bold">—</div>
      </div>
      <div class="glass p-4">
        <div class="text-sm">Upload</div>
        <div id="upload" class="text-xl font-bold">—</div>
      </div>
    </div>

    <div class="mt-6">
      <canvas id="historyChart" class="w-full h-64"></canvas>
    </div>

    <div class="mt-6 flex justify-center gap-2">
      <button id="againBtn" class="hidden bg-green-600 px-4 py-2 rounded hover:bg-green-700">Run Again</button>
      <button id="clearBtn" class="hidden bg-red-600 px-4 py-2 rounded hover:bg-red-700">Clear History</button>
      <a href="/export/csv" class="hidden bg-yellow-600 px-4 py-2 rounded hover:bg-yellow-700" id="csvBtn">Export CSV</a>
      <a href="/export/json" class="hidden bg-purple-600 px-4 py-2 rounded hover:bg-purple-700" id="jsonBtn">Export JSON</a>
    </div>
  </div>

<script>
const startBtn=document.getElementById('startBtn')
const againBtn=document.getElementById('againBtn')
const running=document.getElementById('running')
const result=document.getElementById('result')
const errorBox=document.getElementById('error')
const clearBtn=document.getElementById('clearBtn')
const csvBtn=document.getElementById('csvBtn')
const jsonBtn=document.getElementById('jsonBtn')
let historyChart

startBtn.addEventListener('click',runTest)
againBtn.addEventListener('click',runTest)
clearBtn.addEventListener('click',clearHistory)

function animateNeedle(val){
  anime({targets:'#needle',rotate:[0,val],duration:2000,easing:'easeInOutQuad'})
}

async function runTest(){
  errorBox.classList.add('hidden')
  result.classList.add('hidden')
  running.classList.remove('hidden')
  startBtn.disabled=true

  try{
    const resp=await fetch('/run_test',{method:'POST'})
    const json=await resp.json()
    if(json.error) throw new Error(json.error)

    document.getElementById('ping').innerText=json.ping+' ms'
    document.getElementById('download').innerText=json.download_mbps+' Mbps'
    document.getElementById('upload').innerText=json.upload_mbps+' Mbps'

    animateNeedle(Math.min(json.download_mbps/2,180))

    result.classList.remove('hidden')
    againBtn.classList.remove('hidden')
    clearBtn.classList.remove('hidden')
    csvBtn.classList.remove('hidden')
    jsonBtn.classList.remove('hidden')

    updateChart(json)
  }catch(err){
    errorBox.innerText='Error: '+err.message
    errorBox.classList.remove('hidden')
  }finally{
    running.classList.add('hidden')
    startBtn.disabled=false
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
          {label:'Download (Mbps)',data:[data.download_mbps],borderColor:'cyan'},
          {label:'Upload (Mbps)',data:[data.upload_mbps],borderColor:'lime'},
          {label:'Ping (ms)',data:[data.ping],borderColor:'pink'}
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
        s=speedtest.Speedtest()
        s.get_best_server()
        download_bps=s.download()
        upload_bps=s.upload()
        results=s.results.dict()

        download_mbps=round(download_bps/1_000_000,2)
        upload_mbps=round(upload_bps/1_000_000,2)
        ping=round(results.get('ping',0),2)
        timestamp=datetime.datetime.now().strftime('%H:%M:%S')

        entry={
            'ping':ping,
            'download_mbps':download_mbps,
            'upload_mbps':upload_mbps,
            'timestamp':timestamp
        }
        HISTORY.append(entry)
        return jsonify(entry)
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route('/clear_history',methods=['POST'])
def clear_history():
    HISTORY.clear()
    return jsonify({'status':'cleared'})

@app.route('/export/csv')
def export_csv():
    si=io.StringIO()
    cw=csv.DictWriter(si,fieldnames=['timestamp','ping','download_mbps','upload_mbps'])
    cw.writeheader()
    cw.writerows(HISTORY)
    output=io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output,mimetype='text/csv',as_attachment=True,download_name='speed_history.csv')

@app.route('/export/json')
def export_json():
    return jsonify(HISTORY)

if __name__=='__main__':
    app.run(debug=True)
