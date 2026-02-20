#!/bin/bash
# Simulates typing the command, then executes it.
# Used by asciinema to create a natural-looking terminal recording.
CMD="python scripts/demo_scan.py examples/vulnerable-lending/programs/vulnerable-lending/src/lib.rs"
echo -n "$ "
for (( i=0; i<${#CMD}; i++ )); do
    echo -n "${CMD:$i:1}"
    sleep 0.03
done
echo ""
$CMD
