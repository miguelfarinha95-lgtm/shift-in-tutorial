#!/usr/bin/env python3
import json
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit", "tests/api", "-q"],
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    output = result.stdout + result.stderr
    print(json.dumps({"decision": "block", "reason": output}))
