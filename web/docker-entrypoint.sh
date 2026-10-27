#!/bin/sh
set -eu

conf=/etc/nginx/conf.d/default.conf

render() {
  if [ -n "${API_AUDIENCE:-}" ]; then
    API_TOKEN=$(wget -qO- --header="Metadata-Flavor: Google" \
      "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=${API_AUDIENCE}")
  else
    API_TOKEN=""
  fi

  rest=${API_UPSTREAM#*://}
  scheme=${API_UPSTREAM%%://*}
  hostport=${rest%%/*}
  nameserver=$(awk '/^nameserver/ { print $2; exit }' /etc/resolv.conf)
  if [ -z "$nameserver" ]; then
    nameserver=127.0.0.11
  fi

  cat > "$conf" <<EOF
server {
    listen ${PORT};
    root /usr/share/nginx/html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~ ^/(chat|health|questions|results|run|evaluations|metrics) {
        resolver ${nameserver} valid=10s ipv6=off;
        set \$api_hostport ${hostport};
        proxy_pass ${scheme}://\$api_hostport;
        proxy_http_version 1.1;
        proxy_ssl_server_name on;
        proxy_set_header Host \$api_hostport;
        proxy_set_header Authorization "Bearer ${API_TOKEN}";
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }
}
EOF
}

render
nginx -g "daemon off;" &
nginx_pid=$!
trap 'kill "$nginx_pid" 2>/dev/null || true' TERM INT

if [ -n "${API_AUDIENCE:-}" ]; then
  while kill -0 "$nginx_pid" 2>/dev/null; do
    sleep 2400
    render
    nginx -s reload || true
  done
fi

wait "$nginx_pid"
