# ================================================================
# Zeek Local Configuration — Enterprise Detection Engineering SOC Lab
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
@load policy/integration/collective-intel
@load ./soc-detections

module SOC;

# Keep the sensor output stable for downstream Vector ingestion.
redef Log::default_rotation_interval = 1hrs;
redef HTTP::max_pending_requests = 100;

event zeek_init() {
    print "SOC Lab Zeek NSM started";
}
