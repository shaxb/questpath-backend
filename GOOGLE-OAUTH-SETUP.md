# Google OAuth Setup Guide

## Problem
Getting "Error 401: invalid_client" when trying to sign in with Google.

## Solution

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. If prompted, configure OAuth consent screen first:
   - User Type: **External**
   - App name: `QuestPath`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `email` and `profile`
   - Test users: Add your email (optional during development)
   - Click **Save and Continue**

6. Now create OAuth client ID:
   - Application type: **Web application**
   - Name: `QuestPath Web Client`
   - **Authorized JavaScript origins:**
     ```
     http://localhost:3000
     https://your-vercel-app.vercel.app
     ```
   - **Authorized redirect URIs:**
     ```
     http://localhost:3000/api/auth/callback/google
     https://your-vercel-app.vercel.app/api/auth/callback/google
     ```
   - Click **Create**

7. Copy your **Client ID** and **Client Secret**

---

### Step 2: Update Backend (Render) Environment Variables

1. Go to your Render dashboard
2. Select your `questpath-api` service
3. Go to **Environment** tab
4. Update these variables:
   ```
   GOOGLE_CLIENT_ID = <paste your Client ID>
   GOOGLE_CLIENT_SECRET = <paste your Client Secret>
   ```
5. Click **Save Changes** (will trigger redeploy)

---

### Step 3: Update Frontend (Vercel) Environment Variables

1. Go to your Vercel dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Update/add these variables:
   ```
   GOOGLE_CLIENT_ID = <paste your Client ID>
   GOOGLE_CLIENT_SECRET = <paste your Client Secret>
   ```
5. **Important:** Redeploy to apply changes
   - Go to **Deployments** tab
   - Click ⋯ on latest deployment → **Redeploy**

---

### Step 4: Update Redirect URIs After Deployment

Once you have your actual Vercel URL (e.g., `https://questpath-abc123.vercel.app`):

1. Go back to Google Cloud Console → Credentials
2. Edit your OAuth client
3. Update **Authorized redirect URIs** with your real Vercel URL:
   ```
   https://questpath-abc123.vercel.app/api/auth/callback/google
   ```
4. Save

---

## Testing OAuth

1. Visit your deployed app
2. Click "Sign in with Google"
3. Should redirect to Google login
4. After login, redirects back to your app
5. Check if you're logged in

---

## Common Issues

### "Error 401: invalid_client"
- **Cause:** Client ID/Secret mismatch or not set
- **Fix:** Double-check environment variables in Vercel and Render

### "Redirect URI mismatch"
- **Cause:** The redirect URI isn't registered in Google Console
- **Fix:** Add the exact URI to "Authorized redirect URIs" in Google Console

### OAuth works locally but not in production
- **Cause:** Forgot to add production URLs to Google Console
- **Fix:** Add your Vercel URL to both "Authorized JavaScript origins" and "Authorized redirect URIs"

---

## Skip OAuth (For Now)

If you want to deploy without OAuth:

1. Just use email/password registration
2. Remove Google sign-in button from frontend (optional)
3. Set these to empty strings in environment variables:
   ```
   GOOGLE_CLIENT_ID = ""
   GOOGLE_CLIENT_SECRET = ""
   ```

You can add OAuth later anytime!
