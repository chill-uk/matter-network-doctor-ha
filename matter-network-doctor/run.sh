#!/usr/bin/env sh
set -eu

VERBOSE=""
if [ -f /data/options.json ] && grep -q '"verbose"[[:space:]]*:[[:space:]]*true' /data/options.json; then
  VERBOSE="--verbose"
fi

exec matter-network-doctor scan ${VERBOSE}

