FROM alpine:3.20

RUN apk add --no-cache ca-certificates curl gzip jq

# Download Velociraptor Musl Release Binary
RUN curl -sL https://github.com/Velocidex/velociraptor/releases/download/v0.77.3/velociraptor-v0.77.3-linux-amd64-musl.gz -o /bin/velociraptor.gz && \
    gzip -d /bin/velociraptor.gz && \
    chmod +x /bin/velociraptor

WORKDIR /velociraptor

# Entrypoint script to generate config and start frontend
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8889 8001 8000

ENTRYPOINT ["/entrypoint.sh"]
