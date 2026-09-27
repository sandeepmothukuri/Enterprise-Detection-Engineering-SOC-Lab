import os
import re
import glob

DASHBOARD_DIR = "dashboards"

NAV_ITEMS = [
    ("01_soc_overview.html", "📊", "SOC Overview"),
    ("02_opensearch_siem.html", "🔍", "OpenSearch SIEM"),
    ("03_zeek_network.html", "🌐", "Zeek Network"),
    ("04_suricata_ids.html", "🚨", "Suricata IDS"),
    ("05_ai_agents.html", "🤖", "AI Agents"),
    ("06_iris_cases.html", "📋", "DFIR-IRIS"),
    ("07_caldera_attack.html", "⚔️", "Caldera"),
    ("08_misp_ti.html", "🌍", "MISP Intel"),
    ("09_velociraptor.html", "🦖", "Velociraptor"),
    ("10_responder_redteam.html", "🎭", "Responder"),
    ("11_detection_engineering.html", "🛠️", "Detection Eng"),
    ("12_purple_team.html", "🎯", "Purple Team"),
    ("13_threat_hunting.html", "🔎", "Threat Hunting"),
    ("14_cloud_security.html", "☁️", "Cloud SOC"),
    ("15_malware_analysis.html", "🧬", "Malware &amp; YARA"),
    ("16_d3fend_matrix.html", "🛡️", "MITRE D3FEND"),
    ("17_asset_inventory.html", "🖥️", "Asset &amp; EDR Health"),
    ("18_threat_intel_feeds.html", "📡", "Threat Feeds Hub"),
    ("19_network_topology.html", "🗺️", "Network Topology"),
]

def generate_nav_html(current_filename):
    lines = ['      <ul class="sidebar-nav">']
    for href, icon, label in NAV_ITEMS:
        active_str = ' class="active"' if href == current_filename else ''
        lines.append(f'        <li class="nav-item"><a href="{href}"{active_str}><span class="nav-icon">{icon}</span><span>{label}</span></a></li>')
    lines.append('      </ul>')
    return "\n".join(lines)

def sync_sidebars():
    pattern = os.path.join(DASHBOARD_DIR, "[0-9][0-9]_*.html")
    files = glob.glob(pattern)
    updated_count = 0
    
    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_nav = generate_nav_html(fname)
        # Match <ul class="sidebar-nav">...</ul>
        replaced_content, count = re.subn(
            r'<ul class="sidebar-nav">.*?</ul>',
            new_nav,
            content,
            flags=re.DOTALL
        )
        
        if count > 0:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(replaced_content)
            print(f"[+] Synchronized sidebar in {fname}")
            updated_count += 1
        else:
            print(f"[-] No sidebar-nav tag found in {fname}")

    print(f"\n[+] Successfully updated {updated_count} dashboard files with complete 19-page navigation.")

if __name__ == "__main__":
    sync_sidebars()
