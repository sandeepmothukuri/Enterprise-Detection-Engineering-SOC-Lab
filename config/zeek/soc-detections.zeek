# ================================================================
# Custom Zeek detections — SOC Lab
# MITRE ATT&CK: T1046 Network Service Scanning
#
# The detector is intentionally based on completed connections so it
# works with both live traffic and replayed PCAPs. It separates:
#   - vertical scans: one source -> one destination, many ports
#   - horizontal scans: one source -> many destinations, one service
# ================================================================

@load base/frameworks/notice
@load base/protocols/conn

module Scan;

export {
    redef enum Notice::Type += {
        Port_Scan,
        Address_Scan
    };

    const port_scan_threshold: count = 20 &redef;
    const address_scan_threshold: count = 20 &redef;
    const scan_window: interval = 60secs &redef;
}

type VerticalState: record {
    first_seen: time;
    ports: set[port];
};

type HorizontalState: record {
    first_seen: time;
    destinations: set[addr];
};

global vertical_state: table[addr, addr] of VerticalState &create_expire=1min;
global horizontal_state: table[addr] of HorizontalState &create_expire=1min;

event connection_state_remove(c: connection) {
    if ( c$id$orig_h == 0.0.0.0 || c$id$resp_h == 0.0.0.0 )
        return;

    local now_ts = network_time();

    # Vertical scan: one originator contacting many destination ports on
    # the same host inside a bounded observation window.
    local vkey = [c$id$orig_h, c$id$resp_h];
    if ( vkey !in vertical_state || now_ts - vertical_state[vkey]$first_seen > scan_window ) {
        vertical_state[vkey] = [$first_seen=now_ts, $ports=set()];
    }

    add vertical_state[vkey]$ports[c$id$resp_p];
    if ( |vertical_state[vkey]$ports| >= port_scan_threshold ) {
        NOTICE([$note=Port_Scan,
                $msg=fmt("T1046 network port scan detected from %s: %d unique destination ports contacted", c$id$orig_h, |vertical_state[vkey]$ports|),
                $src=c$id$orig_h,
                $dst=c$id$resp_h,
                $identifier=fmt("vertical-%s-%s", c$id$orig_h, c$id$resp_h)]);
        delete vertical_state[vkey];
    }

    # Horizontal scan: one originator contacting many destination hosts.
    if ( c$id$orig_h !in horizontal_state || now_ts - horizontal_state[c$id$orig_h]$first_seen > scan_window ) {
        horizontal_state[c$id$orig_h] = [$first_seen=now_ts, $destinations=set()];
    }

    add horizontal_state[c$id$orig_h]$destinations[c$id$resp_h];
    if ( |horizontal_state[c$id$orig_h]$destinations| >= address_scan_threshold ) {
        NOTICE([$note=Address_Scan,
                $msg=fmt("T1046 network host scan detected from %s: %d unique destination hosts contacted", c$id$orig_h, |horizontal_state[c$id$orig_h]$destinations|),
                $src=c$id$orig_h,
                $identifier=fmt("horizontal-%s", c$id$orig_h)]);
        delete horizontal_state[c$id$orig_h];
    }
}
