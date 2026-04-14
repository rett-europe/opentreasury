#!/bin/bash
# Custom startup script — bypasses Oryx's startup script generation.
# Packages are pre-installed to .python_packages/ on CI (not on the server).
export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:${PYTHONPATH:-}"
exec gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
