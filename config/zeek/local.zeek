# ================================================================
#  Zeek Local Configuration — SOC Lab
#  Network Security Monitoring (Security Onion core engine)
# ================================================================
@load base/frameworks/intel
@load base/frameworks/notice
@load base/frameworks/logging
@load base/protocols/conn
@load base/protocols/dns
@load base/protocols/http
@load base/protocols/ftp
@load base/protocols/smtp
@load base/protocols/ssh
@load base/protocols/ssl
@load base/protocols/smb
@load base/protocols/krb
@load misc/capture-loss
@load misc/stats
@load policy/frameworks/analyzer/detect-protocols

# JSON output for Vector pipeline

# MITRE ATT&CK enrichment scripts
@load policy/integration/collective-intel

# Custom SOC detection scripts
@load ./soc-detections

module SOC;

# Log all connections to OpenSearch via Vector
redef Log::default_rotation_interval = 1hrs;

# Track C2 beacon intervals (MITRE T1071)
redef HTTP::max_pending_requests = 100;

event zeek_init() {
    print "SOC Lab Zeek NSM started";
}
