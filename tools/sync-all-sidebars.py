import os
import re
import glob

DASHBOARD_DIR = "dashboards"

# 9 Core Enterprise SOC Operations Tiers
CORE_TIERS = [
    ("01_soc_command_center.html", "📊", "01 SOC Command Center"),
    ("02_incident_operations.html", "🚨", "02 Incident Operations"),
    ("03_detection_engineering.html", "🛠️", "03 Detection Engineering"),
    ("04_mitre_attack.html", "⚡", "04 MITRE ATT&CK Matrix"),
    ("05_threat_hunting.html", "🔎", "05 Threat Hunting Sandbox"),
    ("06_network_security.html", "🌐", "06 Network Security & NSM"),
    ("07_endpoint_security.html", "🖥️", "07 Endpoint Security"),
    ("08_ai_soc.html", "🤖", "08 Autonomous AI SOC"),
    ("09_platform_health.html", "💚", "09 Platform Health"),
]

# Specialized Deep Dive Engines
SPECIALIZED_ENGINES = [
    ("02_opensearch_siem.html", "🔍", "OpenSearch SIEM"),
    ("03_zeek_network.html", "📡", "Zeek NSM Evidence"),
    ("04_suricata_ids.html", "🛡️", "Suricata IDS / IPS"),
    ("05_ai_agents.html", "🧠", "CrewAI Multi-Agent"),
    ("06_iris_cases.html", "📋", "DFIR-IRIS Cases"),
    ("07_caldera_attack.html", "⚔️", "Caldera Adversary Sim"),
    ("08_misp_ti.html", "🌍", "MISP Threat Intel"),
    ("09_velociraptor.html", "🦖", "Velociraptor VQL"),
    ("10_responder_redteam.html", "🎭", "Responder Red Team"),
    ("12_purple_team.html", "🎯", "Purple Team Matrix"),
    ("14_cloud_security.html", "☁️", "Cloud Security SOC"),
    ("15_malware_analysis.html", "🧬", "Malware & YARA"),
    ("16_d3fend_matrix.html", "🛡️", "MITRE D3FEND"),
    ("17_asset_inventory.html", "🖥️", "Asset Inventory"),
    ("18_threat_intel_feeds.html", "📡", "Threat Feeds Hub"),
    ("19_network_topology.html", "🗺️", "Network Topology"),
]

def generate_nav_html(current_filename):
    lines = ['      <ul class="sidebar-nav">']
    lines.append('        <li class="sidebar-section-header" style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;padding:8px 12px 4px;">Enterprise SOC Tiers</li>')
    for href, icon, label in CORE_TIERS:
        active_str = ' class="active"' if href == current_filename or (current_filename == '01_soc_overview.html' and href == '01_soc_command_center.html') else ''
        lines.append(f'        <li class="nav-item"><a href="{href}"{active_str}><span class="nav-icon">{icon}</span><span>{label}</span></a></li>')
    
    lines.append('        <li class="sidebar-section-header" style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;padding:12px 12px 4px;border-top:1px solid var(--border);margin-top:8px;">Specialized Engines</li>')
    for href, icon, label in SPECIALIZED_ENGINES:
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

    print(f"\n[+] Successfully synchronized sidebars across {updated_count} dashboard files.")

if __name__ == "__main__":
    sync_sidebars()
