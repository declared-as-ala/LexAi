#!/bin/bash
# LexAI auto-deploy: called by cron every 5 min
# Checks GitHub for new commits; rebuilds and restarts if found.

REPO=/opt/lexai/LexAi
LOG=/opt/lexai/auto-deploy.log
LOCK=/opt/lexai/deploy.lock

# Prevent concurrent deploys
if [ -f "$LOCK" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M')] Already running — skip" >> "$LOG"
  exit 0
fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

cd "$REPO"

# Current local commit
CURRENT=$(git rev-parse HEAD 2>/dev/null)

# Fetch without merging (public repo — no auth needed)
git fetch origin main --quiet 2>/dev/null

# Latest remote commit
LATEST=$(git rev-parse FETCH_HEAD 2>/dev/null)

# Nothing to do
if [ "$CURRENT" = "$LATEST" ] || [ -z "$LATEST" ]; then
  exit 0
fi

{
  echo ""
  echo "========================================"
  echo "[$(date '+%Y-%m-%d %H:%M')] New commit detected"
  echo "  from : ${CURRENT:0:8}"
  echo "  to   : ${LATEST:0:8}"
  echo "========================================"

  # Apply latest code
  git reset --hard FETCH_HEAD

  # Rebuild and restart all containers
  docker compose -f docker-compose.vps-build.yml --env-file .env.prod up --build -d --remove-orphans

  # Clean up dangling images to save disk
  docker image prune -f

  echo "[$(date '+%Y-%m-%d %H:%M')] Deploy complete"
} >> "$LOG" 2>&1
