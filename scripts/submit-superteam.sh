#!/usr/bin/env bash
# SuperTeam Earn Bounty Submission Script
# Bounty: "Audit & Fix Open-Source Solana Repositories" (Agents)
# https://superteam.fun/earn/listing/fix-open-source-solana-repos-agents
#
# Usage:
#   1. Run without args to register a new agent:
#      ./scripts/submit-superteam.sh
#
#   2. Or set your API key if already registered:
#      export SUPERTEAM_API_KEY="sk_..."
#      ./scripts/submit-superteam.sh
#
# Prerequisites: curl, jq

set -euo pipefail

BASE_URL="https://earn.superteam.fun"
LISTING_SLUG="fix-open-source-solana-repos-agents"
AGENT_NAME="anchor-shield-v2-agent"
SUBMISSION_FILE="$(dirname "$0")/../submission/SUBMISSION_CONTENT.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[-]${NC} $1"; exit 1; }

# Check dependencies
command -v curl >/dev/null 2>&1 || err "curl is required"
command -v jq >/dev/null 2>&1 || err "jq is required"

# Step 1: Register agent or use existing key
if [ -z "${SUPERTEAM_API_KEY:-}" ]; then
    log "No API key found. Registering new agent..."
    REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/agents" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${AGENT_NAME}\"}")

    echo "$REGISTER_RESPONSE" | jq . 2>/dev/null || echo "$REGISTER_RESPONSE"

    API_KEY=$(echo "$REGISTER_RESPONSE" | jq -r '.apiKey // .api_key // empty' 2>/dev/null)
    CLAIM_CODE=$(echo "$REGISTER_RESPONSE" | jq -r '.claimCode // .claim_code // empty' 2>/dev/null)

    if [ -z "$API_KEY" ]; then
        err "Failed to extract API key from registration response. Check the response above."
    fi

    log "Agent registered successfully!"
    log "API Key: ${API_KEY}"
    if [ -n "$CLAIM_CODE" ]; then
        warn "SAVE THIS CLAIM CODE to claim rewards later: ${CLAIM_CODE}"
    fi

    export SUPERTEAM_API_KEY="$API_KEY"
else
    log "Using existing API key: ${SUPERTEAM_API_KEY:0:10}..."
fi

# Step 2: Discover the listing
log "Fetching listing details for: ${LISTING_SLUG}..."
LISTING_RESPONSE=$(curl -s "${BASE_URL}/api/agents/listings/details/${LISTING_SLUG}" \
    -H "Authorization: Bearer ${SUPERTEAM_API_KEY}")

echo "$LISTING_RESPONSE" | jq '{id, title, status, agentAccess, type}' 2>/dev/null || echo "$LISTING_RESPONSE"

LISTING_ID=$(echo "$LISTING_RESPONSE" | jq -r '.id // empty' 2>/dev/null)

if [ -z "$LISTING_ID" ]; then
    warn "Could not extract listing ID automatically."
    warn "Trying to search live listings..."

    LIVE_RESPONSE=$(curl -s "${BASE_URL}/api/agents/listings/live?take=50" \
        -H "Authorization: Bearer ${SUPERTEAM_API_KEY}")

    LISTING_ID=$(echo "$LIVE_RESPONSE" | jq -r ".[] | select(.slug == \"${LISTING_SLUG}\") | .id" 2>/dev/null)

    if [ -z "$LISTING_ID" ]; then
        err "Could not find listing. You may need to provide the listing ID manually."
    fi
fi

log "Found listing ID: ${LISTING_ID}"

# Step 3: Prepare submission content
TITLE="anchor-shield-v2: Automated CI Security Pipeline for Solana - 29 Programs, 1 CVE, 0% FP Rate"
REPO_URL="https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2"

# Read the full description from the submission file
if [ -f "$SUBMISSION_FILE" ]; then
    DESCRIPTION=$(cat "$SUBMISSION_FILE")
else
    warn "Submission content file not found at ${SUBMISSION_FILE}"
    DESCRIPTION="See repository README and END_TO_END_VALIDATION.md for full details."
fi

# Step 4: Submit
log "Submitting to bounty..."

SUBMIT_PAYLOAD=$(jq -n \
    --arg listingId "$LISTING_ID" \
    --arg link "$REPO_URL" \
    --arg otherInfo "$DESCRIPTION" \
    '{
        listingId: $listingId,
        link: $link,
        otherInfo: $otherInfo
    }')

SUBMIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/agents/submissions/create" \
    -H "Authorization: Bearer ${SUPERTEAM_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$SUBMIT_PAYLOAD")

echo ""
log "Submission response:"
echo "$SUBMIT_RESPONSE" | jq . 2>/dev/null || echo "$SUBMIT_RESPONSE"

SUBMISSION_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.id // empty' 2>/dev/null)
if [ -n "$SUBMISSION_ID" ]; then
    echo ""
    log "========================================="
    log "SUBMISSION SUCCESSFUL!"
    log "========================================="
    log "Submission ID: ${SUBMISSION_ID}"
    log "Listing: ${LISTING_SLUG}"
    log "Repository: ${REPO_URL}"
    if [ -n "${CLAIM_CODE:-}" ]; then
        warn ""
        warn "IMPORTANT: Save your claim code to receive rewards:"
        warn "Claim Code: ${CLAIM_CODE}"
        warn "API Key: ${SUPERTEAM_API_KEY}"
    fi
else
    warn "Could not confirm submission ID. Check the response above for details."
fi
