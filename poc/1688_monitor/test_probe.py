"""Run: .venv/Scripts/python.exe test_probe.py"""
import subprocess
import sys
from pathlib import Path

probe = Path(__file__).with_name('probe.py')
result = subprocess.run([sys.executable, str(probe), '--url', 'https://example.com/'],
                        capture_output=True, text=True)
assert result.returncode == 2, result
assert 'Expected an HTTPS 1688 product detail URL' in result.stderr
print('URL boundary check passed')
