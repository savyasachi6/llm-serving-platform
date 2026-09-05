# 📊 kvcached Visualizer & Memory Sandbox

This directory contains the compiler and local server tooling for the interactive `kvcached` memory elasticity explainer and VRAM sandbox.

---

## 🚀 Usage

### 1. Build Static Output Only
Compiles modular HTML/CSS/JS components from `templates/memory_explainer/` into `docs/kvcached/index.html`:
```bash
python scripts/kvcached_visualizer/serve.py
```

### 2. Build and Launch Live Interactive Server
Spins up a local HTTP server and automatically opens the interactive simulator in your browser:
```bash
python scripts/kvcached_visualizer/serve.py --serve
```
Default URL: `http://127.0.0.1:7822/index.html`

---

## 🗂️ Architecture
- **Source Templates**: Located in `templates/memory_explainer/` (`template.html`, `styles.css`, `script.js`).
- **Compiled Output**: Published to `docs/kvcached/index.html` for offline viewing or GitHub Pages hosting.
