# ETPS Deployment Quick Start Checklist

Print this page and check off items as you complete them!

---

## 📋 Pre-Deployment Setup

### Accounts (15 minutes)
- [ ] Railway account created → https://railway.app
- [ ] Vercel account created → https://vercel.com  
- [ ] Qdrant Cloud account created → https://cloud.qdrant.io

### API Keys (10 minutes)
- [ ] Anthropic API key obtained → https://console.anthropic.com/settings/keys
- [ ] OpenAI API key obtained → https://platform.openai.com/api-keys
- [ ] Keys saved in password manager or secure note

---

## ☁️ Part 1: Qdrant Cloud (15 minutes)

- [ ] Logged into Qdrant Cloud
- [ ] Created cluster named `etps-production`
- [ ] Selected AWS region: `us-east-1`
- [ ] Selected Free tier (1GB)
- [ ] Waited for cluster to provision
- [ ] Copied Cluster URL: `https://_____________________.aws.cloud.qdrant.io`
- [ ] Created API key named `etps-backend`
- [ ] Copied API key: `qdrant_____________________________`

---

## 🚂 Part 2: Railway Backend (45 minutes)

### Project Setup
- [ ] Logged into Railway with GitHub
- [ ] Created new project from GitHub repo: `blackbenjamin/etps`
- [ ] Set Root Directory to `backend` in Settings

### Database
- [ ] Added PostgreSQL database (New → Database → PostgreSQL)
- [ ] Waited for PostgreSQL to provision
- [ ] Verified DATABASE_URL is auto-set in Variables tab

### Environment Variables
Go to backend service → Variables tab, add these:

- [ ] `ANTHROPIC_API_KEY` = `sk-ant-api03-_______________________`
- [ ] `OPENAI_API_KEY` = `sk-proj-_______________________`
- [ ] `QDRANT_URL` = `https://_____________________.aws.cloud.qdrant.io`
- [ ] `QDRANT_API_KEY` = `qdrant_____________________________`
- [ ] `ENVIRONMENT` = `production`
- [ ] `ALLOWED_ORIGINS` = `https://projects.benjaminblack.consulting`
- [ ] `DATABASE_URL` = (should be auto-set, verify it exists)

### Deployment
- [ ] Waited for automatic deployment (3-5 minutes)
- [ ] Deployment status shows "Success" ✅
- [ ] Generated public domain in Settings → Networking
- [ ] Copied Railway URL: `https://_____________________.up.railway.app`

### Testing
- [ ] Tested health endpoint: `https://your-railway-url/health`
- [ ] Got response: `{"status":"healthy","version":"0.1.0","environment":"production"}`

---

## ▲ Part 3: Vercel Frontend (30 minutes)

### Project Setup
- [ ] Logged into Vercel with GitHub
- [ ] Imported project from GitHub: `blackbenjamin/etps`
- [ ] Set Framework to Next.js (auto-detected)
- [ ] Set Root Directory to `frontend`

### Environment Variables
Before deploying, add these (check all 3 environments):

- [ ] `NEXT_PUBLIC_API_URL` = `https://_____________________.up.railway.app`
- [ ] `NEXT_PUBLIC_USER_NAME` = `Benjamin Black`
- [ ] Checked: ✅ Production ✅ Preview ✅ Development

### Deployment
- [ ] Clicked "Deploy"
- [ ] Waited for build (2-5 minutes)
- [ ] Deployment successful ✅
- [ ] Tested default Vercel URL works

### Custom Domain
- [ ] Went to Settings → Domains
- [ ] Added domain: `projects.benjaminblack.consulting`
- [ ] Went to Cloudflare DNS
- [ ] Added CNAME record:
  - Name: `projects`
  - Target: `cname.vercel-dns.com`
  - Proxy: **Gray cloud** (DNS only)
- [ ] Waited for DNS propagation (1-10 minutes)
- [ ] Domain verified in Vercel ✅
- [ ] SSL certificate auto-provisioned ✅

---

## 💾 Part 4: Database Setup (15 minutes)

Choose ONE option:

### Option A: Fresh Start (Recommended)
- [ ] Will create user profile via API after deployment
- [ ] Will add resume bullets manually or via CSV import

### Option B: Migrate Data
- [ ] Followed `docs/DATABASE_MIGRATION_GUIDE.md`
- [ ] Exported SQLite data
- [ ] Imported to Railway PostgreSQL
- [ ] Verified data integrity

---

## ✅ Part 5: Testing (30 minutes)

### Basic Tests
- [ ] Frontend loads: `https://projects.benjaminblack.consulting`
- [ ] No errors in browser console (F12)
- [ ] Backend health check passes
- [ ] HTTPS works (padlock icon)

### Functional Tests
- [ ] Pasted job description in intake form
- [ ] Submitted form successfully
- [ ] Resume generation completed
- [ ] Downloaded resume DOCX
- [ ] Opened DOCX file successfully
- [ ] Cover letter generation completed
- [ ] Downloaded cover letter DOCX

### Security Tests
- [ ] Checked for CORS errors (should be none)
- [ ] Tested rate limiting (should block after 10 requests)
- [ ] Verified security headers present

---

## 📊 Post-Deployment

### Monitoring Setup
- [ ] Bookmarked Railway dashboard
- [ ] Bookmarked Vercel dashboard
- [ ] Bookmarked Qdrant Cloud dashboard
- [ ] Set up usage alerts in Railway (optional)

### Cost Monitoring
- [ ] Checked Railway usage: _________ / $5
- [ ] Checked Anthropic usage: https://console.anthropic.com/settings/usage
- [ ] Checked OpenAI usage: https://platform.openai.com/usage
- [ ] Checked Qdrant storage: _________ / 1GB

### Documentation
- [ ] Updated portfolio with live demo link
- [ ] Saved all environment variables securely
- [ ] Bookmarked deployment documentation

---

## 🎉 Success!

If all items are checked, your ETPS application is successfully deployed!

**Live URL**: https://projects.benjaminblack.consulting

**Backend API**: https://_____________________.up.railway.app

**API Docs**: https://_____________________.up.railway.app/docs

---

## 🆘 Troubleshooting

If something didn't work:

1. **Check logs**:
   - Railway: Deployments → Latest → View logs
   - Vercel: Deployments → Latest → Function logs

2. **Common issues**:
   - Missing environment variable → Check Variables tab
   - CORS error → Verify ALLOWED_ORIGINS matches Vercel domain
   - Database error → Check DATABASE_URL is set
   - Qdrant error → Verify QDRANT_URL and QDRANT_API_KEY

3. **Documentation**:
   - Full guide: `docs/DEPLOYMENT_WALKTHROUGH_BEGINNERS.md`
   - Env vars: `docs/ENV_VARIABLES_REFERENCE.md`
   - Database: `docs/DATABASE_MIGRATION_GUIDE.md`

---

## 📅 Next Steps

- [ ] Test with real job descriptions
- [ ] Monitor costs for first week
- [ ] Share with friends for feedback
- [ ] Consider Phase 2 features (networking intelligence)

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Notes**:
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
