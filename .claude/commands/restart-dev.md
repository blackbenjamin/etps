# Restart Dev Servers Command

Cleanly restart the development servers (frontend and/or backend) with proper cache clearing.

## Instructions

1. **Check current server status:**
   - Use `pgrep -f "next dev"` to check if Next.js frontend is running
   - Use `pgrep -f "uvicorn main:app"` to check if FastAPI backend is running

2. **Kill existing processes:**
   - Run `pkill -f "next dev"` to stop any running Next.js servers
   - Run `pkill -f "uvicorn main:app"` to stop any running FastAPI servers
   - Wait 2 seconds for clean shutdown

3. **Clear Next.js cache (frontend only):**
   - Delete the `.next` directory: `rm -rf frontend/.next`
   - This resolves CSS/JS 404 errors from corrupted build cache

4. **Restart servers in background:**

   **Frontend:**
   ```bash
   cd /Users/benjaminblack/projects/etps/frontend && npm run dev
   ```

   **Backend:**
   ```bash
   cd /Users/benjaminblack/projects/etps/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify startup:**
   - Wait for "Ready in Xms" message from Next.js
   - Wait for "Uvicorn running on" message from FastAPI
   - Confirm no 404 errors for static assets

## Common Issues

- **404 for CSS/JS files:** Delete `.next` folder before restarting frontend
- **Port already in use:** Kill existing processes first
- **Backend not detecting changes:** Check uvicorn --reload is enabled

## Usage

The user can specify which server to restart:
- "restart frontend" - Only restart Next.js
- "restart backend" - Only restart FastAPI
- "restart all" or just "restart" - Restart both

Always run servers in background mode so the user can continue working.
