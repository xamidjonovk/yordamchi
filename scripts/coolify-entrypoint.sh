#!/bin/sh
set -eu
if [ "${HPA_AUTOSTART:-false}" != true ]; then
  echo 'HPA is in standby. Configure or import the instance before enabling HPA_AUTOSTART.'
  trap 'exit 0' TERM INT
  while :; do sleep 3600 & wait "$!" || :; done
fi
if [ ! -s "$HPA_HOME/config.json" ] || [ ! -s "$HPA_HOME/data/telegram.session" ]; then
  echo 'Instance is not configured. Keep HPA_AUTOSTART=false and perform setup or import first.' >&2
  exit 1
fi
exec /app/.venv/bin/hpa serve
