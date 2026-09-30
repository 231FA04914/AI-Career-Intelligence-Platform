"""
Unified Application & Production Launcher (Milestone 4 - Task 10)
Supports launching FastAPI REST server, Streamlit Dashboard, or both concurrently.

Usage:
  python run_app.py --mode=both       # Launch both API and Streamlit UI (Default)
  python run_app.py --mode=api        # Launch FastAPI REST backend on port 8000
  python run_app.py --mode=streamlit  # Launch Streamlit dashboard on port 8501
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("platform_launcher")


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run FastAPI uvicorn server."""
    logger.info(f"Starting FastAPI server on http://{host}:{port} ...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]
    return subprocess.Popen(cmd)


def run_streamlit(port: int = 8501):
    """Run Streamlit dashboard."""
    logger.info(f"Starting Streamlit dashboard on http://localhost:{port} ...")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    return subprocess.Popen(cmd)


def main():
    parser = argparse.ArgumentParser(description="AI Career Intelligence Platform Unified Launcher")
    parser.add_argument("--mode", choices=["both", "api", "streamlit"], default="both", help="Execution mode")
    parser.add_argument("--api-port", type=int, default=8000, help="FastAPI port")
    parser.add_argument("--streamlit-port", type=int, default=8501, help="Streamlit port")
    args = parser.parse_args()

    # Ensure required data directories exist
    for dir_name in ["data/audio", "data/transcripts", "data/summaries"]:
        Path(dir_name).mkdir(parents=True, exist_ok=True)

    processes = []
    try:
        if args.mode in ["both", "api"]:
            p_api = run_api(port=args.api_port)
            processes.append(p_api)

        if args.mode in ["both", "streamlit"]:
            # Brief pause to let API initialize
            time.sleep(1)
            p_st = run_streamlit(port=args.streamlit_port)
            processes.append(p_st)

        logger.info("Platform services active. Press Ctrl+C to terminate.")
        while True:
            for p in processes:
                if p.poll() is not None:
                    logger.warning(f"Process {p.pid} terminated with code {p.returncode}")
                    return
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown requested. Terminating background services...")
        for p in processes:
            p.terminate()
            p.wait()
        logger.info("All services shut down gracefully.")


if __name__ == "__main__":
    main()
