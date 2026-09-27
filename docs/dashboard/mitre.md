# MITRE ATT&CK Framework Coverage & Adversary Emulation

Author: Sandeep Mothukuri ([@sandeepmothukuri](https://github.com/sandeepmothukuri))  
Platform: Enterprise Detection Engineering & SOC Operations Lab v2

---

## 1. Enterprise MITRE ATT&CK Matrix Alignment

The lab is mapped directly to the **MITRE ATT&CK Enterprise Matrix (v14)**. Detection rules and adversary emulation scripts cover 8 core tactic categories across the attack lifecycle:

```
[Reconnaissance/Discovery] ➔ [Initial Access/Execution] ➔ [Persistence/Privilege Escalation] ➔ [Defense Evasion] ➔ [Credential Access] ➔ [Lateral Movement] ➔ [Command & Control] ➔ [Exfiltration]
```

---

## 2. Tactic & Technique Coverage Breakdown

| MITRE Tactic | Technique ID | Technique Name | Detection Rule | Validation Method |
| :--- | :--- | :--- | :--- | :--- |
| **Discovery** | `T1046` | Network Service Scanning | `SIG-NET-002` | Nmap SYN scan simulation against subnet |
| **Execution** | `T1047` | Windows Management Instrumentation | `SIG-WIN-004` | Caldera `wmic process call create` |
| **Execution** | `T1059.001` | PowerShell: Encoded Commands | `SIG-WIN-005` | Caldera PowerShell Base64 payload |
| **Persistence** | `T1053.005` | Scheduled Task/Job | `SIG-WIN-008` | Atomic Red Team schtasks trigger |
| **Persistence** | `T1547.001` | Boot/Logon Autostart Execution | `SIG-WIN-009` | HKCU\Software\Microsoft\Windows\CurrentVersion\Run |
| **Defense Evasion** | `T1562.001` | Impair Defenses: Disable Defender | `SIG-WIN-003` | `Set-MpPreference -DisableRealtimeMonitoring` |
| **Credential Access**| `T1003.001` | OS Credential Dumping: LSASS Memory | `SIG-WIN-001` | Mimikatz `sekurlsa::logonpasswords` / ProcDump |
| **Credential Access**| `T1110` | Brute Force: Password Spray | `SIG-WIN-002` | Kerbrute / Hydra SMB brute force |
| **Credential Access**| `T1557` | Adversary-in-the-Middle: LLMNR/NBT-NS | `SIG-NET-001` | Kali Responder poisoned broadcast queries |
| **Lateral Movement** | `T1021.002` | Remote Services: SMB/Windows Admin Shares | `SIG-WIN-006` | PsExec / NetExec C$ access |
| **Lateral Movement** | `T1550.002` | Use Alternate Authentication Material: Pass the Hash | `SIG-WIN-007` | Impacket `wmiexec.py` with NTLM hash |
| **Command & Control**| `T1071.004` | Application Layer Protocol: DNS Tunneling | `SIG-NET-004` | Iodine / dnscat2 high entropy queries |
| **Exfiltration** | `T1041` | Exfiltration Over C2 Channel | `SIG-NET-003` | HTTP POST data exfiltration stream |
