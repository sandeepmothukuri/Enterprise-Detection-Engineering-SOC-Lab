# Threat Hunting Methodology & VQL Investigation Playbooks

Author: Sandeep Mothukuri ([@sandeepmothukuri](https://github.com/sandeepmothukuri))  
Platform: Enterprise Detection Engineering & SOC Operations Lab v2

---

## 1. Proactive Threat Hunting Framework

Threat hunting in the lab operates on an assumption of breach, leveraging hypothesis-driven investigations across endpoint artifacts (Velociraptor VQL), network flows (Zeek NSM), and enriched SIEM logs (OpenSearch).

---

## 2. Core Threat Hunting Queries & Playbooks

### Hunt 1: Suspicious Parent-Child Process Spawning
**Hypothesis**: Adversaries launch command interpreters (`cmd.exe`, `powershell.exe`) from unexpected parents (`winword.exe`, `excel.exe`, `w3wp.exe`, `sqlserver.exe`).

**OpenSearch KQL Query**:
```kql
sensor: "sysmon" and EventID: 1 and ParentImage: (*winword.exe or *excel.exe or *w3wp.exe) and Image: (*powershell.exe or *cmd.exe or *mshta.exe or *cscript.exe)
```

**Velociraptor VQL**:
```sql
SELECT Timestamp, Name, CommandLine, Exe, Parent.CommandLine AS ParentCmd
FROM Windows.System.Pstree
WHERE Exe =~ "(powershell|cmd|mshta|cscript)\.exe$"
  AND ParentCmd =~ "(winword|excel|w3wp|sqlservr)\.exe$"
```

---

### Hunt 2: DNS High Entropy & Long Subdomain Beaconing
**Hypothesis**: Data exfiltration or C2 beaconing utilizes encoded subdomains querying custom nameservers.

**OpenSearch KQL Query**:
```kql
sensor: "zeek" and service: "dns" and not dns.rcode: "NXDOMAIN" and dns.query: /[a-zA-Z0-9]{32,}\..*/
```

---

### Hunt 3: LSASS Memory Handle Outliers
**Hypothesis**: Non-standard tools request `PROCESS_QUERY_INFORMATION` (`0x0400`) and `PROCESS_VM_READ` (`0x0010`) access masks to LSASS without creating a full dump file on disk.

**OpenSearch KQL Query**:
```kql
sensor: "sysmon" and EventID: 10 and TargetImage: "*\\lsass.exe" and not SourceImage: ("*\\csrss.exe" or "*\\MsMpEng.exe" or "*\\svchost.exe")
```
