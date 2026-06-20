"""
Build the frontend using PowerShell (has full PATH, finds npm automatically).
Double-click to run.
"""
import subprocess, os, sys

FRONTEND = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\frontend"
LOG      = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\build_log.txt"

print("Building frontend via PowerShell...")

# PowerShell inherits full user PATH — finds npm even when py.exe can't
cmd = f'cd "{FRONTEND}"; npm run build'
result = subprocess.run(
    ["powershell", "-NoProfile", "-Command", cmd],
    capture_output=False
)

if result.returncode == 0:
    print("\nBuild SUCCESS! Refresh http://localhost:8000 in your browser.")
    with open(LOG, "w") as f:
        f.write("Build SUCCESS\n")
else:
    print(f"\nBuild FAILED (exit code {result.returncode})")
    # Try with node path explicitly
    print("\nTrying to find node.exe directly...")
    find_cmd = '(Get-Command node -ErrorAction SilentlyContinue).Source'
    r2 = subprocess.run(["powershell", "-Command", find_cmd], capture_output=True, text=True)
    node_path = r2.stdout.strip()
    if node_path:
        print(f"Node found at: {node_path}")
        npm_path = os.path.join(os.path.dirname(node_path), "npm.cmd")
        print(f"Trying npm at: {npm_path}")
        r3 = subprocess.run([npm_path, "run", "build"], cwd=FRONTEND)
        if r3.returncode == 0:
            print("\nBuild SUCCESS!")
    else:
        print("Node.js not found. Please install from https://nodejs.org")

input("\nPress Enter to close...")
