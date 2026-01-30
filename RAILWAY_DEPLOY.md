# Deploy Live Transcription to Railway

## ✅ Files Ready for Deployment

All files are ready in: `C:\BlueBerryTech\VoiceAgent\Pipecat\testing_framework\webapp\`

- ✅ `live_server_simple.py` - Main server
- ✅ `requirements.txt` - Python dependencies
- ✅ `railway.json` - Railway configuration
- ✅ `.gitignore` - Excludes sensitive files

## 🚀 Deploy to Railway (5 Minutes)

### Step 1: Sign Up for Railway

1. Go to: **https://railway.app**
2. Click **"Start a New Project"**
3. Sign up with **GitHub** (recommended) or email

### Step 2: Initialize Git Repository

Open terminal in the webapp folder:

```bash
cd C:\BlueBerryTech\VoiceAgent\Pipecat\testing_framework\webapp

# Initialize git
git init

# Add files
git add live_server_simple.py requirements.txt railway.json .gitignore base44_demo.html base44_simple_example.js

# Commit
git commit -m "Initial commit - Live transcription server"
```

### Step 3: Create Railway Project

**Option A: Railway CLI (Easiest)**

```bash
# Install Railway CLI
npm install -g @railway/cli

# OR (Windows)
winget install Railway.CLI

# Login to Railway
railway login

# Create new project
railway init

# Link to Railway
railway link

# Deploy!
railway up
```

**Option B: GitHub Deployment**

```bash
# 1. Create GitHub repo
# Go to: https://github.com/new
# Name: live-transcription
# Create repository

# 2. Push code
git remote add origin https://github.com/YOUR_USERNAME/live-transcription.git
git branch -M main
git push -u origin main

# 3. In Railway dashboard:
# - Click "New Project"
# - Select "Deploy from GitHub repo"
# - Choose your repo
# - Railway auto-detects and deploys!
```

**Option C: Railway Dashboard (No Git)**

```bash
# 1. Zip the folder
# Create a zip of: live_server_simple.py, requirements.txt, railway.json

# 2. Go to Railway dashboard
# - Click "New Project"
# - Click "Empty Project"
# - Upload zip file

# Note: This method doesn't support auto-deploy on changes
```

### Step 4: Add Environment Variables

In Railway dashboard:

1. Click your project
2. Go to **"Variables"** tab
3. Add:
   ```
   DEEPGRAM_API_KEY=5b335d685ba1b2ea6b0b0c2de09ee754a352c253
   ```
4. Click **"Add"**

### Step 5: Get Your URL

Railway will automatically:
- ✅ Generate a public URL: `https://your-app.up.railway.app`
- ✅ Deploy your server
- ✅ Start it automatically

Look for: **"Deployments"** tab → Click latest deployment → Copy **"Domain"**

Example: `https://live-transcription-production.up.railway.app`

### Step 6: Update Demo Page

Edit `base44_demo.html` line 432:

```javascript
// OLD
serverUrl: 'ws://localhost:5005',

// NEW
serverUrl: 'wss://your-app.up.railway.app',
```

**Important**: Change `ws://` to `wss://` (secure WebSocket)

### Step 7: Host Demo Page

**Option A: GitHub Pages** (Free, easiest)

```bash
# 1. Create a gh-pages branch
git checkout -b gh-pages

# 2. Keep only HTML/JS files
git rm -rf --cached *
git add base44_demo.html base44_simple_example.js
git commit -m "Demo page"

# 3. Push to gh-pages
git push origin gh-pages

# 4. Enable GitHub Pages
# Go to: Settings → Pages → Source: gh-pages branch
# Your page will be at: https://YOUR_USERNAME.github.io/live-transcription/base44_demo.html
```

**Option B: Railway Static Site** (Same platform)

```bash
# 1. Create new Railway project
railway init demo-page

# 2. Add static site service
# In Railway dashboard → Add service → Static Site
# Point to your HTML file

# 3. Railway hosts it
```

**Option C: Netlify/Vercel** (Free, drag & drop)

- Go to: https://netlify.com or https://vercel.com
- Drag `base44_demo.html` + `base44_simple_example.js`
- Get instant URL

## 🎯 Final URLs

After deployment, you'll have:

### Backend (Railway):
```
https://live-transcription-production.up.railway.app
```

Test it:
```bash
curl https://live-transcription-production.up.railway.app
```

### Frontend (GitHub Pages/Netlify):
```
https://your-username.github.io/live-transcription/base44_demo.html
```

Share this URL with testers!

## ✅ Verify Deployment

### Test WebSocket Connection:

Open browser console on your demo page:

```javascript
const ws = new WebSocket('wss://your-app.up.railway.app/ws/transcribe');
ws.onopen = () => console.log('✅ Connected!');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('❌ Error:', e);
```

### Check Server Logs:

In Railway dashboard:
- Click your project
- Go to **"Deployments"**
- Click latest deployment
- View **"Logs"** tab

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:XXXX
INFO:     Application startup complete.
```

## 🔧 Troubleshooting

### Issue: "Module not found"
**Fix**: Check `requirements.txt` has all dependencies
```bash
railway logs
# Look for missing module errors
```

### Issue: "WebSocket connection failed"
**Fix**: Make sure you're using `wss://` not `ws://`
```javascript
// ❌ Wrong
ws://your-app.railway.app

// ✅ Correct
wss://your-app.railway.app
```

### Issue: "502 Bad Gateway"
**Fix**: Check environment variables
```bash
# In Railway dashboard → Variables
# Make sure DEEPGRAM_API_KEY is set
```

### Issue: "Connection timeout"
**Fix**: Railway may be sleeping (free tier)
- First request wakes it up (takes ~30 seconds)
- Subsequent requests are fast

## 💰 Railway Costs

- **Free**: $5/month credit (enough for testing)
- **After free credit**: ~$5/month for this simple server
- **Monitor usage**: Railway dashboard → Usage tab

## 🔄 Update Deployment

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Updated server"

# Push to Railway (auto-deploys)
git push origin main

# Or use CLI
railway up
```

Railway auto-deploys on every push!

## 🎉 You're Done!

Your live transcription server is now:
- ✅ Publicly accessible
- ✅ HTTPS/WSS secured
- ✅ Auto-scaling
- ✅ Running 24/7

Share your demo page URL with anyone to test! 🚀

## Quick Commands Reference

```bash
# Deploy
railway up

# View logs
railway logs

# Open in browser
railway open

# Check status
railway status

# Environment variables
railway variables

# Rollback deployment
railway rollback
```

## Next Steps

1. ✅ Test from different devices/networks
2. ✅ Monitor Railway logs for errors
3. ✅ Add custom domain (optional)
4. ✅ Set up monitoring/alerts
5. ✅ Share with testers!
