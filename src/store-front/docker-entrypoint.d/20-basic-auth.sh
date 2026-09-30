#!/bin/sh
# Generates the HTTP Basic authentication snippet included by nginx.conf.
#
# Runs automatically at container start (the nginx image executes every
# /docker-entrypoint.d/*.sh script before starting nginx), so credentials are
# supplied as environment variables instead of being baked into the image:
#
#   AUTH_USERNAME   username accepted by the portal (required)
#   AUTH_PASSWORD   password accepted by the portal (required)
#   AUTH_REALM      realm shown by the browser      (optional)
#   AUTH_ENABLED    set to "false" to disable auth  (local development only)

set -e

AUTH_CONF=/etc/nginx/auth.conf
AUTH_USER_FILE=/etc/nginx/.htpasswd

if [ "${AUTH_ENABLED:-true}" = "false" ]; then
  echo "WARNING: AUTH_ENABLED is false - serving the portal APIs without authentication." >&2
  echo "auth_basic off;" > "$AUTH_CONF"
  exit 0
fi

if [ -z "$AUTH_USERNAME" ] || [ -z "$AUTH_PASSWORD" ]; then
  echo "ERROR: AUTH_USERNAME and AUTH_PASSWORD must be set to enable authentication." >&2
  echo "       Set AUTH_ENABLED=false to run without authentication (local development only)." >&2
  exit 1
fi

umask 077
printf '%s:{PLAIN}%s\n' "$AUTH_USERNAME" "$AUTH_PASSWORD" > "$AUTH_USER_FILE"

cat > "$AUTH_CONF" <<EOF
auth_basic "${AUTH_REALM:-Contoso Pet Store}";
auth_basic_user_file ${AUTH_USER_FILE};
EOF
