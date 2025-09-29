from flask import Flask, render_template_string, jsonify, request, send_file
import speedtest
import time
import datetime
import io
import csv

app = Flask(__name__)

# Server-side in-memory history
HISTORY = []

INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>NetPulse — Advanced WiFi Speed Test</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://unpkg.com/animejs@3.2.1/lib/anime.min.js"></script>
  <style>
    /* Dynamic gradient background */
    :root{--card-bg:rgba(255,255,255,0.06)}
    body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial;min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0f172a 0%,#001e3c 50%,#07113a 100%);}
    .container{width:100%;max-width:1100px;padding:28px}
    .glass{backdrop-filter: blur(10px) saturate(120%);background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));border-radius:16px;padding:18px;color:#e6eef8;box-shadow:0 10px 30px rgba(2,6,23,0.6);border:1px solid rgba(255,255,255,0.04)}
    .brand{display:flex;align-items:center;gap:12px}
    .logo{width:48px;height:48px;border-radius:12px;background:linear-gradient(45deg,#06b6d4,#7c3aed);display:flex;align-items:center;justify-content:center;font-weight:700;box-shadow:0 6px 18px rgba(124,58,237,0.18)}
    .small{font-size:13px;color:rgba(230,238,248,0.8)}
    .muted{color:rgba(230,238,248,0.6)}
    .btn{cursor:pointer;padding:10px 14px;border-radius:12px;font-weight:600}
    .btn-primary{background:linear-gradient(90deg,#06b6d4,#7c3aed);color:#021027}
    .btn-ghost{background:transparent;border:1px solid rgba(255,255,255,0.06);color:#dbeafe}
    /* Gauge */
    .gauge-wrap{display:flex;align-items:center;gap:18px}
    .gauge{width:260px;height:150px}
    .needle{transform-origin:50% 85%;}
    /* Animated cards */
    .stat{padding:12px;border-radius:12px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.03)}
    /* small responsive tweaks */
    @media(max-width:900px){.gauge{width:210px;height:120px}.gauge-wrap{flex-direction:column;align-items:center}}
  </style>
</head>
<body>
  <div class="container">
    <div class="glass">
      <div class="brand mb-4">
        <div class="logo">NP</div>
        <div>
          <div style="font-weight:700;font-size:18px">NetPulse</div>
          <div class="small muted">Advanced WiFi & Internet Speed Test</div>
        </div>
        <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
          <button id="exportCSV" class="btn btn-ghost">Export CSV</button>
          <button id="exportJSON" class="btn btn-ghost">Export JSON</button>
          <button id="clearHistory" class="btn btn-ghost">Clear</button>
        </div>
      </div>

      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-7">
          <div class="gauge-wrap glass p-4">
            <svg class="gauge" viewBox="0 0 260 150" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="g1" x1="0" x2="1"><stop offset="0%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#7c3aed"/></linearGradient>
              </defs>
              <!-- Arc -->
              <path d="M20 120 A110 110 0 0 1 240 120" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="18" stroke-linecap="round"/>
              <!-- Colored arc overlay (dynamic via stroke-dasharray) -->
              <path id="arcFill" d="M20 120 A110 110 0 0 1 240 120" fill="none" stroke="url(#g1)" stroke-width="18" stroke-linecap="round" stroke-dasharray="0 700"/>
              <!-- ticks -->
              <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                <!-- draw ticks using JS if needed -->
              </g>
              <!-- needle -->
              <g transform="translate(130,120)">
                <g class="needle" id="needle">
                  <rect x="-2" y="-90" width="4" height="90" rx="2" fill="#f8fafc" opacity="0.95"/>
                  <circle cx="0" cy="0" r="8" fill="#0b1220" stroke="#f8fafc" stroke-width="2"/>
                </g>
              </g>
            </svg>

            <div style="flex:1">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <button id="startBtn" class="btn btn-primary">Start Test</button>
                <div id="status" class="small muted">Ready</div>
              </div>
              <div style="display:flex;gap:8px;margin-top:6px">
                <div class="stat flex-1">
                  <div class="small muted">Ping</div>
                  <div id="pingVal" style="font-weight:700;font-size:18px">— ms</div>
                </div>
                <div class="stat flex-1">
                  <div class="small muted">Download</div>
                  <div id="downloadVal" style="font-weight:700;font-size:18px">— Mbps</div>
                </div>
                <div class="stat flex-1">
                  <div class="small muted">Upload</div>
                  <div id="uploadVal" style="font-weight:700;font-size:18px">— Mbps</div>
                </div>
              </div>

              <div id="progressBar" style="height:8px;background:rgba(255,255,255,0.03);border-radius:999px;margin-top:12px;overflow:hidden;display:none">
                <div id="progressFill" style="height:100%;width:0;background:linear-gradient(90deg,#06b6d4,#7c3aed);transition:width 0.2s"></div>
              </div>

            </div>
          </div>

          <div class="mt-4 glass p-4">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div style="font-weight:700">Test History</div>
              <div class="small muted">Saved locally & on server</div>
            </div>
            <canvas id="historyChart" style="height:220px;margin-top:12px"></canvas>
          </div>
        </div>

        <div class="col-span-5">
          <div class="glass p-4">
            <div style="font-weight:700">Recent Tests</div>
            <div id="historyList" style="margin-top:12px;display:flex;flex-direction:column;gap:8px;max-height:420px;overflow:auto"></div>
          </div>

          <div class="glass p-4 mt-4">
            <div style="font-weight:700">Server Info</div>
            <div id="serverInfo" class="small muted mt-2">—</div>
            <div id="elapsed" class="small muted mt-1">—</div>
          </div>
        </div>
      </div>

      <div style="margin-top:12px;display:flex;justify-content:flex-end;gap:8px">
        <div class="small muted">NetPulse • Built for fast diagnostics</div>
      </div>
    </div>
  </div>

<script>
// Client-side logic: animate gauge, manage history, call server
let needleEl = document.getElementById('needle')
let arcFill = document.getElementById('arcFill')
let startBtn = document.getElementById('startBtn')
let statusEl = document.getElementById('status')
let progressBar = document.getElementById('progressBar')
let progressFill = document.getElementById('progressFill')
let pingVal = document.getElementById('pingVal')
let downloadVal = document.getElementById('downloadVal')
let uploadVal = document.getElementById('uploadVal')
let serverInfoEl = document.getElementById('serverInfo')
let elapsedEl = document.getElementById('elapsed')
let historyList = document.getElementById('historyList')
let exportCSV = document.getElementById('exportCSV')
let exportJSON = document.getElementById('exportJSON')
let clearHistoryBtn = document.getElementById('clearHistory')

let chartCtx = document.getElementById('historyChart').getContext('2d')
let historyChart = new Chart(chartCtx,{
  type:'line',
  data:{labels:[],datasets:[{label:'Download (Mbps)',data:[],fill:false,borderColor:'#06b6d4',tension:0.3},{label:'Upload (Mbps)',data:[],fill:false,borderColor:'#7c3aed',tension:0.3}]},
  options:{responsive:true,plugins:{legend:{labels:{color:'#e6eef8'}}},scales:{x:{ticks:{color:'#cfe8ff'}},y:{ticks:{color:'#cfe8ff'}}}
})

function setNeedle(percent){
  // percent 0..100 mapped to -110deg..110deg
  let deg = -110 + (percent/100)*220
  needleEl.style.transform = `rotate(${deg}deg)`
  // arc dash
  let total = 700
  let draw = Math.min(total, Math.round((percent/100)*total))
  arcFill.setAttribute('stroke-dasharray', `${draw} ${total-draw}`)
}

function simulateProgress(){
  progressBar.style.display='block'
  let p=0
  progressFill.style.width='0%'
  return new Promise(resolve=>{
    let iv = setInterval(()=>{
      p += Math.random()*8 + 3
      if(p>=98){p=98;progressFill.style.width=p+'%';clearInterval(iv);resolve();}
      progressFill.style.width = p+'%'
    },300)
  })
}

async function runTest(){
  startBtn.disabled=true
  statusEl.innerText='Finding best server...'
  await simulateProgress()
  statusEl.innerText='Running test — download...'
  setNeedle(30)

  let resp
  try{
    let r = await fetch('/run_test', {method:'POST'})
    if(!r.ok) throw new Error('Server error')
    resp = await r.json()
  } catch(err){
    statusEl.innerText = 'Error: '+err.message
    startBtn.disabled=false
    progressBar.style.display='none'
    return
  }

  // animate to results
  pingVal.innerText = (resp.ping ?? '—') + ' ms'
  downloadVal.innerText = resp.download_mbps.toFixed(2) + ' Mbps'
  uploadVal.innerText = resp.upload_mbps.toFixed(2) + ' Mbps'
  serverInfoEl.innerText = resp.server || '—'
  elapsedEl.innerText = 'Elapsed: ' + resp.elapsed_seconds + 's'

  // animate needle based on download speed (cap at 1000 Mbps)
  let norm = Math.min(100, (resp.download_mbps/200)*100)
  anime({targets: '#needle', rotate: [-110 + 'deg', (-110 + (norm/100)*220) + 'deg'], easing: 'spring(1, 80, 10, 0)'});
  setNeedle(norm)

  // finalize progress
  progressFill.style.width='100%'
  setTimeout(()=>{progressBar.style.display='none';startBtn.disabled=false;statusEl.innerText='Done'},600)

  // add to history (client + server)
  addHistory(resp)
}

function addHistory(entry){
  // push to chart
  historyChart.data.labels.push(entry.timestamp)
  historyChart.data.datasets[0].data.push(entry.download_mbps)
  historyChart.data.datasets[1].data.push(entry.upload_mbps)
  historyChart.update()

  // add list item
  let div = document.createElement('div')
  div.className='stat'
  div.innerHTML = `<div style="display:flex;justify-content:space-between"><div><div style="font-weight:700">${entry.download_mbps} Mbps</div><div class="small muted">${entry.timestamp} • ${entry.server||'server'}</div></div><div style="text-align:right"><div class="small">Ping ${entry.ping} ms</div><div class="small muted">${entry.elapsed_seconds}s</div></div></div>`
  historyList.prepend(div)

  // persist locally
  let local = JSON.parse(localStorage.getItem('np_history')||'[]')
  local.unshift(entry)
  if(local.length>50) local.pop()
  localStorage.setItem('np_history', JSON.stringify(local))
}

startBtn.addEventListener('click', runTest)

// load history from server on start
async function loadHistory(){
  try{
    let r = await fetch('/history')
    let arr = await r.json()
    // mirror to localStorage and UI
    localStorage.setItem('np_history', JSON.stringify(arr))
    arr.forEach(item=>addHistory(item))
  }catch(e){
    // fallback to localStorage
    let local = JSON.parse(localStorage.getItem('np_history')||'[]')
    local.reverse().forEach(item=>addHistory(item))
  }
}

exportCSV.addEventListener('click', ()=>{ window.location='/export_csv' })
exportJSON.addEventListener('click', ()=>{ window.location='/export_json' })
clearHistoryBtn.addEventListener('click', async ()=>{ await fetch('/clear_history',{method:'POST'}); localStorage.removeItem('np_history'); historyChart.data.labels=[]; historyChart.data.datasets.forEach(ds=>ds.data=[]); historyChart.update(); historyList.innerHTML=''; serverInfoEl.innerText='—'; elapsedEl.innerText='—'; })

loadHistory()
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