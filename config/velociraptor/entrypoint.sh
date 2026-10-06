#!/bin/sh
set -e

CONFIG_FILE="/etc/velociraptor/server.config.yaml"

if [ ! -f "$CONFIG_FILE" ] || [ $(wc -l < "$CONFIG_FILE") -lt 20 ]; then
    echo "[*] Generating Velociraptor server configuration..."
    velociraptor config generate > "$CONFIG_FILE"
    
    # Configure GUI port and binding
    sed -i 's/bind_address: 127.0.0.1/bind_address: 0.0.0.0/g' "$CONFIG_FILE"
    sed -i 's/bind_port: 8889/bind_port: 8889/g' "$CONFIG_FILE"
fi

echo "[*] Creating/Updating admin user (admin / VelociraptorAdmin!2026#Secure)..."
velociraptor --config "$CONFIG_FILE" user add admin "VelociraptorAdmin!2026#Secure" --role administrator || true

echo "[*] Starting Velociraptor GUI Server on port 8889..."
exec velociraptor --config "$CONFIG_FILE" frontend -v
