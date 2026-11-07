"""Check the real Hermes CLI without signing in or exposing captured output."""
import subprocess
import sys

try:
    result=subprocess.run([sys.argv[1],'auth','add','--help'],capture_output=True,timeout=40)
except (OSError,subprocess.TimeoutExpired,IndexError):
    raise SystemExit(1)
raise SystemExit(result.returncode)
