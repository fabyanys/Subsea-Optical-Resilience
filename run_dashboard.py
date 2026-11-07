import subprocess
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    dashboard_app = base_dir / "09_Audit_and_Evaluation" / "dashboard" / "app.py"
    
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_app),
        "--server.port",
        "8501",
        "--client.toolbarMode",
        "minimal"
    ]
    print(f"Starting dashboard from: {dashboard_app}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
