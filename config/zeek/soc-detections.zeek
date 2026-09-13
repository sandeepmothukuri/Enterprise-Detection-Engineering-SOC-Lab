# ================================================================
# Custom Zeek detections — SOC Lab
# MITRE ATT&CK: T1046 Network Service Scanning
#
# Detection is based on completed connections so the same logic works
# with live traffic and replayed PCAPs. Vertical and horizontal scans
# are tracked independently within a bounded observation window.
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

global vertical_first_seen: table[addr, addr] of time &create_expire=1min;
global vertical_ports: table[addr, addr] of set[port] &create_expire=1min;
global horizontal_first_seen: table[addr] of time &create_expire=1min;
global horizontal_destinations: table[addr] of set[addr] &create_expire=1min;

event connection_state_remove(c: connection) {
    if ( c$id$orig_h == 0.0.0.0 || c$id$resp_h == 0.0.0.0 )
        return;

    local now_ts = network_time();
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;

    # Vertical scan: one originator -> one destination -> many ports.
    if ( [orig, resp] !in vertical_first_seen || now_ts - vertical_first_seen[orig, resp] > scan_window ) {
        vertical_first_seen[orig, resp] = now_ts;
        vertical_ports[orig, resp] = set();
    }

    add vertical_ports[orig, resp][c$id$resp_p];
    if ( |vertical_ports[orig, resp]| >= port_scan_threshold ) {
        NOTICE([$note=Port_Scan,
                $msg=fmt("T1046 network port scan detected from %s: %d unique destination ports contacted", orig, |vertical_ports[orig, resp]|),
                $src=orig,
                $dst=resp,
                $identifier=fmt("vertical-%s-%s", orig, resp)]);
        delete vertical_first_seen[orig, resp];
        delete vertical_ports[orig, resp];
    }

    # Horizontal scan: one originator -> many destination hosts.
    if ( orig !in horizontal_first_seen || now_ts - horizontal_first_seen[orig] > scan_window ) {
        horizontal_first_seen[orig] = now_ts;
        horizontal_destinations[orig] = set();
    }

    add horizontal_destinations[orig][resp];
    if ( |horizontal_destinations[orig]| >= address_scan_threshold ) {
        NOTICE([$note=Address_Scan,
                $msg=fmt("T1046 network host scan detected from %s: %d unique destination hosts contacted", orig, |horizontal_destinations[orig]|),
                $src=orig,
                $identifier=fmt("horizontal-%s", orig)]);
        delete horizontal_first_seen[orig];
        delete horizontal_destinations[orig];
    }
}
