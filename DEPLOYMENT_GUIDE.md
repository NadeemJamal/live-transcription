# Live Transcription Demo - Deployment Guide

## Current Status
- ✅ Server running locally on `http://localhost:5005`
- ✅ Demo page at `base44_demo.html`
- ❌ Only accessible on your machine

## Make it Live - 3 Options

---

## Option 1: ngrok (Fastest - 5 minutes)

**Best for**: Quick testing, demos, temporary sharing

### Steps:

1. **Download ngrok**:
   - Go to: https://ngrok.com/download
   - Or run: `winget install ngrok`

2. **Install ngrok**:
   ```bash
   # Extract and move to a folder in PATH
   # Or just run from download folder
   ```

3. **Sign up** (free):
   - Go to: https://dashboard.ngrok.com/signup
   - Get your auth token

4. **Authenticate**:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

5. **Start tunnel**:
   ```bash
   ngrok http 5005
   ```

6. **Copy the public URL**:
   ```
   Forwarding   https://abc123.ngrok.io -> http://localhost:5005
   ```

7. **Update demo page**:
   - Change `ws://localhost:5005` to `wss://abc123.ngrok.io`
   - Share the ngrok URL with testers

**Pros**:
- ✅ Instant - takes 5 minutes
- ✅ Free tier available
- ✅ HTTPS/WSS included
- ✅ No code changes needed

**Cons**:
- ❌ URL changes every restart (free tier)
- ❌ Must keep your computer running
- ❌ Limited to 1 connection on free tier

---

## Option 2: Railway.app (Best for Production - 15 minutes)

**Best for**: Permanent deployment, multiple users, production use

### Steps:

1. **Create Railway account**:
   - Go to: https://railway.app
   - Sign up with GitHub

2. **Prepare deployment files**:

**Create `requirements.txt`**:
```txt
fastapi
uvicorn[standard]
websockets
deepgram-sdk
python-dotenv
loguru
```

**Create `railway.json`**:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn live_server_simple:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Create `.env.railway`**:
```bash
DEEPGRAM_API_KEY=5b335d685ba1b2ea6b0b0c2de09ee754a352c253
```

3. **Initialize git** (if not already):
   ```bash
   cd C:\BlueBerryTech\VoiceAgent\Pipecat\testing_framework\webapp
   git init
   git add live_server_simple.py requirements.txt railway.json
   git commit -m "Initial commit"
   ```

4. **Deploy to Railway**:
   - Click "New Project" in Railway dashboard
   - Choose "Deploy from GitHub repo"
   - Or use Railway CLI: `railway up`

5. **Add environment variables**:
   - In Railway dashboard → Variables
   - Add `DEEPGRAM_API_KEY`

6. **Get your URL**:
   - Railway will give you: `https://your-app.railway.app`

7. **Update demo page**:
   - Change to: `wss://your-app.railway.app/ws/transcribe`

**Pros**:
- ✅ Free $5/month credit
- ✅ Persistent URL
- ✅ Auto-deployment from GitHub
- ✅ Scales automatically
- ✅ Built-in HTTPS/WSS
- ✅ No need to keep your PC running

**Cons**:
- ❌ Takes 15 minutes to set up
- ❌ Requires GitHub account

---

## Option 3: Render.com (Alternative to Railway - 15 minutes)

**Best for**: Same as Railway, alternative platform

### Steps:

1. **Create Render account**:
   - Go to: https://render.com
   - Sign up with GitHub

2. **Prepare files**:

**Create `requirements.txt`** (same as above)

**Create `render.yaml`**:
```yaml
services:
  - type: web
    name: live-transcription
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn live_server_simple:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DEEPGRAM_API_KEY
        value: 5b335d685ba1b2ea6b0b0c2de09ee754a352c253
```

3. **Deploy**:
   - Connect GitHub repo
   - Click "New Web Service"
   - Select repo and branch
   - Render auto-detects Python

4. **Get URL**:
   - Render gives you: `https://your-app.onrender.com`

**Pros/Cons**: Similar to Railway

---

## Option 4: Deploy HTML to GitHub Pages + Use Cloud Backend

**Best for**: Separate frontend/backend deployment

### Frontend (HTML):

1. **Create GitHub repo** for the HTML page
2. **Enable GitHub Pages**:
   - Repo Settings → Pages
   - Source: main branch
3. **Update JS** to point to your backend URL
4. **Access at**: `https://yourusername.github.io/repo-name`

### Backend:
- Deploy server using Railway/Render (above)

---

## Recommended Setup

For testing/demo:
1. **Use ngrok** (5 minutes, instant)

For production/sharing:
1. **Use Railway** for backend server
2. **Use GitHub Pages** for HTML demo page
3. **Point HTML to Railway URL**

---

## Quick Start: ngrok Setup

```bash
# 1. Install ngrok
winget install ngrok

# 2. Authenticate (get token from https://dashboard.ngrok.com)
ngrok config add-authtoken YOUR_TOKEN

# 3. Start tunnel (keep this running)
ngrok http 5005

# 4. Copy the https URL shown (like https://abc123.ngrok.io)

# 5. Update base44_demo.html:
# Change: ws://localhost:5005
# To: wss://abc123.ngrok.io  (note: wss not ws!)

# 6. Share the ngrok URL with testers!
```

---

## Security Notes

⚠️ **IMPORTANT**: Your Deepgram API key is in the code!

For production:
- ✅ Move API key to environment variables
- ✅ Add rate limiting
- ✅ Add authentication if needed
- ✅ Monitor API usage

---

## Need Help?

Choose based on your needs:
- **Quick test/demo today**: Use ngrok
- **Permanent public demo**: Use Railway + GitHub Pages
- **Production app**: Railway + custom domain + auth

Let me know which option you want and I'll help set it up!
