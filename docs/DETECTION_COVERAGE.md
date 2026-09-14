# Detection Coverage Matrix

This matrix reconciles the 15 detection scenarios documented in the project with the current detection-as-code and training telemetry paths. It intentionally distinguishes **training telemetry** from native endpoint/network evidence.

| Detection | ATT&CK | Sigma | ElastAlert2 | Training simulation | Expected telemetry |
|---|---|---|---|---|---|
| Brute Force / Password Spray | T1110.001 | `detection-rules/sigma/credential-access/T1110_brute_force.yml` | `T1110.001_brute_force_training.yml` | `simulate-attack.sh bruteforce`, `apt29` | OpenSearch training event |
| LSASS Memory Dump | T1003.001 | `T1003.001_lsass_dump.yml` | `T1003.001_lsass_training.yml` | `apt29` | Sysmon/Windows-style event |
| PowerShell Encoded Command | T1059.001 | `T1059.001_encoded_powershell.yml` | `T1059.001_powershell_training.yml` | `apt29` | Sysmon/Windows-style event |
| Lateral Movement via SMB | T1021.002 | `T1021.002_smb_lateral.yml` | `T1021.002_smb_training.yml` | `apt29` | Zeek/Windows-style event |
| LLMNR/NBT-NS Poisoning | T1557.001 | `T1557_llmnr_poison.yml` | `T1557.001_llmnr_training.yml` | `apt29` | Zeek-style event |
| Scheduled Task Creation | T1053.005 | `T1053.005_scheduled_task.yml` | `T1053.005_scheduled_task_training.yml` | `apt29` | Sysmon/Windows-style event |
| Registry Run Key Persistence | T1547.001 | `T1547.001_registry_run.yml` | `T1547.001_registry_run_training.yml` | `apt29` | Sysmon/Windows-style event |
| DNS Tunneling C2 | T1071.004 | `T1071.004_dns_tunneling.yml` | `T1071.004_dns_tunneling_training.yml` | `apt29` | Zeek-style event |
| Pass-the-Hash | T1550.002 | `T1550.002_pass_the_hash.yml` | `T1550.002_pass_the_hash_training.yml` | `apt29` | Windows-style event |
| Network Port Scan | T1046 | `T1046_network_scan.yml` | `T1046_network_scan_training.yml` | `apt29` | Suricata/Zeek-style event |
| Data Exfiltration over C2 | T1041 | `T1041_c2_exfil.yml` | `T1041_exfil_training.yml` | `apt29` | Zeek-style event |
| Defender Disabled | T1562.001 | `T1562.001_defender_disable.yml` | `T1562.001_defender_training.yml` | `apt29` | Sysmon/Windows-style event |
| Spearphishing Attachment | T1566.001 | `T1566.001_spearphishing_attachment.yml` | `T1566.001_spearphishing_training.yml` | `apt29` | Email/Windows-style training event |
| Bulk File Collection | T1039 | `T1039_bulk_file_collection.yml` | `T1039_bulk_collection_training.yml` | `insider` | File-audit training event |
| After-Hours Account Login | T1078 | `T1078_after_hours_login.yml` | `T1078_after_hours_training.yml` | `insider` | Windows-style training event |

## Validation contract

- Sigma files are parsed with `yaml.safe_load_all` and checked for UUIDs, metadata, ATT&CK tags and either a standard `detection` block or Sigma correlation block.
- ElastAlert2 rules are structurally checked for rule type, index, filter and alert fields.
- Training simulation writes events to `soc-logs-*` using the generated OpenSearch admin certificate and CA.
- An ElastAlert `debug` alert is intentionally used by the added training-coverage rules so the detection engine can be regression-tested without fabricating an external notification or SOAR action.
- Native Caldera, Zeek, Suricata and endpoint evidence remain distinct from synthetic training telemetry.
