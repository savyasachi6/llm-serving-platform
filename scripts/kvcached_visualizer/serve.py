"""Build and serve the interactive kvcached visual explainer and simulator.

Compiles modular HTML/CSS/JS components from templates/memory_explainer/ into
docs/kvcached/index.html for static hosting or local browser preview.

Usage:
    # Build only:
    python scripts/kvcached_visualizer/serve.py

    # Build and launch local web server at http://127.0.0.1:7822:
    python scripts/kvcached_visualizer/serve.py --serve
"""

import http.server
import os
import pathlib
import sys
import threading
import webbrowser

project_root = pathlib.Path(__file__).resolve().parents[2]
template_dir = project_root / "templates" / "memory_explainer"

# Read modular HTML/CSS/JS components
template = (template_dir / "template.html").read_text(encoding="utf-8")
css = (template_dir / "styles.css").read_text(encoding="utf-8")
js = (template_dir / "script.js").read_text(encoding="utf-8")

# Inject CSS and JS into single self-contained document
html_content = template.replace("{{CSS}}", css).replace("{{JS}}", js)

# Write to project documentation output
out = project_root / "docs" / "kvcached" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html_content, encoding="utf-8")
print(f"[OK] Successfully built docs/kvcached/index.html ({out.stat().st_size:,} bytes).")

# Optional: Serve locally with --serve flag
if "--serve" in sys.argv:
    PORT = 7822
    os.chdir(out.parent)
    Handler = http.server.SimpleHTTPRequestHandler

    class QuietHandler(Handler):
        def log_message(self, fmt, *args):
            pass

    with http.server.HTTPServer(("127.0.0.1", PORT), QuietHandler) as httpd:
        url = f"http://127.0.0.1:{PORT}/index.html"
        print(f"\n[Serving] Interactive kvcached Visualizer at {url}")
        print("          Press Ctrl+C to stop.\n")
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
