#!/usr/bin/env python3
"""StackStorm action: block a malicious IP via iptables + log to IRIS."""
import subprocess
import os
import json
import ipaddress
import requests
from st2common.runners.base_action import Action


class BlockIPAction(Action):
    def run(self, ip_address, direction="both", duration_hours=24,
            reason="Automated SOC block", notify=True):
        results = {"ip": ip_address, "blocked": False, "method": [], "errors": []}

        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            results["errors"].append("invalid IP address")
            return (False, results)

        if direction not in ("inbound", "outbound", "both"):
            results["errors"].append("direction must be inbound, outbound, or both")
            return (False, results)
        if duration_hours < 0:
            results["errors"].append("duration_hours must be non-negative")
            return (False, results)

        # iptables block
        commands = []
        if direction in ("inbound", "both"):
            commands.append(["iptables", "-I", "INPUT", "-s", ip_address, "-j", "DROP"])
        if direction in ("outbound", "both"):
            commands.append(["iptables", "-I", "OUTPUT", "-d", ip_address, "-j", "DROP"])

        applied = []
        try:
            for cmd in commands:
                subprocess.run(cmd, check=True, capture_output=True)
                applied.append(cmd)
            results["blocked"] = True
            results["method"].append("iptables")
        except (OSError, subprocess.CalledProcessError) as e:
            results["errors"].append(f"iptables: {e}")
            for cmd in reversed(applied):
                rollback = [cmd[0], "-D", *cmd[2:]]
                subprocess.run(rollback, check=False, capture_output=True)

        # Schedule unblock if duration set
        if duration_hours > 0 and results["blocked"]:
            try:
                cleanup = "\n".join(
                    f"{cmd[0]} -D {' '.join(cmd[2:])}" for cmd in commands
                ) + "\n"
                subprocess.run(
                    ["at", "now", "+", str(duration_hours), "hours"],
                    input=cleanup,
                    text=True,
                    check=True,
                    capture_output=True,
                )
                results["scheduled_unblock_hours"] = duration_hours
            except (OSError, subprocess.CalledProcessError) as e:
                results["errors"].append(f"at-scheduler: {e}")

        # Notify via webhook if configured
        if notify and os.getenv("SLACK_WEBHOOK_URL"):
            try:
                msg = {"text": f"🚫 IP BLOCKED: `{ip_address}` — Reason: {reason} — Duration: {duration_hours}h"}
                requests.post(os.getenv("SLACK_WEBHOOK_URL"), json=msg, timeout=5)
            except requests.RequestException as e:
                results["errors"].append(f"slack-webhook: {e}")

        self.logger.info(f"block_ip result: {json.dumps(results)}")
        return (results["blocked"], results)
