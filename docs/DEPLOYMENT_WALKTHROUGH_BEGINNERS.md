# ETPS Deployment Walkthrough for Beginners
**Step-by-Step Guide Using Web Dashboards (No CLI Required)**

This guide assumes you've never deployed before. We'll use web interfaces for everything.

---

## 📋 Before You Start

### What You'll Need

1. ✅ GitHub account (you already have the repo)
2. ✅ Railway account (sign up at https://railway.app)
3. ✅ Vercel account (sign up at https://vercel.com)
4. ✅ Qdrant Cloud account (sign up at https://cloud.qdrant.io)
5. ✅ Cloudflare account (you already have this for your domain)
6. ✅ API Keys:
   - Anthropic API key (from https://console.anthropic.com)
   - OpenAI API key (from https://platform.openai.com)

### Estimated Time
- **Total**: 2-3 hours (including account setup)
- **Qdrant**: 15 minutes
- **Railway**: 45 minutes
- **Vercel**: 30 minutes
- **Testing**: 30 minutes

---

## Part 1: Qdrant Cloud Setup (15 minutes)

### Step 1.1: Create Account

1. Go to https://cloud.qdrant.io/
2. Click **Sign Up**
3. Use GitHub or email to sign up
4. Verify your email

### Step 1.2: Create Cluster

1. After login, click **Create Cluster**
2. Fill in:
   - **Cluster Name**: `etps-production`
   - **Cloud Provider**: AWS
   - **Region**: `us-east-1` (or closest to you)
   - **Configuration**: Free tier (1GB)
3. Click **Create**
4. Wait 2-3 minutes for cluster to provision

### Step 1.3: Get Connection Details

1. Click on your `etps-production` cluster
2. You'll see a **Cluster URL** like: `https://abc123-xyz.aws.cloud.qdrant.io`
3. **Copy this URL** - you'll need it later

### Step 1.4: Create API Key

1. In the cluster page, click **API Keys** tab
2. Click **Create API Key**
3. Give it a name: `etps-backend`
4. Click **Create**
5. **Copy the API key** (starts with `qdrant_...`) - you can only see this once!
6. Save it somewhere safe (you'll add it to Railway later)

✅ **Checkpoint**: You should have:
- Qdrant URL: `https://abc123-xyz.aws.cloud.qdrant.io`
- Qdrant API Key: `qdrant_...`

---

## Part 2: Railway Backend Deployment (45 minutes)

### Step 2.1: Create Railway Account

1. Go to https://railway.app/
2. Click **Login** → **Login with GitHub**
3. Authorize Railway to access your GitHub

### Step 2.2: Create New Project

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. If prompted, click **Configure GitHub App** and give Railway access to your repos
4. Select repository: `blackbenjamin/etps`
5. Railway will detect it's a Python project

### Step 2.3: Configure Build Settings

1. Railway will create a service automatically
2. Click on the service card
3. Go to **Settings** tab
4. Find **Root Directory** and set it to: `backend`
5. Click **Save**

### Step 2.4: Add PostgreSQL Database

1. In your project view, click **New** button (top right)
2. Select **Database** → **Add PostgreSQL**
3. Railway will create a PostgreSQL database
4. It will automatically link to your backend service
5. Wait for it to provision (1-2 minutes)

### Step 2.5: Configure Environment Variables

This is the most important step! Here's exactly what to add:

1. Click on your **backend service** (not the database)
2. Go to **Variables** tab
3. Click **New Variable** for each of these:

#### Variable 1: ANTHROPIC_API_KEY
- **Name**: `ANTHROPIC_API_KEY`
- **Value**: Your Anthropic API key (get from https://console.anthropic.com/settings/keys)
  - Should look like: `sk-ant-api03-...`
  - Click **Create API Key** if you don't have one

#### Variable 2: OPENAI_API_KEY
- **Name**: `OPENAI_API_KEY`
- **Value**: Your OpenAI API key (get from https://platform.openai.com/api-keys)
  - Should look like: `sk-proj-...` or `sk-...`
  - Click **Create new secret key** if you don't have one

#### Variable 3: QDRANT_URL
- **Name**: `QDRANT_URL`
- **Value**: The Qdrant URL you copied earlier
  - Should look like: `https://abc123-xyz.aws.cloud.qdrant.io`

#### Variable 4: QDRANT_API_KEY
- **Name**: `QDRANT_API_KEY`
- **Value**: The Qdrant API key you copied earlier
  - Should look like: `qdrant_...`

#### Variable 5: ENVIRONMENT
- **Name**: `ENVIRONMENT`
- **Value**: `production`

#### Variable 6: ALLOWED_ORIGINS
- **Name**: `ALLOWED_ORIGINS`
- **Value**: `https://projects.benjaminblack.consulting`
  - ⚠️ **Important**: No trailing slash!

#### Variable 7: DATABASE_URL
- **Name**: `DATABASE_URL`
- **Value**: This should already be set automatically by Railway when you added PostgreSQL
  - If not, click on the PostgreSQL database → **Connect** tab → copy the **Database URL**

### Step 2.6: Deploy

1. Railway will automatically deploy after you add variables
2. Go to **Deployments** tab
3. Watch the build logs (this takes 3-5 minutes)
4. Wait for status to show **Success** ✅

### Step 2.7: Get Your Backend URL

1. Go to **Settings** tab
2. Scroll to **Networking** section
3. Click **Generate Domain**
4. Railway will give you a URL like: `etps-production.up.railway.app`
5. **Copy this URL** - you'll need it for Vercel

### Step 2.8: Test Backend

1. Open a new browser tab
2. Go to: `https://your-railway-url.up.railway.app/health`
   - Replace `your-railway-url` with your actual Railway URL
3. You should see:
   ```json
   {
     "status": "healthy",
     "version": "0.1.0",
     "environment": "production"
   }
   ```

✅ **Checkpoint**: Your backend is deployed and healthy!

---

## Part 3: Vercel Frontend Deployment (30 minutes)

### Step 3.1: Create Vercel Account

1. Go to https://vercel.com/
2. Click **Sign Up** → **Continue with GitHub**
3. Authorize Vercel

### Step 3.2: Import Project

1. Click **Add New...** → **Project**
2. Find your `etps` repository
3. Click **Import**

### Step 3.3: Configure Project Settings

1. **Framework Preset**: Should auto-detect as **Next.js** ✅
2. **Root Directory**: Click **Edit** and set to `frontend`
3. **Build Command**: Leave as `npm run build`
4. **Output Directory**: Leave as `.next`

### Step 3.4: Add Environment Variables

Before clicking Deploy, add these environment variables:

1. Click **Environment Variables** section to expand it

#### Variable 1: NEXT_PUBLIC_API_URL
- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: Your Railway backend URL (from Step 2.7)
  - Should look like: `https://etps-production.up.railway.app`
  - ⚠️ **Important**: No `/api` at the end, no trailing slash

#### Variable 2: NEXT_PUBLIC_USER_NAME
- **Name**: `NEXT_PUBLIC_USER_NAME`
- **Value**: `Benjamin Black`

2. For both variables, check all three environments:
   - ✅ Production
   - ✅ Preview
   - ✅ Development

### Step 3.5: Deploy

1. Click **Deploy**
2. Wait 2-5 minutes for build to complete
3. You'll see a success screen with a preview URL

### Step 3.6: Test Default Deployment

1. Click **Visit** to open your deployed site
2. You'll get a URL like: `etps-frontend-abc123.vercel.app`
3. Test that the page loads

✅ **Checkpoint**: Frontend is deployed on Vercel's default domain!

---

## Part 4: Custom Domain Setup (30 minutes)

### Step 4.1: Add Domain in Vercel

1. In your Vercel project, go to **Settings** → **Domains**
2. Click **Add**
3. Enter: `projects.benjaminblack.consulting`
4. Click **Add**

### Step 4.2: Configure DNS in Cloudflare

Vercel will show you what DNS records to add. Here's what to do:

1. Go to Cloudflare dashboard
2. Select your domain: `benjaminblack.consulting`
3. Go to **DNS** → **Records**
4. Click **Add record**

Fill in:
- **Type**: `CNAME`
- **Name**: `projects`
- **Target**: `cname.vercel-dns.com`
- **Proxy status**: Click the cloud icon to make it **gray** (DNS only)
  - ⚠️ **Important**: Must be gray, not orange!
- **TTL**: Auto

5. Click **Save**

### Step 4.3: Wait for DNS Propagation

1. Back in Vercel, wait for the domain to verify (1-10 minutes)
2. You'll see a green checkmark when ready
3. Vercel will automatically provision an SSL certificate

### Step 4.4: Test Custom Domain

1. Open: `https://projects.benjaminblack.consulting`
2. You should see your ETPS frontend
3. Check that HTTPS works (padlock icon in browser)

✅ **Checkpoint**: Custom domain is working!

---

## Part 5: Database Setup (15 minutes)

### Step 5.1: Initialize Database Schema

The easiest way is to let it auto-create on first API call, but you can also manually initialize:

**Option A: Auto-initialize (Recommended)**
- Just use the app - the schema will be created automatically on first database access

**Option B: Manual initialize**
1. Go to Railway → your backend service → **Deployments**
2. Click on the latest deployment
3. You'll see logs showing the schema being created

### Step 5.2: Create Your User Profile

Use the API to create your user:

1. Open a terminal or use a tool like Postman
2. Run this command (replace the URL with your Railway URL):

```bash
curl -X POST "https://your-railway-url.up.railway.app/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Benjamin Black",
    "email": "your.email@example.com",
    "linkedin_meta": {
      "top_skills": ["Strategy", "Analytics", "Leadership", "Product Management"],
      "certifications": []
    }
  }'
```

3. You should get back a response with `"id": 1`

### Step 5.3: Add Resume Data

You have two options:

**Option A: Use the frontend**
- Go to your deployed site
- Use the job intake form
- The system will work with your existing resume bullets from the database

**Option B: Migrate from local database**
- See `DATABASE_MIGRATION_GUIDE.md` for detailed instructions
- Recommended only if you have important local data

✅ **Checkpoint**: Database is set up and user profile created!

---

## Part 6: End-to-End Testing (30 minutes)

### Test 1: Health Checks

```bash
# Backend health
curl https://your-railway-url.up.railway.app/health

# Should return:
# {"status":"healthy","version":"0.1.0","environment":"production"}
```

### Test 2: Frontend Loads

1. Go to: `https://projects.benjaminblack.consulting`
2. Check that page loads without errors
3. Open browser console (F12) - should be no errors

### Test 3: API Connection

1. On the frontend, paste a job description
2. Click submit
3. Watch the network tab (F12 → Network)
4. Verify API calls go to your Railway backend
5. Check for any CORS errors (there shouldn't be any)

### Test 4: Resume Generation

1. Submit a full job description
2. Wait for resume generation to complete
3. Download the DOCX file
4. Verify it opens correctly

### Test 5: Cover Letter Generation

1. Generate a cover letter
2. Download the DOCX
3. Verify formatting

✅ **All tests passing?** You're deployed! 🎉

---

## Troubleshooting

### ❌ Backend shows "Service Unavailable"

**Check:**
1. Railway → Deployments → View logs
2. Look for errors in the logs
3. Common issues:
   - Missing environment variable
   - Database connection failed
   - Qdrant connection failed

**Fix:**
- Go to Variables tab and verify all variables are set correctly

### ❌ Frontend shows "Failed to fetch"

**Check:**
1. Browser console (F12) for CORS errors
2. Verify `NEXT_PUBLIC_API_URL` in Vercel matches your Railway URL
3. Verify `ALLOWED_ORIGINS` in Railway matches your Vercel domain

**Fix:**
- Redeploy frontend after fixing environment variables
- Make sure no trailing slashes in URLs

### ❌ Custom domain not working

**Check:**
1. Cloudflare DNS record is correct
2. Proxy status is **gray** (DNS only), not orange
3. Wait up to 24 hours for DNS propagation

**Fix:**
- Use https://dnschecker.org/ to check DNS propagation
- Verify CNAME points to `cname.vercel-dns.com`

### ❌ Database errors

**Check:**
1. Railway → PostgreSQL → Metrics
2. Verify database is running

**Fix:**
- Restart the database in Railway
- Check DATABASE_URL is set correctly

---

## What to Do After Deployment

### 1. Monitor for 24 Hours

- Check Railway logs for errors
- Monitor Vercel analytics
- Watch for any failed requests

### 2. Set Up Monitoring (Optional)

**Railway:**
- Enable usage alerts (Settings → Usage)
- Set up webhook notifications

**Vercel:**
- Enable Web Analytics (Settings → Analytics)

### 3. Update Your Portfolio

Add the live demo link:
- URL: `https://projects.benjaminblack.consulting`
- Description: "AI-powered resume and cover letter tailoring system"

### 4. Share and Test

- Share with friends for feedback
- Test with different job descriptions
- Monitor API usage and costs

---

## Cost Monitoring

### Where to Check Costs

**Railway:**
- Dashboard → Usage
- Shows current month spend
- $5 credit included with Hobby plan

**Anthropic:**
- https://console.anthropic.com/settings/usage

**OpenAI:**
- https://platform.openai.com/usage

### Expected Monthly Costs

| Service | Cost |
|---------|------|
| Railway | $5 (includes $5 credit) |
| Vercel | $0 (free tier) |
| Qdrant | $0 (free tier) |
| Anthropic | $10-20 (usage) |
| OpenAI | $5 (usage) |
| **Total** | **~$20-30/month** |

---

## Need Help?

1. **Check the logs**:
   - Railway: Deployments → Click deployment → View logs
   - Vercel: Deployments → Click deployment → Function logs

2. **Common issues**: See Troubleshooting section above

3. **Documentation**:
   - Railway: https://docs.railway.app/
   - Vercel: https://vercel.com/docs
   - Qdrant: https://qdrant.tech/documentation/

---

## Summary Checklist

- [ ] Qdrant Cloud cluster created
- [ ] Qdrant URL and API key saved
- [ ] Railway account created
- [ ] Backend deployed to Railway
- [ ] PostgreSQL added to Railway
- [ ] All environment variables set in Railway
- [ ] Backend health check passes
- [ ] Vercel account created
- [ ] Frontend deployed to Vercel
- [ ] Environment variables set in Vercel
- [ ] Custom domain added in Vercel
- [ ] DNS configured in Cloudflare
- [ ] Custom domain working with HTTPS
- [ ] User profile created in database
- [ ] End-to-end test successful
- [ ] Monitoring set up

---

**Congratulations!** 🎉 Your ETPS application is now live in production!

**Live URL**: https://projects.benjaminblack.consulting
