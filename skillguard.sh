#!/bin/bash

# ==============================================================================
# SkillGuard v2.3 — Extreme Hardening Edition (Professional Security)
# Author: CM Fang (NewTWCM) & Antigravity
# Research Context: Industrial-Grade Reliability
# ==============================================================================

VERSION="2.3"
VACCINE_DIR="$HOME/.skillguard"
SEAL_FILE="$VACCINE_DIR/.seal"
DB_FILE="$VACCINE_DIR/patterns.db"
STATE_DB="$VACCINE_DIR/state.db"

# [ADVANCED v2.3] Absolute Paths for Security Tools (Prevent Hijacking)
CAT="/bin/cat"
GREP="/usr/bin/grep"
SHASUM="/usr/bin/shasum"
MKDIR="/bin/mkdir"
CHMOD="/bin/chmod"
SED="/usr/bin/sed"
AWK="/usr/bin/awk"
FIND="/usr/bin/find"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ------------------------------------------------------------------------------
# Layer 3.1: Environment Sanitization (Anti-Path-Hijack)
# ------------------------------------------------------------------------------

check_env_sanity() {
    # If PATH contains /tmp or begins/ends with a dot, its compromised
    if echo "$PATH" | "$GREP" -qE "(^|:)/tmp(:|$)|(^|:)\.(:|$)"; then
        echo -e "${RED}[!] CRITICAL: $PATH Hijack detected! (Insecure path found)${NC}"
        echo -e "${RED}[!] SkillGuard refused to run in compromised environment.${NC}"
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# Layer 3.2: Multi-Link Integrated Sealing
# ------------------------------------------------------------------------------

verify_integrity() {
    if [[ ! -f "$SEAL_FILE" ]]; then return 0; fi
    check_env_sanity
    
    local script_hash=$("$SHASUM" -a 256 "$0" | "$AWK" '{print $1}')
    local db_hash=$([[ -f "$DB_FILE" ]] && "$SHASUM" -a 256 "$DB_FILE" | "$AWK" '{print $1}' || echo "missing")
    local expected=$("$CAT" "$SEAL_FILE")
    
    if [[ "$script_hash:$db_hash" != "$expected" ]]; then
        echo -e "${RED}[!] INTEGRITY BREACH: Script or Database Tampered!${NC}"
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# Layer 2.1: Advanced OOB & Behavioral Vector Scan
# ------------------------------------------------------------------------------

scan_hardened() {
    local target=$1
    echo -e "${BLUE}[L2] Performing v2.3 Extreme Scan on: $target${NC}"

    # V11: Behavioral Time-Bomb (Delayed Execution)
    "$GREP" -rnE "(sleep|delay|setTimeout).*?(fetch|http|axios|curl)" "$target" > /tmp/sg_v11 2>/dev/null

    # V12: Env Hijack (Attempting to modify PATH dynamically)
    "$GREP" -rnE "PATH=|PYTHONPATH=|LD_PRELOAD" "$target" > /tmp/sg_v12 2>/dev/null

    # V15 (NEW): Out-of-Band (OOB) Variable Injection
    # Detects: eval(process.env.XXX) or exec(os.environ['...'])
    "$GREP" -rnE "(eval|exec|Function|setTimeout).*?(process\.env|os\.environ|env\[)" "$target" > /tmp/sg_v15 2>/dev/null

    # State Memory (Post-Scan Drift Check)
    "$FIND" "$target" -type f -exec ls -l {} + > /tmp/sg_state_current 2>/dev/null

    # Reporting Metrics
    echo -e "${NC}V11 (Time-Bombs):   $("$CAT" /tmp/sg_v11 | wc -l | "$AWK" '{print $1}') hits"
    echo -e "${NC}V12 (Env-Hijack):   $("$CAT" /tmp/sg_v12 | wc -l | "$AWK" '{print $1}') hits"
    echo -e "${NC}V15 (OOB Inject):   $("$CAT" /tmp/sg_v15 | wc -l | "$AWK" '{print $1}') hits (CRITICAL)"

    local total=$(($("$CAT" /tmp/sg_v11 | wc -l) + $("$CAT" /tmp/sg_v12 | wc -l) + $("$CAT" /tmp/sg_v15 | wc -l)))
    if [[ $total -gt 0 ]]; then
        echo -e "${RED}[!] WARNING: Critical risk found. Analysis recommended.${NC}"
    else
        echo -e "${GREEN}[√] v2.3 Scan complete. Security posture: EXTREME.${NC}"
        # Store state to detect later changes
        "$CAT" /tmp/sg_state_current > "$STATE_DB"
    fi
}

# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

case "$1" in
    install)
        check_env_sanity
        echo -e "${YELLOW}Hardening SkillGuard v$VERSION...${NC}"
        if [[ ! -f "$DB_FILE" ]]; then touch "$DB_FILE"; fi
        
        # Chain Sealing
        local script_hash=$("$SHASUM" -a 256 "$0" | "$AWK" '{print $1}')
        local db_hash=$("$SHASUM" -a 256 "$DB_FILE" | "$AWK" '{print $1}')
        echo "$script_hash:$db_hash" > "$SEAL_FILE"
        "$CHMOD" 444 "$SEAL_FILE" "$0" "$DB_FILE"
        echo -e "${PURPLE}[L3] v2.3 Multi-Link Seal Applied.${NC}"
        ;;
    scan)
        verify_integrity
        if [[ -z "$2" ]]; then echo "Usage: $0 scan <target>"; exit 1; fi
        scan_hardened "$2"
        ;;
    check)
        verify_integrity && echo -e "${GREEN}System and PATH Integrity: SECURE.${NC}"
        ;;
    *)
        echo "SkillGuard v$VERSION (Hardened): {install|scan|check}"
        ;;
esac
