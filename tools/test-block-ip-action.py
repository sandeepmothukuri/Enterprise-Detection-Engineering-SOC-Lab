#!/usr/bin/env python3
"""Static regression checks for the StackStorm block_ip action."""
from pathlib import Path


SOURCE = Path("config/stackstorm/packs/soc/actions/block_ip.py").read_text(
    encoding="utf-8"
)

assert "ipaddress.ip_address(ip_address)" in SOURCE
assert 'subprocess.run(at_cmd, shell=True' not in SOURCE
assert '["at", "now", "+", str(duration_hours), "hours"]' in SOURCE
assert 'for cmd in commands' in SOURCE
assert 'rollback = [cmd[0], "-D", *cmd[2:]]' in SOURCE
assert '"direction must be inbound, outbound, or both"' in SOURCE
print("V10 block_ip safety regression test passed")
