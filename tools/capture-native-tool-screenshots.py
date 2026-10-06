#!/usr/bin/env python3
"""
Live Native Tools Screenshot Capture Engine
===========================================
Captures high-resolution, fully authenticated screenshots of:
1. OpenSearch Dashboards (SIEM) - http://localhost:5601
2. MITRE Caldera (Adversary Simulation) - http://localhost:8888
3. Velociraptor (EDR & Forensics) - https://localhost:8889
"""

import sys
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboards" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

def capture_opensearch(context):
    print("[*] Capturing OpenSearch Dashboards (http://localhost:5601)...")
    page = context.new_page()
    try:
        # Navigate to login or home
        page.goto("http://localhost:5601/app/login", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        
        # Check if login form exists
        if page.query_selector('input[type="text"]') or page.query_selector('input[name="username"]'):
            print("    Logging into OpenSearch Dashboards...")
            page.fill('input[type="text"], input[name="username"]', "admin")
            page.fill('input[type="password"], input[name="password"]', "SocLabAdmin!2026#Secure")
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)
            
        # Navigate to 01 SOC Command Center Dashboard or Discover
        page.goto("http://localhost:5601/app/dashboards#/view/soc-dashboard-command-center", wait_until="networkidle", timeout=30000)
        time.sleep(4)
        
        target_file = OUT / "02_opensearch_siem.png"
        page.screenshot(path=str(target_file), full_page=False)
        print(f"[+] Saved OpenSearch screenshot: {target_file}")
    except Exception as e:
        print(f"[-] OpenSearch capture failed: {e}")
        # Fallback to home
        try:
            page.goto("http://localhost:5601/app/home", wait_until="networkidle", timeout=15000)
            time.sleep(2)
            page.screenshot(path=str(OUT / "02_opensearch_siem.png"))
            print(f"[+] Saved OpenSearch fallback screenshot.")
        except Exception as e2:
            print(f"[-] OpenSearch fallback failed: {e2}")
    finally:
        page.close()

def capture_caldera(context):
    print("[*] Capturing MITRE Caldera (http://localhost:8888)...")
    page = context.new_page()
    try:
        # Caldera login
        page.goto("http://localhost:8888/login", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        
        if page.query_selector('input[name="username"]') or page.query_selector('input[type="text"]'):
            print("    Logging into MITRE Caldera...")
            page.fill('input[name="username"], input[type="text"]', "admin")
            page.fill('input[name="password"], input[type="password"]', "admin123")
            page.click('button[type="submit"], input[type="submit"]')
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)
            
        # Navigate to Caldera main navigation / compass / operations
        page.goto("http://localhost:8888/", wait_until="networkidle", timeout=30000)
        time.sleep(3)
        
        target_file = OUT / "07_caldera_attack.png"
        page.screenshot(path=str(target_file), full_page=False)
        print(f"[+] Saved Caldera screenshot: {target_file}")
    except Exception as e:
        print(f"[-] Caldera capture failed: {e}")
    finally:
        page.close()

def capture_velociraptor(context):
    print("[*] Capturing Velociraptor EDR (https://localhost:8889)...")
    page = context.new_page()
    try:
        # Velociraptor uses HTTP basic auth
        # Set HTTP credentials on page or URL
        page.goto("https://admin:VelociraptorAdmin!2026%23Secure@localhost:8889/app/index.html", wait_until="networkidle", timeout=30000)
        time.sleep(3)
        
        target_file = OUT / "09_velociraptor.png"
        page.screenshot(path=str(target_file), full_page=False)
        print(f"[+] Saved Velociraptor screenshot: {target_file}")
    except Exception as e:
        print(f"[-] Velociraptor capture failed: {e}")
    finally:
        page.close()

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1680, "height": 1050},
            device_scale_factor=1,
            ignore_https_errors=True,
            http_credentials={
                "username": "admin",
                "password": "VelociraptorAdmin!2026#Secure"
            }
        )
        
        capture_opensearch(context)
        capture_caldera(context)
        capture_velociraptor(context)
        
        browser.close()
        print("[*] All native live tool screenshots captured successfully!")

if __name__ == "__main__":
    main()
