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

## 💻 Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/advanced-wifi-speedtest.git
cd advanced-wifi-speedtest
