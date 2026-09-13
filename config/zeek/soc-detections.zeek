module Scan;

export {
    redef enum Notice::Type += {
        Port_Scan,
        Address_Scan,
    };

    const port_scan_threshold: count = 20 &redef;
    const address_scan_threshold: count = 20 &redef;
    const scan_window: interval = 60secs &redef;
}

type VerticalState: record {
    first_seen: time;
    ports: set[port];
    alerted: bool &default=F;
};

type HorizontalState: record {
    first_seen: time;
    hosts: set[addr];
    alerted: bool &default=F;
};

global vertical_state: table[addr, addr] of VerticalState
    &write_expire=scan_window;

global horizontal_state: table[addr] of HorizontalState
    &write_expire=scan_window;

event new_connection(c: connection)
    {
    if ( c$id$orig_h == 0.0.0.0 ||
         c$id$resp_h == 0.0.0.0 )
        return;

    local orig_h = c$id$orig_h;
    local resp_h = c$id$resp_h;
    local resp_p = c$id$resp_p;
    local now = network_time();

    # Vertical scan: one source contacting many ports on one destination.
    if ( [orig_h, resp_h] !in vertical_state )
        vertical_state[orig_h, resp_h] = VerticalState(
            $first_seen=now,
            $ports=set()
        );

    local vstate = vertical_state[orig_h, resp_h];

    if ( now - vstate$first_seen > scan_window )
        {
        vstate = VerticalState(
            $first_seen=now,
            $ports=set()
        );
        }

    add vstate$ports[resp_p];

    if ( !vstate$alerted &&
         |vstate$ports| >= port_scan_threshold )
        {
        NOTICE([$note=Scan::Port_Scan,
                $msg=fmt("T1046 network port scan detected from %s to %s: %d unique destination ports contacted",
                         orig_h, resp_h, |vstate$ports|),
                $src=orig_h,
                $dst=resp_h,
                $identifier=fmt("%s:%s:port-scan", orig_h, resp_h)]);

        vstate$alerted = T;
        }

    vertical_state[orig_h, resp_h] = vstate;

    # Horizontal scan: one source contacting many destination hosts.
    if ( orig_h !in horizontal_state )
        horizontal_state[orig_h] = HorizontalState(
            $first_seen=now,
            $hosts=set()
        );

    local hstate = horizontal_state[orig_h];

    if ( now - hstate$first_seen > scan_window )
        {
        hstate = HorizontalState(
            $first_seen=now,
            $hosts=set()
        );
        }

    add hstate$hosts[resp_h];

    if ( !hstate$alerted &&
         |hstate$hosts| >= address_scan_threshold )
        {
        NOTICE([$note=Scan::Address_Scan,
                $msg=fmt("T1046 network address scan detected from %s: %d unique destination hosts contacted",
                         orig_h, |hstate$hosts|),
                $src=orig_h,
                $identifier=fmt("%s:address-scan", orig_h)]);

        hstate$alerted = T;
        }

    horizontal_state[orig_h] = hstate;
    }
