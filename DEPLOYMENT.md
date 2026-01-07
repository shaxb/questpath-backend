# QuestPath Deployment Guide

## Prerequisites
1. GitHub account
2. Vercel account (sign up with GitHub)
3. Render account (sign up with GitHub)
4. Upstash account (free Redis)

---

## 🚀 Step 1: Create Upstash Redis (1 minute)

1. Go to [upstash.com](https://upstash.com) → Sign up/Login
2. Click "Create Database"
3. Name: `questpath-redis`
4. Region: Choose closest to you
5. Type: **Regional** (free tier)
6. Click "Create"
7. Copy the **Redis URL** (looks like: `rediss://default:xxx@xxx.upstash.io:6379`)
8. Save it for later

---

## 🗄️ Step 2: Deploy Backend to Render (5 minutes)

### 2.1 Push to GitHub
```bash
cd c:/Users/abdux/OneDrive/Desktop/goal
git init
git add .
git commit -m "Initial commit"
# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/questpath-backend.git
git push -u origin main
```

### 2.2 Create PostgreSQL Database on Render
1. Go to [render.com](https://render.com) → Sign up/Login
2. Click "New +" → "PostgreSQL"
3. Name: `questpath-db`
4. Database: `questpath`
5. User: `questpath`
6. Region: Choose closest
7. Plan: **Free** (spins down after 15 min inactivity)
8. Click "Create Database"
9. Wait for it to provision (~2 minutes)
10. Copy the **Internal Database URL** (starts with `postgresql://`)
11. **IMPORTANT:** Change `postgresql://` to `postgresql+asyncpg://` (add `+asyncpg`)

### 2.3 Deploy FastAPI Backend
1. Click "New +" → "Web Service"
2. Connect your GitHub repo: `questpath-backend`
3. Configure:
   - **Name:** `questpath-api`
   - **Region:** Same as database
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `sh migrate.sh && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

4. Add Environment Variables (click "Advanced" → "Add Environment Variable"):
   ```
   DATABASE_URL = <paste your Internal Database URL with +asyncpg>
   REDIS_URL = <paste your Upstash Redis URL>
   JWT_SECRET = <generate random string, e.g., run: python -c "import secrets; print(secrets.token_urlsafe(32))">
   OPENAI_API_KEY = <your OpenAI API key>
   FRONTEND_URL = https://questpath.vercel.app (you'll update this later)
   ENVIRONMENT = production
   GOOGLE_CLIENT_ID = <your Google OAuth client ID>
   GOOGLE_CLIENT_SECRET = <your Google OAuth client secret>
   ```

5. Click "Create Web Service"
6. Wait for deployment (~5 minutes)
7. Copy your backend URL (like: `https://questpath-api.onrender.com`)

---

## 🎨 Step 3: Deploy Frontend to Vercel (2 minutes)

### 3.1 Push Frontend to GitHub
```bash
cd c:/Users/abdux/OneDrive/Desktop/questpath-frontend
git init
git add .
git commit -m "Initial commit"
# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/questpath-frontend.git
git push -u origin main
```

### 3.2 Deploy to Vercel
1. Go to [vercel.com](https://vercel.com) → Login with GitHub
2. Click "Add New" → "Project"
3. Import your `questpath-frontend` repo
4. Configure:
   - **Framework Preset:** Next.js
   - **Root Directory:** ./
   - **Build Command:** (leave default)
   - **Output Directory:** (leave default)

5. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL = <paste your Render backend URL>
   NEXTAUTH_URL = https://questpath.vercel.app
   NEXTAUTH_SECRET = <generate random string>
   GOOGLE_CLIENT_ID = <your Google OAuth client ID>
   GOOGLE_CLIENT_SECRET = <your Google OAuth client secret>
   ```

6. Click "Deploy"
7. Wait (~2 minutes)
8. Copy your Vercel URL (like: `https://questpath.vercel.app`)

### 3.3 Update Backend CORS
1. Go back to Render → Your backend service
2. Update environment variable:
   ```
   FRONTEND_URL = https://questpath.vercel.app
   ```
3. Save (will auto-redeploy)

---

## ✅ Step 4: Test Your Deployment

1. Visit your Vercel URL: `https://questpath.vercel.app`
2. Try registering a new account
3. Create a goal
4. Take a quiz
5. Check leaderboard
6. Update profile

---

## 🔧 Troubleshooting

### Backend errors:
- Check Render logs: Dashboard → Your service → Logs
- Verify DATABASE_URL has `+asyncpg`
- Ensure migrations ran (check logs for "Migrations completed")

### Frontend errors:
- Check Vercel deployment logs
- Verify NEXT_PUBLIC_API_URL is correct
- Check browser console for CORS errors

### CORS errors:
- Ensure FRONTEND_URL in backend matches your Vercel URL exactly
- Wait for backend redeploy after updating FRONTEND_URL

---

## 💰 Free Tier Limits

- **Render Free:** 
  - Database: 1GB storage, expires after 90 days
  - Web Service: Spins down after 15 min inactivity (cold start ~30s)
  - 750 hours/month

- **Vercel Free:**
  - 100GB bandwidth/month
  - Unlimited deployments
  - Automatic HTTPS

- **Upstash Free:**
  - 10,000 commands/day
  - 256MB storage
  - Perfect for your scale

---

## 🚀 Optional: Set Up Auto-Deploy

Both Render and Vercel automatically redeploy when you push to GitHub main branch. No extra setup needed!

---

## 📝 Next Steps

After deployment works:
1. Add custom domain (optional)
2. Implement Redis caching (10x speed boost)
3. Add rate limiting
4. Set up monitoring (Sentry)
5. Optimize database queries

---

Your app is now live at $0/month! 🎉
