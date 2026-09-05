"""
Build script: writes the enhanced kvcached HTML explainer to
docs/kvcached/index.html inside the project repo.

Run from the project root:
    python scripts/build_kvcached_explainer.py
    python scripts/build_kvcached_explainer.py --serve
"""

import http.server
import os
import pathlib
import sys
import threading
import webbrowser

project_root = pathlib.Path(__file__).parent.parent
explainer_dir = pathlib.Path(__file__).parent / "kvcached_explainer"

# Read components
template = (explainer_dir / "template.html").read_text(encoding="utf-8")
css = (explainer_dir / "styles.css").read_text(encoding="utf-8")
js = (explainer_dir / "script.js").read_text(encoding="utf-8")

# Inject CSS and JS
html_content = template.replace("{{CSS}}", css).replace("{{JS}}", js)

# Write to project docs
out = project_root / "docs" / "kvcached" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html_content, encoding="utf-8")
print(f"Written {out.stat().st_size:,} bytes.")

# Serve with --serve flag
if "--serve" in sys.argv:
    PORT = 7822
    os.chdir(out.parent)
    Handler = http.server.SimpleHTTPRequestHandler

    class QuietHandler(Handler):
        def log_message(self, fmt, *args):
            pass

    with http.server.HTTPServer(("127.0.0.1", PORT), QuietHandler) as httpd:
        url = f"http://127.0.0.1:{PORT}/index.html"
        print(f"\nServing at {url}")
        print("   Press Ctrl+C to stop.\n")
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
