# ETPS Production Environment Variables
# Quick reference for Railway and Vercel deployment

## Railway Backend Environment Variables

# Copy these to Railway dashboard → Variables

# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# Qdrant Cloud
QDRANT_URL=https://xxx-xxx.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_cloud_api_key

# Application Environment
ENVIRONMENT=production

# CORS Configuration
ALLOWED_ORIGINS=https://projects.benjaminblack.consulting

# Database (automatically set by Railway PostgreSQL addon)
# DATABASE_URL=postgresql://...  (already set by Railway)

# Optional: Rate Limiting (uses defaults from config.yaml if not set)
# RATE_LIMIT_ENABLED=true
# MAX_REQUESTS_PER_MINUTE_GENERATION=10
# MAX_REQUESTS_PER_MINUTE_READ=60

## Vercel Frontend Environment Variables

# Copy these to Vercel dashboard → Settings → Environment Variables
# Set for: Production, Preview, Development

# Backend API URL (from Railway deployment)
NEXT_PUBLIC_API_URL=https://etps-production.up.railway.app

# User Configuration
NEXT_PUBLIC_USER_NAME=Benjamin Black

## Notes

# 1. Replace placeholder values with actual keys
# 2. Never commit actual API keys to git
# 3. Railway DATABASE_URL is auto-generated when you add PostgreSQL addon
# 4. Update NEXT_PUBLIC_API_URL with your actual Railway backend URL
# 5. ALLOWED_ORIGINS must match your Vercel domain exactly (no trailing slash)
