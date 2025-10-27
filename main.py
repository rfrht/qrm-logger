"""
Compatibility shim. Launches qrm_logger.__main__.main().
Also ensures the local 'src' directory is on sys.path for direct execution without installation.
"""

import sys
from pathlib import Path

# Prepend the local 'src' directory to sys.path so imports work when running this file directly
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

def main():
    from qrm_logger.__main__ import main as _main
    _main()

if __name__ == "__main__":
    main()
