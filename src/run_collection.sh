#!/bin/bash
# Overnight runner for collect_data.py.
#
#   src/run_collection.sh            # run for up to 8 hours (default)
#   src/run_collection.sh 4          # up to 4 hours
#   src/run_collection.sh 8 --case lahaina   # extra args go to collect_data.py
#
# Detaches immediately (closing the terminal is fine) and keeps the Mac awake
# with caffeinate for as long as it runs -- the lid must stay open; closing it
# sleeps the Mac no matter what. Each pass runs collect_data.py; if any source
# failed (e.g. PullPush 429s), it waits PASS_GAP_MIN minutes and tries again,
# until a pass finishes clean or the time budget runs out. Rows already saved
# are kept and deduplicated, so repeated passes only fill gaps.
#
# Everything is logged with timestamps to logs/collect_<start time>.txt.
# Follow it live:   tail -f logs/collect_*.txt
# Is it running?    pgrep -fl run_collection.sh
# Stop it:          pkill -f run_collection.sh; pkill -f collect_data.py

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SELF="$PROJECT_DIR/src/run_collection.sh"
PYTHON="$PROJECT_DIR/.venv/bin/python"
PASS_GAP_MIN=20

HOURS="${1:-8}"
[ $# -gt 0 ] && shift

# --- launcher: re-run this script detached, under caffeinate, then return ---
if [ -z "$COLLECT_DETACHED" ]; then
    mkdir -p "$PROJECT_DIR/logs"
    LOG="$PROJECT_DIR/logs/collect_$(date '+%Y-%m-%d_%H%M%S').txt"
    # -i: no idle sleep, -s: no system sleep while on AC power, -m: keep disk awake
    COLLECT_DETACHED=1 LOG="$LOG" nohup caffeinate -i -s -m "$SELF" "$HOURS" "$@" \
        >/dev/null 2>&1 &
    echo "Started in the background (pid $!), running for up to $HOURS hours."
    echo "Log: $LOG"
    echo "Follow it with:  tail -f \"$LOG\""
    echo "Keep the Mac plugged in with the lid open; you can close this terminal."
    exit 0
fi

# --- detached worker ---
cd "$PROJECT_DIR" || exit 1
exec >>"$LOG" 2>&1

stamp() { while IFS= read -r line; do printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"; done; }
log() { echo "$*" | stamp; }

trap 'log "=== runner stopped by signal ==="; exit 130' INT TERM HUP

deadline=$(( $(date +%s) + HOURS * 3600 ))
log "=== run_collection.sh started: up to $HOURS h, pass gap $PASS_GAP_MIN min, args: $* ==="
log "git: $(git log --oneline -1 2>/dev/null) | uncommitted: $(git status --short src | tr '\n' ' ')"
log "python: $("$PYTHON" --version 2>&1) | power: $(pmset -g ps | head -1)"

pass=0
result="ran out of time"
while :; do
    pass=$((pass + 1))
    start=$(date +%s)
    log "=== pass $pass starting | power: $(pmset -g ps | head -1 | sed "s/Now drawing from //") ==="
    "$PYTHON" -u src/collect_data.py "$@" 2>&1 | stamp
    code=${PIPESTATUS[0]}
    log "=== pass $pass finished in $(( ($(date +%s) - start) / 60 )) min, exit code $code ==="

    if [ "$code" -eq 0 ]; then
        result="all sources complete"
        break
    fi
    if [ $(( $(date +%s) + PASS_GAP_MIN * 60 )) -ge "$deadline" ]; then
        break
    fi
    log "some sources failed -- waiting $PASS_GAP_MIN min before pass $((pass + 1))"
    # backgrounded + wait, so a pkill stops the runner immediately instead of
    # after the sleep finishes (bash defers traps during a foreground command)
    sleep $(( PASS_GAP_MIN * 60 )) &
    wait $!
done

log "=== done after $pass pass(es): $result ==="
log "row counts:"
"$PYTHON" - <<'EOF' 2>&1 | stamp
import glob, os, pandas as pd
for p in sorted(glob.glob("data/*.csv")):
    if p.endswith("_burst.csv"):
        continue
    try:
        n = len(pd.read_csv(p))
    except Exception:
        n = 0
    print(f"  {os.path.basename(p):45s} {n:>7}")
EOF
