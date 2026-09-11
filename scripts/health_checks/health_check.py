import sys, json, argparse, os, socket
def check_port(host, port, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False
def run_health_checks(ci_mode=False):
    results = {"timestamp": "2026-09-11T00:00:00Z", "overall_status": "PASS", "checks": []}
    missing_creds = [var for var in ["SIEM_API_KEY", "MISP_URL"] if not os.getenv(var)]
    if missing_creds:
        results["overall_status"] = "FAIL"
        results["checks"].append({"name": "credentials_missing", "status": "FAIL", "details": f"Missing: {', '.join(missing_creds)}"})
    else:
        results["checks"].append({"name": "credentials_missing", "status": "PASS", "details": "Credentials present."})
    for svc, port in [("opensearch", 9200), ("velociraptor", 8889)]:
        is_up = check_port("localhost", port)
        status = "PASS" if is_up else "FAIL"
        if status == "FAIL": results["overall_status"] = "FAIL"
        results["checks"].append({"name": f"{svc}_port_unavailable", "status": status, "details": f"Host: localhost, Port: {port}"})
    return results
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true")
    args = parser.parse_args()
    results = run_health_checks(ci_mode=args.ci)
    if args.ci:
        print(json.dumps(results, indent=2))
    sys.exit(0 if results["overall_status"] == "PASS" else 1)