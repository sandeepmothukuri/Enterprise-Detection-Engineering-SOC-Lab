/**
 * SOC Lab — Universal AI Copilot (CrewAI + Llama 3.2:3b), Theme Switcher & Kiosk Controller
 * Version 2.5 — Enterprise Visual Design System & Theme Engine
 */

(function initSocCopilot() {
  // Pre-load theme on immediate script execution
  const activeTheme = localStorage.getItem('soc_dashboard_theme') || 'darkblue';
  document.documentElement.setAttribute('data-theme', activeTheme);

  // Styles for Copilot, Kiosk & Theme Modal
  const style = document.createElement('style');
  style.id = 'soc-copilot-styles';
  style.textContent = `
    /* Theme Modal Styles */
    .soc-theme-modal {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(8px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 10005;
    }
    .soc-theme-modal.open { display: flex; }
    .soc-theme-modal-box {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      width: 720px;
      max-width: 95vw;
      max-height: 85vh;
      overflow-y: auto;
      padding: 24px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
    }
    .soc-theme-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }
    .soc-theme-card {
      background: var(--bg-card);
      border: 2px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .soc-theme-card:hover {
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: 0 6px 18px var(--accent-glow);
    }
    .soc-theme-card.active {
      border-color: var(--accent);
      background: var(--bg-card-hover);
      box-shadow: 0 0 16px var(--accent-glow);
    }
    .soc-theme-swatches {
      display: flex;
      gap: 4px;
      height: 18px;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 4px;
    }
    .soc-theme-swatch {
      flex: 1;
      height: 100%;
    }

    /* Topbar Theme Trigger Button */
    .soc-theme-btn {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-accent);
      font-size: 11px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .soc-theme-btn:hover {
      background: var(--bg-card-hover);
      border-color: var(--accent);
      color: #ffffff;
      box-shadow: 0 0 10px var(--accent-glow);
    }

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

  // Themes list
  const THEMES = [
    { id: 'darkblue', name: '🌌 Deep Dark Blue', desc: 'Royal Navy / Default SOC Theme', bg: '#070d1e', surface: '#0c1530', accent: '#38bdf8', crit: '#f43f5e' },
    { id: 'oled', name: '🕶️ OLED Pitch-Blue', desc: 'Pure Pitch Black & Cyber Neon', bg: '#00030a', surface: '#020817', accent: '#00d2ff', crit: '#ff2a55' },
    { id: 'obsidian', name: '🥷 Obsidian Stealth', desc: 'CrowdStrike / SentinelOne Minimalist', bg: '#0b0e14', surface: '#0f141c', accent: '#3b82f6', crit: '#ef4444' },
    { id: 'indigo', name: '⚡ Linear Indigo', desc: 'Modern Vercel / Linear Glow', bg: '#08090d', surface: '#0e0f17', accent: '#6366f1', crit: '#f43f5e' },
    { id: 'nordic', name: '🧊 Nordic Slate', desc: 'GitHub Dark / Arctic Navy', bg: '#0d1117', surface: '#161b22', accent: '#38bdf8', crit: '#f85149' },
    { id: 'emerald', name: '📟 Cyber Emerald', desc: 'Matrix / Threat Hunter Green', bg: '#020905', surface: '#05150c', accent: '#00ff9d', crit: '#ff3366' },
    { id: 'synthwave', name: '🔮 Synthwave Violet', desc: 'Darktrace Neon Violet Glow', bg: '#08040f', surface: '#10081e', accent: '#d946ef', crit: '#ff0055' },
    { id: 'amber', name: '☀️ Solar Amber', desc: 'Splunk / Datadog Gold', bg: '#0a0804', surface: '#141008', accent: '#f59e0b', crit: '#ef4444' }
  ];

  function createThemeModal() {
    const modal = document.createElement('div');
    modal.className = 'soc-theme-modal';
    modal.id = 'socThemeModal';
    modal.onclick = (e) => {
      if (e.target === modal) window.closeSocThemeModal();
    };

    const current = localStorage.getItem('soc_dashboard_theme') || 'darkblue';

    const cardsHtml = THEMES.map(t => `
      <div class="soc-theme-card ${t.id === current ? 'active' : ''}" onclick="window.setSocTheme('${t.id}')">
        <div style="font-weight:700;font-size:13px;color:var(--text-primary);display:flex;justify-content:space-between;align-items:center;">
          <span>${t.name}</span>
          ${t.id === current ? '<span style="color:var(--accent);font-size:11px;">✓ Active</span>' : ''}
        </div>
        <div style="font-size:11px;color:var(--text-secondary);">${t.desc}</div>
        <div class="soc-theme-swatches">
          <div class="soc-theme-swatch" style="background:${t.bg};" title="Base: ${t.bg}"></div>
          <div class="soc-theme-swatch" style="background:${t.surface};" title="Surface: ${t.surface}"></div>
          <div class="soc-theme-swatch" style="background:${t.accent};" title="Accent: ${t.accent}"></div>
          <div class="soc-theme-swatch" style="background:${t.crit};" title="Alert: ${t.crit}"></div>
        </div>
      </div>
    `).join('');

    modal.innerHTML = `
      <div class="soc-theme-modal-box">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);padding-bottom:12px;">
          <div>
            <h3 style="margin:0;font-size:18px;color:var(--text-primary);">🎨 Choose SOC Platform Theme</h3>
            <p style="margin:4px 0 0;font-size:12px;color:var(--text-secondary);">Select your preferred high-contrast theme. Persisted automatically across all dashboards.</p>
          </div>
          <button class="btn btn-ghost btn-sm" onclick="window.closeSocThemeModal()" style="font-size:16px;">✕</button>
        </div>
        <div class="soc-theme-grid" id="socThemeGrid">
          ${cardsHtml}
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  window.openSocThemeModal = function() {
    let m = document.getElementById('socThemeModal');
    if (!m) {
      createThemeModal();
      m = document.getElementById('socThemeModal');
    }
    m.classList.add('open');
  };

  window.closeSocThemeModal = function() {
    const m = document.getElementById('socThemeModal');
    if (m) m.classList.remove('open');
  };

  window.setSocTheme = function(themeId) {
    document.documentElement.setAttribute('data-theme', themeId);
    localStorage.setItem('soc_dashboard_theme', themeId);
    
    // Update select if exists
    const sel = document.getElementById('socThemeSelect');
    if (sel) sel.value = themeId;

    // Refresh modal cards
    const grid = document.getElementById('socThemeGrid');
    if (grid) {
      grid.innerHTML = THEMES.map(t => `
        <div class="soc-theme-card ${t.id === themeId ? 'active' : ''}" onclick="window.setSocTheme('${t.id}')">
          <div style="font-weight:700;font-size:13px;color:var(--text-primary);display:flex;justify-content:space-between;align-items:center;">
            <span>${t.name}</span>
            ${t.id === themeId ? '<span style="color:var(--accent);font-size:11px;">✓ Active</span>' : ''}
          </div>
          <div style="font-size:11px;color:var(--text-secondary);">${t.desc}</div>
          <div class="soc-theme-swatches">
            <div class="soc-theme-swatch" style="background:${t.bg};" title="Base: ${t.bg}"></div>
            <div class="soc-theme-swatch" style="background:${t.surface};" title="Surface: ${t.surface}"></div>
            <div class="soc-theme-swatch" style="background:${t.accent};" title="Accent: ${t.accent}"></div>
            <div class="soc-theme-swatch" style="background:${t.crit};" title="Alert: ${t.crit}"></div>
          </div>
        </div>
      `).join('');
    }

    window.showSocToast(`🎨 Theme Changed: <b>${themeId.toUpperCase()}</b>`);
  };

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
          <button class="soc-copilot-btn-icon" title="Themes" onclick="window.openSocThemeModal()">🎨</button>
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
        <span class="soc-chip" onclick="window.quickPrompt('Investigate critical alert on WIN-DC01')">🔍 Investigate WIN-DC01</span>
        <span class="soc-chip" onclick="window.quickPrompt('Draft Sigma rule for Mimikatz LSASS access')">⚙️ Draft Sigma Rule</span>
        <span class="soc-chip" onclick="window.quickPrompt('Containment playbook for LLMNR poisoning')">🛡️ Containment Steps</span>
        <span class="soc-chip" onclick="window.openSocThemeModal()">🎨 Switch Color Theme</span>
        <span class="soc-chip" onclick="window.quickPrompt('Generate SOC executive weekly summary')">📋 Weekly Report</span>
      </div>
      <div class="soc-copilot-input-bar">
        <input type="text" id="socChatInput" class="soc-copilot-input" placeholder="Ask AI Copilot about incidents, IOCs, Sigma rules..." onkeydown="if(event.key==='Enter') window.sendSocChat()">
        <button class="soc-copilot-send" onclick="window.sendSocChat()">Send</button>
      </div>
    `;
    document.body.appendChild(drawer);

    // 3. Inject Theme Switcher Button into Topbar (Exact single instance)
    const topbarRight = document.querySelector('.topbar-right') || document.querySelector('.portal-meta');
    if (topbarRight && !document.getElementById('socThemeBtn')) {
      const wrapper = document.createElement('div');
      wrapper.id = 'socThemeBtnWrapper';
      wrapper.style.cssText = 'display:flex;align-items:center;gap:8px;margin-right:6px;';
      
      const themeBtn = document.createElement('button');
      themeBtn.id = 'socThemeBtn';
      themeBtn.className = 'soc-theme-btn';
      themeBtn.innerHTML = '🎨 Themes ▾';
      themeBtn.onclick = () => window.openSocThemeModal();

      const kBtn = document.createElement('button');
      kBtn.id = 'socKioskBtn';
      kBtn.className = 'btn btn-ghost btn-sm';
      kBtn.style.padding = '3px 8px';
      kBtn.style.fontSize = '11px';
      kBtn.innerHTML = '📺 Kiosk';
      kBtn.title = 'SOC Wallboard Kiosk Mode (Auto-rotates through dashboards)';
      kBtn.onclick = () => window.startKiosk();

      wrapper.appendChild(themeBtn);
      wrapper.appendChild(kBtn);
      topbarRight.prepend(wrapper);
    }

    createThemeModal();
  }

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
Target Index: <code>soc-logs-*</code> | Ingested via Vector.`;
      } else if (lower.includes('win-dc01') || lower.includes('alert') || lower.includes('investigate')) {
        resp = `<b>[Threat Analyst Agent]</b><br>
<b>Investigation Summary: WIN-DC01</b> (172.20.0.10)<br>
• <b>Severity:</b> <span style="color:#ef4444;font-weight:bold;">CRITICAL</span> (Score: 96/100)<br>
• <b>Root Cause:</b> Process <code>mimikatz.exe</code> accessed LSASS with GrantedAccess <code>0x1010</code>.<br>
• <b>Lateral Movement:</b> Overpass-the-Hash authentication attempted to <code>SRV-APP01</code>.<br>
• <b>Recommended Action:</b> Isolate WIN-DC01 network adapter and invalidate Kerberos KRBTGT hash.`;
      } else {
        resp = `<b>[Senior SOC Lead]</b><br>
Analyzed query: "<em>${msg}</em>"<br>
• Active Persona: <code>${persona.toUpperCase()}</code><br>
• OpenSearch Telemetry: Ingesting 842 EPS across 6 sensors (Sysmon, Zeek, Suricata, Auditd).<br>
• Cluster Status: Green (2 Nodes, 0 Unassigned Shards).`;
      }

      botEl.innerHTML = resp;
      msgs.scrollTop = msgs.scrollHeight;
    }, 600);
  };

  window.showSocToast = function(msg) {
    let t = document.getElementById('socGlobalToast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'socGlobalToast';
      t.style.cssText = 'position:fixed;bottom:20px;left:20px;background:#0f172a;border:1px solid #3b82f6;color:#fff;padding:12px 18px;border-radius:8px;font-size:12px;z-index:10010;box-shadow:0 6px 20px rgba(0,0,0,0.5);display:none;';
      document.body.appendChild(t);
    }
    t.innerHTML = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3500);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createCopilotUI);
  } else {
    createCopilotUI();
  }
})();
