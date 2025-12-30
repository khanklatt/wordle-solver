# Fix for Missing X-CommitId Header

## Problem
- Frontend shows version `e6e4fa9` (JavaScript is updated)
- Backend doesn't show `X-CommitId` header (Python code is cached in Docker)

## Root Cause
The Docker container was built with old Python code. The `api/` directory and `wordle_solver.py` 
are copied into the image at build time, not mounted as volumes.

## Solution

### Option 1: Rebuild Docker Image (Recommended)
```bash
# Stop containers
docker-compose down

# Rebuild without cache
docker-compose build --no-cache

# Start fresh
docker-compose up
```

### Option 2: Use Volume Mounts (Development)
I've updated `docker-compose.yml` to mount Python code as volumes.
After restarting, Python code changes will be reflected immediately:

```bash
docker-compose restart
```

## Verification
After rebuilding/restarting:
1. Check browser console: Should see `Version: e6e4fa9`
2. Check API response headers: Should see `X-CommitId: e6e4fa9`
3. If both match, code is synchronized!
