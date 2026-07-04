#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Create the raptorscope-* data view in Kibana (and import saved objects if any),
# so the ingested ECS docs are explorable in Discover / Dashboards.
#
#   ./kibana/provision.sh                       # defaults to http://localhost:5601
#   KIBANA=http://host:5601 ./kibana/provision.sh
set -euo pipefail

KIBANA="${KIBANA:-http://localhost:5601}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Waiting for Kibana at ${KIBANA} …"
for _ in $(seq 1 60); do
  if curl -sf "${KIBANA}/api/status" >/dev/null 2>&1; then break; fi
  sleep 3
done

# Primary path: import the data view + saved search from NDJSON.
if [ -f "${DIR}/saved_objects.ndjson" ] && \
   curl -sf -X POST "${KIBANA}/api/saved_objects/_import?overwrite=true" \
     -H 'kbn-xsrf: true' --form file=@"${DIR}/saved_objects.ndjson" >/dev/null; then
  echo "Imported the Raptorscope data view + saved search."
else
  # Fallback: create just the data view via the Data Views API.
  echo "Import unavailable; creating the raptorscope-* data view directly …"
  curl -sf -X POST "${KIBANA}/api/data_views/data_view" \
    -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
    -d '{"data_view":{"name":"Raptorscope","title":"raptorscope-*","timeFieldName":"@timestamp"}}' \
    >/dev/null && echo "  data view ready" \
    || echo "  data view may already exist (ok)"
fi

echo "Done. Open ${KIBANA}/app/discover and pick the Raptorscope data view."
