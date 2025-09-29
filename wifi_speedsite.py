from flask import Flask, render_template_string, jsonify, request
import speedtest
import time

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WiFi Network Speed Test</title>
  <style>
    body{font-family:Inter,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f4f6fb;color:#0b1330;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
    .card{background:#fff;padding:28px;border-radius:12px;box-shadow:0 8px 30px rgba(13,38,76,0.08);width:360px;text-align:center}
    h1{font-size:20px;margin:0 0 12px}
    p.lead{margin:0 0 18px;color:#55607a;font-size:13px}
    button{background:#0b66ff;color:#fff;border:0;padding:10px 16px;border-radius:10px;font-weight:600;cursor:pointer}
    button:disabled{opacity:0.6;cursor:wait}
    .stat{margin-top:18px;display:flex;justify-content:space-between;align-items:center}
    .value{font-size:20px;font-weight:700}
    .label{font-size:12px;color:#64707f}
    .spinner{border:4px solid #f3f3f3;border-top:4px solid #0b66ff;border-radius:50%;width:28px;height:28px;animation:spin 1s linear infinite;margin:0 auto}
    @keyframes spin{to{transform:rotate(360deg)}}
    .small{font-size:12px;color:#6b7280}
    .server{margin-top:12px;font-size:12px;color:#475569}
  </style>
</head>
<body>
  <div class="card">
    <h1>Wi‑Fi Network Speed Test</h1>
    <p class="lead">Measure Ping, Download and Upload speeds using Speedtest.net servers.</p>

    <div id="controls">
      <button id="startBtn">Start Test</button>
      <div id="running" style="display:none;margin-top:12px">
        <div class="spinner" aria-hidden="true"></div>
        <div class="small">Running test... this may take 20–40 seconds</div>
      </div>
    </div>

    <div id="result" style="display:none">
      <div class="stat"><div>
        <div class="label">Ping</div>
        <div id="ping" class="value">— ms</div>
      </div></div>

      <div class="stat"><div>
        <div class="label">Download</div>
        <div id="download" class="value">— Mbps</div>
      </div></div>

      <div class="stat"><div>
        <div class="label">Upload</div>
        <div id="upload" class="value">— Mbps</div>
      </div></div>

      <div class="server" id="serverInfo"></div>
      <div style="margin-top:12px"><button id="againBtn">Run Again</button></div>
    </div>

    <div id="error" style="display:none;margin-top:12px;color:#b91c1c"></div>
  </div>

<script>
const startBtn = document.getElementById('startBtn')
const againBtn = document.getElementById('againBtn')
const running = document.getElementById('running')
const result = document.getElementById('result')
const errorBox = document.getElementById('error')

startBtn.addEventListener('click', runTest)
againBtn.addEventListener('click', runTest)

async function runTest(){
  errorBox.style.display='none'
  result.style.display='none'
  startBtn.disabled = true
  running.style.display = 'block'

  try{
    const resp = await fetch('/run_test', {method:'POST'} )
    if(!resp.ok) throw new Error('Network response was not ok')
    const json = await resp.json()
    if(json.error) throw new Error(json.error)

    document.getElementById('ping').innerText = (json.ping === null)? '— ms' : (json.ping + ' ms')
    document.getElementById('download').innerText = json.download_mbps.toFixed(2) + ' Mbps'
    document.getElementById('upload').innerText = json.upload_mbps.toFixed(2) + ' Mbps'
    document.getElementById('serverInfo').innerText = json.server || ''

    result.style.display = 'block'
  } catch(err){
    errorBox.innerText = 'Error: ' + err.message
    errorBox.style.display = 'block'
  } finally{
    running.style.display = 'none'
    startBtn.disabled = false
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
    # Run speedtest.sync and return JSON
    try:
        t0 = time.time()
        s = speedtest.Speedtest()
        # find best server
        s.get_best_server()
        # perform download and upload
        download_bps = s.download()
        upload_bps = s.upload()
        results = s.results.dict()

        # convert to Mbps and format
        download_mbps = float(download_bps) / 1_000_000
        upload_mbps = float(upload_bps) / 1_000_000
        ping = results.get('ping', None)
        server = results.get('server', {})
        server_info = None
        if server:
            name = server.get('name')
            country = server.get('country')
            sponsor = server.get('sponsor')
            server_info = f"{sponsor} — {name}, {country}"

        t1 = time.time()
        elapsed = t1 - t0

        return jsonify({
            'ping': round(ping,2) if ping is not None else None,
            'download_mbps': round(download_mbps, 4),
            'upload_mbps': round(upload_mbps, 4),
            'server': server_info,
            'elapsed_seconds': round(elapsed,2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
