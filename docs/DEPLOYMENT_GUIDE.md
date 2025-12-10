# ETPS Deployment Guide
**Sprint 14: Cloud Deployment to Railway + Vercel**

This guide walks through deploying ETPS to production:
- **Backend**: Railway (FastAPI + PostgreSQL)
- **Frontend**: Vercel (Next.js)
- **Vector Store**: Qdrant Cloud (free tier)
- **Domain**: https://projects.benjaminblack.consulting/etps

---

## Prerequisites

- [x] Railway account (Hobby tier: $5/month)
- [x] Vercel account (Free tier)
- [x] Domain: `benjaminblack.consulting` (hosted on Cloudflare)
- [ ] Qdrant Cloud account (free tier)
- [ ] API Keys: Anthropic, OpenAI

---

## Part 1: Qdrant Cloud Setup (15 minutes)

### 1.1 Create Qdrant Cloud Account

1. Go to https://cloud.qdrant.io/
2. Sign up for free account
3. Create a new cluster:
   - **Name**: `etps-production`
   - **Region**: Choose closest to your Railway region (e.g., `aws-us-east-1`)
   - **Tier**: Free (1GB)

### 1.2 Get Connection Details

1. After cluster creation, click on the cluster
2. Copy the **Cluster URL** (e.g., `https://xxx-xxx.aws.cloud.qdrant.io`)
3. Go to **API Keys** → **Create API Key**
4. Copy the API key (you'll need this for Railway)

### 1.3 Test Connection (Optional)

```bash
# From your local machine
export QDRANT_URL="https://xxx-xxx.aws.cloud.qdrant.io"
export QDRANT_API_KEY="your_api_key_here"

# Test with Python
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='$QDRANT_URL', api_key='$QDRANT_API_KEY')
print('Collections:', client.get_collections())
"
```

---

## Part 2: Railway Backend Deployment (30-45 minutes)

### 2.1 Create Railway Project

1. Go to https://railway.app/
2. Click **New Project** → **Deploy from GitHub repo**
3. Connect your GitHub account if not already connected
4. Select repository: `blackbenjamin/etps`
5. Railway will auto-detect the backend (Python)

### 2.2 Configure Build Settings

1. In Railway dashboard, click on your service
2. Go to **Settings** → **Build**
3. Set **Root Directory**: `backend`
4. Railway will automatically use `Procfile` and `railway.toml`

### 2.3 Add PostgreSQL Database

1. In your Railway project, click **New** → **Database** → **Add PostgreSQL**
2. Railway will automatically create a `DATABASE_URL` environment variable
3. The database will be linked to your backend service

### 2.4 Configure Environment Variables

1. Go to your backend service → **Variables**
2. Add the following variables:

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# Qdrant Cloud (from Part 1)
QDRANT_URL=https://xxx-xxx.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_cloud_api_key

# Application Environment
ENVIRONMENT=production

# CORS Configuration
ALLOWED_ORIGINS=https://projects.benjaminblack.consulting

# Database (automatically set by Railway PostgreSQL addon)
# DATABASE_URL=postgresql://...  (already set)
```

### 2.5 Deploy Backend

1. Railway will automatically deploy after you add environment variables
2. Wait for deployment to complete (2-5 minutes)
3. Copy your backend URL (e.g., `https://etps-production.up.railway.app`)

### 2.6 Test Backend Deployment

```bash
# Test health endpoint
curl https://your-railway-url.up.railway.app/health

# Expected response:
# {"status":"healthy","version":"0.1.0","environment":"production"}
```

### 2.7 Initialize Database Schema

Railway PostgreSQL starts empty. You need to initialize the schema:

**Option A: Run migration script (recommended)**
```bash
# From your local machine, connect to Railway PostgreSQL
# Get DATABASE_URL from Railway dashboard

export DATABASE_URL="postgresql://postgres:..."  # From Railway

# Run schema migration
cd backend
python -c "
from db.database import Base, engine
Base.metadata.create_all(bind=engine)
print('Schema created successfully')
"
```

**Option B: Use Railway CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link to project
railway login
railway link

# Run migration
railway run python -c "from db.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 2.8 Seed Initial Data (Optional)

If you want to migrate your local data:

```bash
# Export from local SQLite
cd backend
sqlite3 etps.db .dump > data_export.sql

# Import to PostgreSQL (requires manual conversion)
# This is complex - recommend starting fresh and re-adding your profile
```

---

## Part 3: Vercel Frontend Deployment (20-30 minutes)

### 3.1 Create Vercel Project

1. Go to https://vercel.com/
2. Click **Add New** → **Project**
3. Import your GitHub repository: `blackbenjamin/etps`
4. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 3.2 Configure Environment Variables

1. In Vercel project settings → **Environment Variables**
2. Add the following (for all environments: Production, Preview, Development):

```bash
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
NEXT_PUBLIC_USER_NAME=Benjamin Black
```

Replace `your-railway-url.up.railway.app` with your actual Railway backend URL from Part 2.5.

### 3.3 Deploy Frontend

1. Click **Deploy**
2. Vercel will build and deploy (2-5 minutes)
3. You'll get a default URL like `etps-frontend.vercel.app`

### 3.4 Configure Custom Domain

#### 3.4.1 Add Domain in Vercel

1. Go to your Vercel project → **Settings** → **Domains**
2. Click **Add Domain**
3. Enter: `projects.benjaminblack.consulting`
4. Vercel will show you DNS records to add

#### 3.4.2 Configure Cloudflare DNS

1. Go to Cloudflare dashboard → `benjaminblack.consulting` → **DNS**
2. Add a **CNAME** record:
   - **Type**: CNAME
   - **Name**: `projects`
   - **Target**: `cname.vercel-dns.com`
   - **Proxy status**: DNS only (gray cloud) - **Important!**
   - **TTL**: Auto

3. Wait for DNS propagation (1-10 minutes)

#### 3.4.3 Configure Subdomain Path

Since you want `projects.benjaminblack.consulting/etps`, you have two options:

**Option A: Dedicated subdomain (recommended)**
- Use `etps.benjaminblack.consulting` instead
- Simpler configuration
- Add CNAME: `etps` → `cname.vercel-dns.com`

**Option B: Path-based routing**
- Keep `projects.benjaminblack.consulting/etps`
- Requires additional Vercel configuration
- The `vercel.json` already includes path rewrites for `/etps`
- You'll need to configure this in Vercel's project settings

For now, I recommend **Option A** (dedicated subdomain) for simplicity.

### 3.5 Test Frontend Deployment

1. Visit `https://projects.benjaminblack.consulting` (or your chosen domain)
2. You should see the ETPS interface
3. Test the job intake form
4. Verify API calls work (check browser console for errors)

---

## Part 4: End-to-End Testing (15 minutes)

### 4.1 Test Complete Flow

1. **Navigate to frontend**: https://projects.benjaminblack.consulting/etps
2. **Paste a job description** in the intake form
3. **Submit** and verify:
   - Job parsing works
   - Resume generation completes
   - Cover letter generation completes
   - DOCX downloads work
   - No CORS errors in browser console

### 4.2 Verify Security Headers

```bash
# Check security headers
curl -I https://your-railway-url.up.railway.app/health

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Strict-Transport-Security: max-age=31536000
```

### 4.3 Test Rate Limiting

```bash
# Test rate limiting (should block after 10 requests/minute)
for i in {1..15}; do
  curl https://your-railway-url.up.railway.app/api/v1/resume/generate \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"job_id": 1}'
  echo "Request $i"
done

# Should see 429 Too Many Requests after request 10
```

### 4.4 Monitor Logs

**Railway:**
- Go to your service → **Deployments** → Click latest deployment
- View logs for errors

**Vercel:**
- Go to your project → **Deployments** → Click latest deployment
- View function logs

---

## Part 5: Post-Deployment Configuration

### 5.1 Update GitHub Repository

Add deployment status badges to README:

```markdown
[![Railway Deploy](https://img.shields.io/badge/Railway-Deployed-success)](https://your-railway-url.up.railway.app)
[![Vercel Deploy](https://img.shields.io/badge/Vercel-Deployed-success)](https://projects.benjaminblack.consulting/etps)
```

### 5.2 Set Up Monitoring (Optional)

**Railway:**
- Enable **Metrics** in Railway dashboard
- Monitor CPU, memory, and request rates

**Vercel:**
- Enable **Analytics** in Vercel dashboard
- Monitor page views and performance

**Qdrant Cloud:**
- Monitor storage usage in Qdrant dashboard
- Free tier: 1GB limit

### 5.3 Configure Alerts (Optional)

**Railway:**
- Set up **Webhooks** for deployment failures
- Configure **Usage Alerts** if approaching limits

**Vercel:**
- Set up **Deployment Notifications** in project settings

---

## Troubleshooting

### Backend Issues

**Problem: Health check fails**
```bash
# Check Railway logs
railway logs

# Common issues:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Qdrant connection failed
```

**Problem: Database connection error**
```bash
# Verify DATABASE_URL is set
railway variables

# Test connection
railway run python -c "from db.database import engine; print(engine.url)"
```

**Problem: CORS errors**
```bash
# Verify ALLOWED_ORIGINS matches your frontend domain
# Check Railway environment variables
# Ensure no trailing slashes in ALLOWED_ORIGINS
```

### Frontend Issues

**Problem: API calls fail (CORS)**
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Check Railway backend CORS configuration
- Ensure backend URL doesn't have trailing slash

**Problem: Environment variables not updating**
- Redeploy after changing environment variables
- Clear Vercel cache: Settings → General → Clear Cache

**Problem: Domain not resolving**
- Check Cloudflare DNS propagation: https://dnschecker.org/
- Ensure CNAME proxy is **disabled** (gray cloud)
- Wait up to 24 hours for full propagation

### Qdrant Issues

**Problem: Vector search not working**
- Verify `QDRANT_URL` and `QDRANT_API_KEY` are set
- Check Qdrant Cloud dashboard for cluster status
- Test connection from Railway:
  ```bash
  railway run python -c "from qdrant_client import QdrantClient; client = QdrantClient(url='...', api_key='...'); print(client.get_collections())"
  ```

---

## Cost Monitoring

### Expected Monthly Costs

| Service | Cost | Notes |
|---------|------|-------|
| Railway | $5 | Hobby tier includes $5 credit |
| Vercel | $0 | Free tier (hobby) |
| Qdrant Cloud | $0 | Free tier (1GB) |
| Anthropic API | $10-20 | Usage-based (~100 resumes) |
| OpenAI API | $5 | Usage-based (embeddings) |
| **Total** | **~$20-30** | Mostly API usage |

### Monitor Usage

**Railway:**
- Dashboard → Usage → View current month spend
- Set up alerts if approaching $5 credit limit

**API Usage:**
- Anthropic: https://console.anthropic.com/settings/usage
- OpenAI: https://platform.openai.com/usage

**Qdrant:**
- Dashboard → Cluster → Storage usage
- Free tier: 1GB limit (plenty for this project)

---

## Rollback Procedure

### Railway Rollback

1. Go to Railway dashboard → Deployments
2. Click on previous successful deployment
3. Click **Redeploy**

### Vercel Rollback

1. Go to Vercel dashboard → Deployments
2. Find previous successful deployment
3. Click **⋯** → **Promote to Production**

---

## Security Checklist

- [x] HTTPS enabled (automatic on Railway/Vercel)
- [x] CORS restricted to production domain
- [x] Rate limiting enabled (10 req/min for generation)
- [x] Security headers configured
- [x] Error sanitization enabled (no stack traces)
- [x] Environment variables secured (not in code)
- [x] Database credentials managed by Railway
- [x] API keys stored in environment variables

---

## Next Steps

After successful deployment:

1. **Test thoroughly** with real job descriptions
2. **Monitor costs** for first week
3. **Set up monitoring** and alerts
4. **Update portfolio** with live demo link
5. **Consider Sprint 13** (additional security hardening) if needed

---

## Support Resources

- **Railway Docs**: https://docs.railway.app/
- **Vercel Docs**: https://vercel.com/docs
- **Qdrant Cloud Docs**: https://qdrant.tech/documentation/cloud/
- **Cloudflare DNS**: https://developers.cloudflare.com/dns/

---

*Last Updated: December 2025*
*Sprint 14 - Cloud Deployment*
