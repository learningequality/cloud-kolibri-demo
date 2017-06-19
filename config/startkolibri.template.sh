#!/bin/bash
# Startup script for running kolibri all-in-one `pex` file

set -eo pipefail

export KOLIBRI_LANG={{KOLIBRI_LANG}}
export KOLIBRI_HOME={{KOLIBRI_HOME}}
export KOLIBRI_PORT={{KOLIBRI_PORT}}
export KOLIBRI_PEX_FILE={{KOLIBRI_PEX_FILE}}

python $KOLIBRI_PEX_FILE language setdefault $KOLIBRI_LANG
exec python $KOLIBRI_PEX_FILE start --port=$KOLIBRI_PORT   # TODO: test exec vs no-exec