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
        # Navigate to login
        print("    Navigating to OpenSearch login...")
        page.goto("http://localhost:5601/app/login", wait_until="networkidle", timeout=30000)
        time.sleep(2)
        
        # Check if login form exists
        user_input = page.query_selector('input[data-test-subj="user-name"], input[type="text"], input[name="username"]')
        if user_input:
            print("    Entering OpenSearch Dashboards admin credentials...")
            page.fill('input[data-test-subj="user-name"], input[type="text"], input[name="username"]', "admin")
            page.fill('input[data-test-subj="password"], input[type="password"], input[name="password"]', "SocLabAdmin!2026#Secure")
            page.click('button[data-test-subj="submit"], button[type="submit"], button.euiButton--fill')
            time.sleep(4)
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)
            
        print(f"    Current OpenSearch URL: {page.url}")
        
        # Check and handle "Select your tenant" modal if present via JS
        try:
            print("    Dismissing tenant selection modal via JS...")
            page.evaluate("""() => {
                const btn = document.querySelector('[data-test-subj="confirm-tenant"], .euiModalFooter button.euiButton--fill, button[type="submit"]');
                if (btn) btn.click();
            }""")
            time.sleep(3)
        except Exception as tenant_err:
            print(f"    Tenant modal check: {tenant_err}")
            
        # Navigate to Discover SIEM Event Telemetry Console with 30-day time range
        discover_url = "http://localhost:5601/app/discover#/?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-30d,to:now))"
        print(f"    Navigating to Discover SIEM Console: {discover_url}...")
        page.goto(discover_url, timeout=30000)
        time.sleep(5)
        
        # Check if tenant modal popped up again
        try:
            page.evaluate("""() => {
                const btn = document.querySelector('[data-test-subj="confirm-tenant"], .euiModalFooter button.euiButton--fill');
                if (btn) btn.click();
            }""")
            time.sleep(2)
        except Exception:
            pass
            
        # Wait for log records and histogram to render
        time.sleep(6)
        
        target_file = OUT / "02_opensearch_siem.png"
        page.screenshot(path=str(target_file), full_page=False)
        print(f"[+] Saved OpenSearch SIEM screenshot: {target_file}")
    except Exception as e:
        print(f"[-] OpenSearch capture failed: {e}")
        try:
            page.goto("http://localhost:5601/app/home", timeout=15000)
            time.sleep(3)
            page.screenshot(path=str(OUT / "02_opensearch_siem.png"))
            print(f"[+] Saved OpenSearch fallback screenshot.")
        except Exception as e2:
            print(f"[-] OpenSearch fallback failed: {e2}")
    finally:
        page.close()

def capture_caldera_user(browser, username, password, output_filename, section_args=None, is_main=False):
    print(f"[*] Capturing MITRE Caldera for user '{username}' -> {output_filename}...")
    context = browser.new_context(
        viewport={"width": 1680, "height": 1050},
        device_scale_factor=1,
        ignore_https_errors=True
    )
    page = context.new_page()
    try:
        # Caldera login
        page.goto("http://localhost:8888/login", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        
        # Fill credentials
        if page.query_selector('input[name="username"]') or page.query_selector('input[type="text"]'):
            print(f"    Entering credentials for {username}...")
            page.fill('input[name="username"], input[type="text"]', username)
            page.fill('input[name="password"], input[type="password"]', password)
            page.click('button[type="submit"], input[type="submit"]')
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)
            
        page.goto("http://localhost:8888/", wait_until="networkidle", timeout=30000)
        time.sleep(2)
        
        if section_args:
            name, address = section_args
            print(f"    Opening specific section: {name} ({address})...")
            try:
                page.evaluate(f"viewSection('{name}', '{address}')")
                time.sleep(3)
                
                # If opening profiles, select an adversary to populate abilities
                if name == "profiles":
                    dropdown = page.query_selector("select#profile-existing-name, select")
                    if dropdown:
                        dropdown.select_option(index=1)
                        time.sleep(2)
            except Exception as eval_err:
                print(f"    viewSection eval failed: {eval_err}")
                try:
                    page.evaluate("openNav()")
                    time.sleep(1)
                except Exception:
                    pass
        else:
            try:
                page.evaluate("openNav()")
                time.sleep(1)
            except Exception:
                pass
        
        target_file = OUT / output_filename
        page.screenshot(path=str(target_file), full_page=False)
        print(f"[+] Saved Caldera ({username}) screenshot: {target_file}")
        
        if is_main:
            main_target = OUT / "07_caldera_attack.png"
            page.screenshot(path=str(main_target), full_page=False)
            print(f"[+] Saved Caldera hero screenshot: {main_target}")
    except Exception as e:
        print(f"[-] Caldera capture failed for {username}: {e}")
    finally:
        page.close()
        context.close()

def capture_caldera(browser):
    # 1. Administrator: Configurations, Plugins & Server Management View
    capture_caldera_user(browser, "admin", "admin123", "07_caldera_admin.png", section_args=("configurations", "/advanced/configurations"))
    
    # 2. Red Team Operator: Adversary Profiles & ATT&CK Abilities Campaign
    capture_caldera_user(browser, "red", "RedTeamPass123!", "07_caldera_red.png", section_args=("profiles", "/campaign/profiles"), is_main=True)
    
    # 3. Blue Team Defender: Incident Response, Defensive Agents & Gameboard Matrix
    capture_caldera_user(browser, "blue", "BlueTeamPass123!", "07_caldera_blue.png", section_args=("gameboard", "/plugin/gameboard/gui"))

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
        capture_caldera(browser)
        capture_velociraptor(context)
        
        browser.close()
        print("[*] All native live tool screenshots captured successfully!")

if __name__ == "__main__":
    main()
