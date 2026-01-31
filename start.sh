#!/bin/bash

# Start FastAPI in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit in background
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 &

# Start MITM Proxy (Port 8080)
# Use --web-host 0.0.0.0 to allow IAP tunnel to access dashboard at 8081 if needed
mitmweb -s proxy_addon.py --set confdir=./certs --listen-host 0.0.0.0 --listen-port 8080 --web-host 0.0.0.0 --web-port 8081 &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
