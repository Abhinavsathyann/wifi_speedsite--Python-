# WiFi Speed Test

A **modern, interactive, web-based WiFi/Internet speed testing application** built with **Python Flask**.  
It provides **real-time download, upload, and ping measurements**, animated visualizations, history charts, and export options — all with a sleek **glassmorphism UI** and fully responsive design.

---

## 🌟 Features

- **Real-time Speed Test**
  - Measures **Download**, **Upload**, and **Ping**.
  - Animated gauge showing speed visually.
- **Interactive Flip Cards**
  - Displays Ping, Download, and Upload in dynamic flip cards.
- **History Chart**
  - Tracks last 10 tests with line charts for download & upload speeds.
- **Export Options**
  - Export test history to **CSV** or **JSON**.
- **Modern UI**
  - Glassmorphism style cards and sections.
  - Responsive design for mobile and desktop.
  - Dark/Light theme toggle.
- **Threaded Backend**
  - Speedtest runs in a separate thread for responsive UI.
  - Handles timeouts gracefully.

---

## 🛠 Technology Stack

- **Backend**: Python 3 + Flask  
- **Speed Test**: `speedtest-cli`  
- **Frontend**: HTML, TailwindCSS, Chart.js, Anime.js  
- **Threading**: Python `threading` for non-blocking speed test

---

## 🖥 Usage

-Click the Start Test button to measure your internet speed.

-View animated gauge and flip-cards for Ping, Download, Upload.

-Observe history chart of last 10 tests.

-Export results via CSV or JSON buttons.

-Switch between Light/Dark mode using the toggle button.

---

Create a virtual environment (optional but recommended)
```
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows


Install dependencies
pip install flask speedtest-cli

Run the application
python wifi_speedsite.py


Open in browser
http://127.0.0.1:5000

---
Installation

1. Clone the repository

```bash
git clone https://github.com/Abhinavsathyann/wifi_speedsite-Python.git
cd advanced-wifi-speedtest
