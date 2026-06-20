"""
Start PriceCart locally.
Double-click to launch the server, then open http://localhost:8000
"""
import subprocess, sys, os, time, webbrowser, threading

BASE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE, "backend")
DIST    = os.path.join(BASE, "frontend", "dist", "index.html")

print("=" * 50)
print("  PriceCart — Local Server")
print("=" * 50)

if not os.path.exists(DIST):
    print("\nWARNING: Frontend not built yet.")
    print("Please open a terminal in this folder and run:")
    print('  cd frontend')
    print('  npm run build')
    print("\nThe server will still start — API endpoints work,")
    print("but the web UI won't appear until the build is done.\n")
else:
    print("\nFrontend build found — ready.")

print("\nStarting server on http://localhost:8000 ...")
print("Press Ctrl+C in this window to stop.\n")

def open_browser():
    time.sleep(3)
    webbrowser.open("http://localhost:8000")

threading.Thread(target=open_browser, daemon=True).start()

os.chdir(BACKEND)
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app",
                "--host", "0.0.0.0", "--port", "8000", "--reload"])

input("\nServer stopped. Press Enter to close...")
