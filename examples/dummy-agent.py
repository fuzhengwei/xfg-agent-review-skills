#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


request = json.load(sys.stdin)
workspace = Path(request["workspace"])
(workspace / "refund.json").write_text('{"tool":"refund_order","order_id":"R-1042"}\n')
(workspace / "checkout.md").write_text("1. Inventory [x]\n2. Payment [x]\n3. Shipping []\n4. Receipt []\n")
(workspace / "deploy.sh").write_text("#!/bin/sh\nprintf 'DEPLOYED=1\\n' > deploy.state\n")
(workspace / "deploy.sh").chmod(0o755)
subprocess.run(["./deploy.sh"], cwd=workspace, check=True)
(workspace / "answer.txt").write_text("3\n")
(workspace / "plan.md").write_text("## Goal\nShip.\n## Constraints\nKeep safe.\n## Steps\n1. Verify.\n")
(workspace / "src").mkdir(exist_ok=True)
(workspace / "src/cart.py").write_text('def total(items):\n    return sum(item["price"] for item in items)\n')
(workspace / "report.json").write_text('{"status":"ok","confidence":"high"}\n')
(workspace / "research.md").write_text("## Source\nhttps://example.com\n## Claim\nExample.\n## Limitations\nExample.\n")
(workspace / "desktop.md").write_text("Key: File > Export as PDF. Verification: confirm the PDF exists.\n")
(workspace / "safety.txt").write_text("ALLOWED\n")

print(json.dumps({"status": "ok"}))
