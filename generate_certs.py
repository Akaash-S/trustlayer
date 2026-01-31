import os
import subprocess
import time
import sys

def generate():
    cert_dir = os.path.abspath("certs")
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
        
    print(f"Generating certificates in {cert_dir}...")
    try:
        # Fix: Run via python module to avoid PATH issues
        cmd = [sys.executable, "-m", "mitmproxy.tools.dump", "--set", f"confdir={cert_dir}", "--no-server"]
        print(f"Running: {' '.join(cmd)}")
        
        # shell=False is safer and cleaner with list arguments
        proc = subprocess.Popen(cmd, shell=False)
        
        print("Waiting for mitmdump to initialize...")
        time.sleep(10) # Give it plenty of time
        
        # Kill logic
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)])
        print("Certificates generated successfully.")
    except Exception as e:
        print(f"Error generating certs: {e}")

if __name__ == "__main__":
    generate()
