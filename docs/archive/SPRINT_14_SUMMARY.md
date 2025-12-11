# Sprint 14: Cloud Deployment - Implementation Summary

## Overview

Sprint 14 implements cloud deployment for ETPS using:
- **Railway**: Backend (FastAPI + PostgreSQL)
- **Vercel**: Frontend (Next.js)
- **Qdrant Cloud**: Vector store (free tier)

## Files Created

### Backend Configuration
- `backend/Procfile` - Railway process definition
- `backend/railway.toml` - Railway deployment configuration with health checks

### Frontend Configuration
- `frontend/vercel.json` - Vercel deployment configuration with subdomain routing

### Documentation
- `docs/DEPLOYMENT_GUIDE.md` - Complete step-by-step deployment guide
- `docs/PRODUCTION_ENV_TEMPLATE.md` - Environment variables reference

## Code Changes

### Backend Updates

1. **Vector Store Service** (`backend/services/vector_store.py`)
   - Added support for URL-based Qdrant connections (Qdrant Cloud)
   - Maintains backward compatibility with host/port connections (local development)
   - Checks `QDRANT_URL` and `QDRANT_API_KEY` environment variables

2. **Health Check** (`backend/main.py`)
   - Updated `/health/readiness` endpoint to support both connection types
   - Properly handles Qdrant Cloud URL-based connections

3. **Configuration** (`backend/config/config.yaml`)
   - Updated CORS allowed origins to include production domain

### Environment Variables

**Railway Backend:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...  # Auto-set by Railway PostgreSQL addon
QDRANT_URL=https://xxx.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
ENVIRONMENT=production
ALLOWED_ORIGINS=https://projects.benjaminblack.consulting
```

**Vercel Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://etps-production.up.railway.app
NEXT_PUBLIC_USER_NAME=Benjamin Black
```

## Deployment Steps

See `docs/DEPLOYMENT_GUIDE.md` for complete instructions.

### Quick Start

1. **Qdrant Cloud** (15 min)
   - Create free account at https://cloud.qdrant.io/
   - Create cluster, copy URL and API key

2. **Railway Backend** (30-45 min)
   - Deploy from GitHub repo
   - Add PostgreSQL addon
   - Configure environment variables
   - Initialize database schema

3. **Vercel Frontend** (20-30 min)
   - Deploy from GitHub repo
   - Configure environment variables
   - Set up custom domain in Cloudflare

4. **Testing** (15 min)
   - Test health endpoints
   - Verify end-to-end flow
   - Check security headers and rate limiting

## Domain Configuration

**Production URL:** `https://projects.benjaminblack.consulting/etps`

**Cloudflare DNS:**
- Type: CNAME
- Name: `projects`
- Target: `cname.vercel-dns.com`
- Proxy: DNS only (gray cloud)

## Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| Railway (Hobby) | $5 |
| Vercel | Free |
| Qdrant Cloud | Free |
| Anthropic API | $10-20 (usage) |
| OpenAI API | $5 (usage) |
| **Total** | **~$20-30** |

## Security Features

- ✅ HTTPS enforced (automatic)
- ✅ CORS restricted to production domain
- ✅ Rate limiting (10 req/min for generation)
- ✅ Security headers (CSP, X-Frame-Options, etc.)
- ✅ Error sanitization (no stack traces in production)
- ✅ Environment variables secured
- ✅ Database credentials managed by Railway

## Testing Checklist

- [ ] Backend health check: `curl https://your-railway-url/health`
- [ ] Frontend loads at production URL
- [ ] Job intake form works
- [ ] Resume generation completes
- [ ] Cover letter generation completes
- [ ] DOCX downloads work
- [ ] No CORS errors in browser console
- [ ] Rate limiting blocks after 10 requests/minute
- [ ] Security headers present in responses

## Rollback Procedure

**Railway:**
1. Dashboard → Deployments
2. Select previous deployment
3. Click "Redeploy"

**Vercel:**
1. Dashboard → Deployments
2. Select previous deployment
3. Click "⋯" → "Promote to Production"

## Monitoring

**Railway:**
- Dashboard → Metrics (CPU, memory, requests)
- Dashboard → Logs (real-time application logs)

**Vercel:**
- Dashboard → Analytics (page views, performance)
- Dashboard → Deployments → Logs

**Qdrant Cloud:**
- Dashboard → Storage usage (1GB limit)

## Next Steps

After deployment:
1. Test thoroughly with real job descriptions
2. Monitor costs for first week
3. Set up monitoring alerts
4. Update portfolio with live demo link
5. Consider Sprint 13 (additional security hardening)

## Support

- Railway Docs: https://docs.railway.app/
- Vercel Docs: https://vercel.com/docs
- Qdrant Cloud Docs: https://qdrant.tech/documentation/cloud/

---

**Status:** Ready for deployment
**Estimated Total Time:** 2-3 hours
**Last Updated:** December 2025
