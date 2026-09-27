# Detection Engineering Lifecycle & Sigma Rule Pipeline

Author: Sandeep Mothukuri ([@sandeepmothukuri](https://github.com/sandeepmothukuri))  
Platform: Enterprise Detection Engineering & SOC Operations Lab v2

---

## 1. Detection-as-Code Lifecycle

The platform operationalizes a robust Detection-as-Code pipeline:

```
[Threat Modeling] ➔ [Sigma Rule Development] ➔ [Automated Transpilation] ➔ [ElastAlert2 Deployment] ➔ [Adversary Emulation Testing] ➔ [SOC Dashboard Visibility]
```

---

## 2. Active Sigma Rule Catalog (13 Core Rules)

| Rule ID | MITRE ID | Rule Title | Tactic | Severity | Target Sensor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SIG-WIN-001` | `T1003.001` | LSASS Memory Access & Dumping | Credential Access | Critical | Sysmon Event 10 |
| `SIG-WIN-002` | `T1110` | Account Brute Force & Password Spray | Credential Access | High | Windows Security 4625 |
| `SIG-NET-001` | `T1557` | LLMNR / NBT-NS Poisoning (Responder) | Credential Access | High | Zeek / Suricata |
| `SIG-WIN-003` | `T1562.001`| Windows Defender Real-Time Protection Disabled | Defense Evasion | High | Sysmon Event 1 / Powershell |
| `SIG-NET-002` | `T1046` | Port Scanning & Reconnaissance | Discovery | Medium | Zeek conn.log / Suricata |
| `SIG-WIN-004` | `T1047` | WMI Process Execution (wmic.exe) | Execution | High | Sysmon Event 1 |
| `SIG-WIN-005` | `T1059.001`| Base64 Encoded PowerShell Command Execution | Execution | Critical | Sysmon Event 1 / Script Block |
| `SIG-NET-003` | `T1041` | Exfiltration Over C2 Channel | Exfiltration | High | Zeek HTTP / Conn |
| `SIG-WIN-006` | `T1021.002`| Suspicious SMB Administrative Share Lateral Movement| Lateral Movement | High | Zeek SMB / Sysmon Event 3 |
| `SIG-WIN-007` | `T1550.002`| Pass-the-Hash / Overpass-the-Hash | Lateral Movement | Critical | Windows Security 4624 (Logon Type 9) |
| `SIG-NET-004` | `T1071.004`| DNS Tunneling & High-Entropy Query C2 | Command & Control | High | Zeek dns.log / Suricata |
| `SIG-WIN-008` | `T1053.005`| Scheduled Task Creation via schtasks.exe | Persistence | Medium | Sysmon Event 1 / Security 4698 |
| `SIG-WIN-009` | `T1547.001`| Registry Run Key Persistence Modification | Persistence | Medium | Sysmon Event 13 (Registry) |

---

## 3. Automated Validation & CI/CD Pipeline

The detection rules are continuously transpiled and validated using `tools/transpile-sigma-to-opensearch.py` and tested using the purple team test harness `tools/test-e2e-harness.py`.

### Validation Output
- **Total Rules Analyzed**: 13
- **Transpilation Success Rate**: 100% (13/13)
- **ElastAlert2 Compatibility**: Validated against OpenSearch 2.13.0 query DSL
- **End-to-End Adversary Test Pass Rate**: 100%
