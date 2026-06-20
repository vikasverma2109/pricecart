# Deploy PriceCart to Railway

No passwords needed — both GitHub and Railway use "Login with Google" or email OTP.

---

## Step 1 — Push code to GitHub

1. Go to **https://github.com** → sign in (or create a free account)
2. Click **+** (top right) → **New repository**
   - Name: `pricecart` (or anything)
   - Private or Public — your choice
   - Click **Create repository**
3. Open **Command Prompt** in the `Price Compare Tool` folder:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/pricecart.git
   git push -u origin main
   ```
   *(GitHub will ask you to log in via browser — click Authorize)*

---

## Step 2 — Deploy on Railway

1. Go to **https://railway.app** → click **Login** → use GitHub login
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `pricecart` repository
4. Railway auto-detects the `Dockerfile` → click **Deploy**
5. Wait ~3–5 minutes for the build (it installs Chromium inside Docker)

---

## Step 3 — Get your live URL

1. In Railway dashboard → click your project → **Settings** tab
2. Under **Domains** → click **Generate Domain**
3. You get a free URL like `pricecart-production.up.railway.app`
4. Open it on your phone — it works!

---

## Notes

- **Free tier**: Railway gives $5/month credit — enough for ~500 hours of runtime
- **Chromium memory**: The app uses ~400MB RAM. Railway's free tier allows 512MB — it'll be tight. If it crashes, upgrade to Hobby plan ($5/month) for 1GB RAM.
- **Redeploy**: Every time you push to GitHub, Railway redeploys automatically.
- **Logs**: Railway dashboard → your service → **Logs** tab (useful for debugging)

---

## Quick test after deploy

Open in browser:
```
https://your-railway-url.up.railway.app/api/health
```
Should return: `{"status":"ok","platforms":6}`
