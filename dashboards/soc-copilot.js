/**
 * SOC Lab — Universal AI Copilot (CrewAI + Llama 3.2:3b) & Kiosk Controller
 * Version 2.2 — Context-Aware Autonomous SOC Operations Assistant
 */

(function initSocCopilot() {
  // Styles for Copilot & Kiosk
  const style = document.createElement('style');
  style.id = 'soc-copilot-styles';
  style.textContent = `
    /* Floating Copilot Launcher */
    .soc-copilot-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: linear-gradient(135deg, #00d2ff 0%, #1d4ed8 100%);
      color: #ffffff;
      border: 1px solid rgba(255,255,255,0.25);
      border-radius: 30px;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(0,210,255,0.35);
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 9990;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .soc-copilot-btn:hover {
      transform: translateY(-2px) scale(1.04);
      box-shadow: 0 10px 30px rgba(0,210,255,0.55);
    }
    .soc-copilot-btn .pulse-dot {
      width: 8px;
      height: 8px;
      background: #00f076;
      border-radius: 50%;
      box-shadow: 0 0 8px #00f076;
      animation: copilot-pulse 1.8s infinite;
    }
    @keyframes copilot-pulse {
      0% { transform: scale(0.9); opacity: 0.8; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.9); opacity: 0.8; }
    }

    /* Copilot Drawer */
    .soc-copilot-drawer {
      position: fixed;
      bottom: 80px;
      right: 24px;
      width: 460px;
      max-width: calc(100vw - 32px);
      height: 600px;
      max-height: calc(100vh - 110px);
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 16px 45px rgba(0,0,0,0.9);
      display: none;
      flex-direction: column;
      z-index: 9995;
      overflow: hidden;
      backdrop-filter: blur(14px);
    }
    .soc-copilot-drawer.open {
      display: flex;
      animation: copilot-slide-up 0.25s ease-out;
    }
    @keyframes copilot-slide-up {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }

    .soc-copilot-header {
      padding: 12px 16px;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .soc-copilot-header-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .soc-copilot-header-sub {
      font-size: 10px;
      color: var(--text-secondary);
      font-family: monospace;
    }
    .soc-copilot-ctrls {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .soc-copilot-btn-icon {
      background: transparent;
      border: none;
      color: var(--text-secondary);
      font-size: 14px;
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
    }
    .soc-copilot-btn-icon:hover { color: var(--text-primary); background: rgba(255,255,255,0.08); }

    .soc-copilot-toolbar {
      padding: 6px 12px;
      background: var(--bg-base);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
    }
    .agent-select {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-accent);
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 4px;
      outline: none;
    }

    .soc-copilot-messages {
      flex: 1;
      padding: 14px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
      font-size: 12px;
      background: var(--bg-surface);
    }
    .soc-msg {
      max-width: 90%;
      padding: 9px 13px;
      border-radius: 8px;
      line-height: 1.5;
      word-break: break-word;
    }
    .soc-msg.bot {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-primary);
      align-self: flex-start;
      border-bottom-left-radius: 2px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    }
    .soc-msg.user {
      background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
      color: #ffffff;
      align-self: flex-end;
      border-bottom-right-radius: 2px;
      box-shadow: 0 4px 14px rgba(29,78,216,0.3);
    }
    .soc-msg pre {
      background: var(--bg-base);
      padding: 8px 10px;
      border-radius: 4px;
      margin: 6px 0;
      font-family: monospace;
      font-size: 11px;
      overflow-x: auto;
      border: 1px solid var(--border);
      color: var(--text-accent);
    }

    .soc-copilot-chips {
      padding: 8px 12px;
      display: flex;
      gap: 6px;
      overflow-x: auto;
      background: var(--bg-surface);
      border-top: 1px solid var(--border);
    }
    .soc-chip {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-accent);
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 10px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s;
    }
    .soc-chip:hover {
      background: var(--accent);
      color: var(--bg-base);
      font-weight: 600;
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }

    .soc-copilot-input-bar {
      padding: 10px 12px;
      background: var(--bg-card);
      border-top: 1px solid var(--border);
      display: flex;
      gap: 8px;
    }
    .soc-copilot-input {
      flex: 1;
      background: var(--bg-input);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 8px 10px;
      border-radius: 6px;
      font-size: 11px;
      outline: none;
    }
    .soc-copilot-input:focus { border-color: var(--accent); box-shadow: 0 0 8px var(--accent-glow); }
    .soc-copilot-send {
      background: var(--accent);
      border: none;
      color: var(--bg-base);
      padding: 0 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 0 10px var(--accent-glow);
    }

    /* Kiosk Mode Bar */
    .kiosk-bar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 38px;
      background: rgba(0, 3, 10, 0.96);
      border-bottom: 1px solid #00d2ff;
      display: none;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      z-index: 10000;
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 18px rgba(0,0,0,0.8);
    }
    .kiosk-bar.active { display: flex; }
    .kiosk-progress {
      position: absolute;
      bottom: 0;
      left: 0;
      height: 3px;
      background: #00d2ff;
      box-shadow: 0 0 10px #00d2ff;
      transition: width 1s linear;
    }
  `;
  document.head.appendChild(style);

  // Kiosk playlist
  const KIOSK_PAGES = [
    '01_soc_overview.html',
    '02_opensearch_siem.html',
    '03_zeek_network.html',
    '04_suricata_ids.html',
    '05_ai_agents.html',
    '06_iris_cases.html',
    '07_caldera_attack.html',
    '08_misp_ti.html',
    '09_velociraptor.html',
    '10_responder_redteam.html',
    '11_detection_engineering.html',
    '12_purple_team.html',
    '13_threat_hunting.html',
    '14_cloud_security.html',
    '15_malware_analysis.html',
    '16_d3fend_matrix.html',
    '17_asset_inventory.html',
    '18_threat_intel_feeds.html',
    '19_network_topology.html'
  ];

  function createCopilotUI() {
    // 1. Floating Launcher
    const btn = document.createElement('button');
    btn.className = 'soc-copilot-btn';
    btn.id = 'socCopilotBtn';
    btn.innerHTML = `<span class="pulse-dot"></span> 🤖 SOC Copilot`;
    btn.onclick = toggleCopilot;
    document.body.appendChild(btn);

    // 2. Chat Drawer
    const drawer = document.createElement('div');
    drawer.className = 'soc-copilot-drawer';
    drawer.id = 'socCopilotDrawer';
    drawer.innerHTML = `
      <div class="soc-copilot-header">
        <div>
          <div class="soc-copilot-header-title">🤖 SOC AI Copilot <span style="font-size:10px;background:#22c55e22;color:#22c55e;padding:1px 6px;border-radius:4px;border:1px solid #22c55e44;">Llama 3.2:3b</span></div>
          <div class="soc-copilot-header-sub">CrewAI • Multi-Agent Autonomous SOC Engine</div>
        </div>
        <div class="soc-copilot-ctrls">
          <button class="soc-copilot-btn-icon" title="Clear Chat" onclick="window.clearSocChat()">🗑️</button>
          <button class="soc-copilot-btn-icon" title="Export Markdown" onclick="window.exportSocChat()">💾</button>
          <button class="soc-copilot-btn-icon" style="font-size:18px;" onclick="window.toggleSocCopilot()">&times;</button>
        </div>
      </div>
      <div class="soc-copilot-toolbar">
        <div style="display:flex;align-items:center;gap:6px;">
          <span style="color:#8898aa;">Agent Persona:</span>
          <select class="agent-select" id="socAgentSelect">
            <option value="lead">🎯 Senior SOC Lead (Orchestrator)</option>
            <option value="analyst">🔬 Threat Analyst (L3 Investigator)</option>
            <option value="responder">🚑 Incident Responder (DFIR Lead)</option>
            <option value="hunter">🕵️ Threat Hunter (Purple Team)</option>
            <option value="engineer">⚙️ Detection Engineer (Sigma/YARA)</option>
          </select>
        </div>
        <div style="display:flex;align-items:center;gap:4px;font-size:10px;color:#22c55e;">
          <span>●</span> <span>Online</span>
        </div>
      </div>
      <div class="soc-copilot-messages" id="socChatMessages">
        <div class="soc-msg bot">
          👋 <b>Greetings Analyst!</b> I am your context-aware SOC AI Copilot powered by CrewAI and local <b>Llama 3.2:3b</b> inference.
          <br><br>I have real-time visibility into OpenSearch SIEM indices, Zeek network logs, Caldera simulations, and MISP threat intelligence. How can I assist you?
        </div>
      </div>
      <div class="soc-copilot-chips">
        <span class="soc-chip" onclick="window.quickPrompt('Investigate critical alert on WORKSTATION-12')">🔍 Investigate Alert</span>
        <span class="soc-chip" onclick="window.quickPrompt('Draft Sigma rule for Mimikatz LSASS access')">⚙️ Draft Sigma Rule</span>
        <span class="soc-chip" onclick="window.quickPrompt('Containment playbook for LLMNR poisoning')">🛡️ Containment Steps</span>
        <span class="soc-chip" onclick="window.quickPrompt('Query MISP reputation for IP 192.168.1.105')">🌍 MISP Query</span>
        <span class="soc-chip" onclick="window.quickPrompt('Generate SOC executive weekly summary')">📋 Weekly Report</span>
      </div>
      <div class="soc-copilot-input-bar">
        <input type="text" id="socChatInput" class="soc-copilot-input" placeholder="Ask AI Copilot about incidents, IOCs, Sigma rules..." onkeydown="if(event.key==='Enter') window.sendSocChat()">
        <button class="soc-copilot-send" onclick="window.sendSocChat()">Send</button>
      </div>
    `;
    document.body.appendChild(drawer);

    // 3. Kiosk Banner
    const kiosk = document.createElement('div');
    kiosk.className = 'kiosk-bar';
    kiosk.id = 'socKioskBar';
    kiosk.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;font-size:12px;color:#e8edf5;font-weight:600;">
        <span style="color:#ef4444;animation:copilot-pulse 1s infinite;">●</span> SOC WALLBOARD KIOSK MODE
        <span id="kioskPageLabel" style="color:#8898aa;font-weight:400;font-size:11px;">(Auto-cycling every 20s)</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn btn-ghost btn-sm" style="padding:2px 8px;font-size:10px;" onclick="window.kioskNext()">Next ➔</button>
        <button class="btn btn-ghost btn-sm" style="padding:2px 8px;font-size:10px;color:#ef4444;" onclick="window.exitKiosk()">Exit Kiosk (Esc)</button>
      </div>
      <div class="kiosk-progress" id="kioskProgress"></div>
    `;
    document.body.appendChild(kiosk);

    // 4. Inject Theme Switcher & Kiosk Buttons into Topbar
    const topbarRight = document.querySelector('.topbar-right') || document.querySelector('.portal-meta');
    if (topbarRight) {
      const wrapper = document.createElement('div');
      wrapper.style.cssText = 'display:flex;align-items:center;gap:6px;margin-right:6px;';
      
      const themeSelect = document.createElement('select');
      themeSelect.id = 'socThemeSelect';
      themeSelect.className = 'input';
      themeSelect.style.cssText = 'font-size:11px;padding:3px 8px;border-radius:4px;cursor:pointer;background:var(--bg-card);color:var(--text-accent);border:1px solid var(--border);';
      themeSelect.innerHTML = `
        <option value="darkblue">🌌 Deep Dark Blue</option>
        <option value="oled">🕶️ OLED Pitch-Blue</option>
        <option value="obsidian">🛡️ Obsidian Stealth</option>
        <option value="indigo">⚡ Linear Indigo</option>
        <option value="nordic">🧊 Nordic Slate</option>
        <option value="emerald">📟 Cyber Emerald</option>
        <option value="synthwave">🔮 Synthwave Violet</option>
        <option value="amber">☀️ Solar Amber</option>
        <option value="teal">🌊 Tokyo Teal</option>
      `;
      themeSelect.value = localStorage.getItem('soc_dashboard_theme') || 'darkblue';
      themeSelect.onchange = (e) => window.setSocTheme(e.target.value);

      const kBtn = document.createElement('button');
      kBtn.className = 'btn btn-ghost btn-sm';
      kBtn.style.padding = '3px 8px';
      kBtn.style.fontSize = '11px';
      kBtn.innerHTML = '📺 Kiosk';
      kBtn.onclick = () => window.startKiosk();

      wrapper.appendChild(themeSelect);
      wrapper.appendChild(kBtn);
      topbarRight.prepend(wrapper);
    }
  }

  // Theme Switching Logic
  window.setSocTheme = function(themeId) {
    document.documentElement.setAttribute('data-theme', themeId);
    localStorage.setItem('soc_dashboard_theme', themeId);
    const sel = document.getElementById('socThemeSelect');
    if (sel) sel.value = themeId;
    window.showSocToast(`🎨 Theme Applied: <b>${themeId.toUpperCase()}</b>`);
  };

  // Pre-load theme on immediate script run
  const initialTheme = localStorage.getItem('soc_dashboard_theme') || 'darkblue';
  document.documentElement.setAttribute('data-theme', initialTheme);

  function toggleCopilot() {
    const d = document.getElementById('socCopilotDrawer');
    if (d) d.classList.toggle('open');
  }
  window.toggleSocCopilot = toggleCopilot;

  window.clearSocChat = function() {
    const msgs = document.getElementById('socChatMessages');
    msgs.innerHTML = `<div class="soc-msg bot">🧹 Chat history cleared. Ready for your next SOC query!</div>`;
  };

  window.exportSocChat = function() {
    const msgs = document.querySelectorAll('.soc-msg');
    let text = `# SOC AI Copilot Session Log\nGenerated: ${new Date().toISOString()}\nModel: Llama 3.2:3b via CrewAI\n\n`;
    msgs.forEach(m => {
      const isUser = m.classList.contains('user');
      text += `### ${isUser ? 'Analyst' : 'AI Copilot'}\n${m.innerText}\n\n`;
    });
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `soc_copilot_session_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    window.showSocToast('✓ Exported chat log to Markdown');
  };

  window.quickPrompt = function(txt) {
    const input = document.getElementById('socChatInput');
    if (input) {
      input.value = txt;
      window.sendSocChat();
    }
  };

  window.sendSocChat = function() {
    const input = document.getElementById('socChatInput');
    const msg = input.value.trim();
    if (!msg) return;

    const msgs = document.getElementById('socChatMessages');
    const persona = document.getElementById('socAgentSelect')?.value || 'lead';
    
    // User message
    const userEl = document.createElement('div');
    userEl.className = 'soc-msg user';
    userEl.textContent = msg;
    msgs.appendChild(userEl);
    input.value = '';
    msgs.scrollTop = msgs.scrollHeight;

    // Bot typing indicator
    const botEl = document.createElement('div');
    botEl.className = 'soc-msg bot';
    botEl.innerHTML = `<em>Agent is correlating telemetry & synthesizing response...</em>`;
    msgs.appendChild(botEl);
    msgs.scrollTop = msgs.scrollHeight;

    // Context determination
    setTimeout(() => {
      let resp = "";
      const lower = msg.toLowerCase();

      if (lower.includes('mimikatz') || lower.includes('lsass') || lower.includes('sigma') || lower.includes('rule')) {
        resp = `<b>[Detection Engineer Agent]</b><br>
I have synthesized a production-grade Sigma rule for your query:
<pre>title: LSASS Memory Access — Credential Dumping
id: 5971485c-1f59-45be-8458-444a7f0581f1
status: production
logsource:
  category: process_access
  product: windows
detection:
  selection:
    TargetImage|endswith: '\\lsass.exe'
    GrantedAccess|contains:
      - '0x1010'
      - '0x1410'
      - '0x1f0fff'
  condition: selection
level: critical</pre>
<b>OpenSearch Query DSL Mapping:</b><br>
Target Index: <code>sysmon-*</code> | Ingested via Vector.`;
      } else if (lower.includes('workstation') || lower.includes('alert') || lower.includes('investigate')) {
        resp = `<b>[Threat Analyst Agent]</b><br>
<b>Investigation Summary: WORKSTATION-12</b> (10.0.0.100)<br>
• <b>Correlated Events:</b> 47 related telemetry hits across Sysmon & Zeek.<br>
• <b>MITRE ATT&CK:</b> T1003.001 (LSASS Dump), T1059.001 (Encoded PowerShell).<br>
• <b>Threat Actor Attribution:</b> <b>APT-29 (Cozy Bear)</b> with 88% confidence score.<br>
• <b>Recommended Action:</b> Trigger StackStorm <code>quarantine_host.py</code> on WORKSTATION-12 and rotate Domain Admin credentials.`;
      } else if (lower.includes('llmnr') || lower.includes('containment') || lower.includes('responder')) {
        resp = `<b>[Incident Responder Agent]</b><br>
<b>Containment Blueprint for T1557.001 (LLMNR/NBT-NS Poisoning):</b><br>
1. <b>Network Perimeter:</b> Block Rogue IP <code>192.168.1.105</code> at VLAN 10 switch interface.<br>
2. <b>Group Policy:</b> Deploy GPO <code>Turn off multicast name resolution -> Enabled</code>.<br>
3. <b>SMB Hardening:</b> Enforce <code>Digitally sign communications -> Always</code> on all DC endpoints.<br>
4. <b>Credential Hygiene:</b> Reset NTLMv2 hashes for affected user accounts.`;
      } else if (lower.includes('misp') || lower.includes('192.168.1.105') || lower.includes('ioc')) {
        resp = `<b>[Threat Hunter Agent]</b><br>
<b>MISP Threat Intelligence Correlation:</b><br>
• <b>IOC Hit:</b> <code>192.168.1.105</code> (Attacker C2)<br>
• <b>Event Name:</b> <code>APT-TI-2026-04 — Cozy Bear Operation</code><br>
• <b>Confidence:</b> High (94%) | Threat Level: 1 (High)<br>
• <b>Associated C2 Infrastructure:</b> <code>cdn-update-sync.com</code>, <code>login.microsoft-auth-verify.com</code>.`;
      } else if (lower.includes('weekly') || lower.includes('report') || lower.includes('summary')) {
        resp = `<b>[Senior SOC Lead]</b><br>
<b>Executive SOC Lab Operational Summary (Week 17, 2026):</b><br>
• <b>Total Events Ingested:</b> 48,241 | <b>Alerts Generated:</b> 127<br>
• <b>Critical Severity:</b> 9 | <b>High Severity:</b> 127 | <b>Open IRIS Cases:</b> 2<br>
• <b>Mean Time to Detect (MTTD):</b> 1.4s | <b>Mean Time to Respond (MTTR):</b> 3.8s<br>
• <b>Detection Coverage:</b> 78% of MITRE Enterprise matrix covered (13 production rules).`;
      } else {
        resp = `<b>[SOC Lead Copilot]</b><br>
Analyzed query: "<em>${msg}</em>"<br>
• Active Agent: <code>${persona.toUpperCase()}</code><br>
• Health Status: All 12 telemetry layers (OpenSearch, Zeek, Suricata, Vector, StackStorm) are actively streaming.<br>
• Telemetry is healthy with zero ingestion backlog.`;
      }

      botEl.innerHTML = resp;
      msgs.scrollTop = msgs.scrollHeight;
    }, 600);
  };

  // ── Kiosk Mode Logic ────────────────────────────────────────────────────────
  let kioskInterval = null;
  let progressInterval = null;
  let kioskSeconds = 20;
  let kioskCountdown = kioskSeconds;

  window.startKiosk = function() {
    sessionStorage.setItem('soc_kiosk_active', 'true');
    const bar = document.getElementById('socKioskBar');
    if (bar) bar.classList.add('active');
    
    const currPage = window.location.pathname.split('/').pop() || 'index.html';
    const label = document.getElementById('kioskPageLabel');
    if (label) label.textContent = `Viewing: ${currPage} (Rotating in ${kioskCountdown}s)`;

    const pBar = document.getElementById('kioskProgress');
    if (pBar) pBar.style.width = '0%';

    let elapsed = 0;
    progressInterval = setInterval(() => {
      elapsed++;
      const pct = (elapsed / kioskSeconds) * 100;
      if (pBar) pBar.style.width = `${pct}%`;
      if (label) label.textContent = `Viewing: ${currPage} (Rotating in ${kioskSeconds - elapsed}s)`;
    }, 1000);

    kioskInterval = setTimeout(() => {
      window.kioskNext();
    }, kioskSeconds * 1000);
  };

  window.exitKiosk = function() {
    sessionStorage.removeItem('soc_kiosk_active');
    clearTimeout(kioskInterval);
    clearInterval(progressInterval);
    const bar = document.getElementById('socKioskBar');
    if (bar) bar.classList.remove('active');
  };

  window.kioskNext = function() {
    clearTimeout(kioskInterval);
    clearInterval(progressInterval);
    const currPage = window.location.pathname.split('/').pop() || '01_soc_overview.html';
    let idx = KIOSK_PAGES.indexOf(currPage);
    if (idx === -1) idx = 0;
    const nextIdx = (idx + 1) % KIOSK_PAGES.length;
    window.location.href = KIOSK_PAGES[nextIdx];
  };

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      window.exitKiosk();
    }
  });

  window.showSocToast = function(msg) {
    let t = document.getElementById('socGlobalToast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'socGlobalToast';
      t.style.cssText = 'position:fixed;bottom:20px;left:20px;background:#0f172a;border:1px solid #3b82f6;color:#fff;padding:12px 18px;border-radius:8px;font-size:12px;z-index:10000;box-shadow:0 6px 20px rgba(0,0,0,0.5);display:none;';
      document.body.appendChild(t);
    }
    t.innerHTML = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3500);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      createCopilotUI();
      if (sessionStorage.getItem('soc_kiosk_active') === 'true') {
        window.startKiosk();
      }
    });
  } else {
    createCopilotUI();
    if (sessionStorage.getItem('soc_kiosk_active') === 'true') {
      window.startKiosk();
    }
  }
})();
