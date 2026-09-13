#!/bin/sh
set -eu

INTERFACE="${ZEEK_INTERFACE:-auto}"
SOC_NETWORK="${SOC_NETWORK:-172.20.0.0/16}"

if [ "$INTERFACE" = "auto" ]; then
    INTERFACE="$(ip -o route show "$SOC_NETWORK" 2>/dev/null | awk 'NR==1 {for (i=1; i<=NF; i++) if ($i == "dev") {print $(i+1); exit}}')"
fi

if [ -z "${INTERFACE}" ] || [ ! -d "/sys/class/net/${INTERFACE}" ]; then
    echo "ERROR: Zeek capture interface '${INTERFACE:-<empty>}' is not available" >&2
    echo "Configured network: ${SOC_NETWORK}" >&2
    echo "Available interfaces:" >&2
    ls /sys/class/net >&2
    echo "Routes:" >&2
    ip -o route >&2 || true
    exit 1
fi

echo "SOC Lab Zeek capture interface: ${INTERFACE}"

exec zeek \
    -i "$INTERFACE" \
    -C \
    local \
    /usr/local/zeek/share/zeek/policy/tuning/json-logs.zeek
