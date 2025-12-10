# Environment Variables Quick Reference Card

## 📍 Where to Add These

### Railway Backend
Go to: Railway Dashboard → Your Backend Service → **Variables** tab

### Vercel Frontend  
Go to: Vercel Dashboard → Your Project → **Settings** → **Environment Variables**

---

## 🚂 Railway Backend Variables

Copy and paste these variable names exactly. Replace the values with your actual keys.

| Variable Name | Where to Get the Value | Example Value | Required? |
|---------------|------------------------|---------------|-----------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys | `sk-ant-api03-xxxxx...` | ✅ Yes |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys | `sk-proj-xxxxx...` | ✅ Yes |
| `QDRANT_URL` | Qdrant Cloud Dashboard → Your Cluster | `https://abc-xyz.aws.cloud.qdrant.io` | ✅ Yes |
| `QDRANT_API_KEY` | Qdrant Cloud → API Keys tab | `qdrant_xxxxx...` | ✅ Yes |
| `ENVIRONMENT` | Type manually | `production` | ✅ Yes |
| `ALLOWED_ORIGINS` | Type manually | `https://projects.benjaminblack.consulting` | ✅ Yes |
| `DATABASE_URL` | Auto-set by Railway PostgreSQL addon | `postgresql://postgres:...` | ✅ Auto |

### ⚠️ Important Notes for Railway:

1. **DATABASE_URL**: This is automatically created when you add the PostgreSQL addon. Don't manually add it unless it's missing.

2. **ALLOWED_ORIGINS**: 
   - Must match your Vercel domain EXACTLY
   - No trailing slash: ❌ `https://projects.benjaminblack.consulting/`
   - Correct: ✅ `https://projects.benjaminblack.consulting`

3. **QDRANT_URL**: 
   - Include `https://`
   - No trailing slash
   - Get from Qdrant Cloud cluster page

---

## ▲ Vercel Frontend Variables

Copy and paste these variable names exactly.

| Variable Name | Where to Get the Value | Example Value | Required? |
|---------------|------------------------|---------------|-----------|
| `NEXT_PUBLIC_API_URL` | Railway → Your Service → Settings → Networking | `https://etps-production.up.railway.app` | ✅ Yes |
| `NEXT_PUBLIC_USER_NAME` | Type manually | `Benjamin Black` | ✅ Yes |

### ⚠️ Important Notes for Vercel:

1. **NEXT_PUBLIC_API_URL**:
   - Must be your Railway backend URL
   - Include `https://`
   - No `/api` at the end
   - No trailing slash
   - Example: ✅ `https://etps-production.up.railway.app`
   - Wrong: ❌ `https://etps-production.up.railway.app/api/v1`

2. **Environment Selection**:
   - When adding variables in Vercel, check ALL THREE boxes:
     - ✅ Production
     - ✅ Preview  
     - ✅ Development

3. **After Adding Variables**:
   - You must redeploy for changes to take effect
   - Go to Deployments → Latest → Click "⋯" → Redeploy

---

## 🔍 How to Verify Variables Are Set

### Railway:
1. Go to your backend service
2. Click **Variables** tab
3. You should see 7 variables listed (including DATABASE_URL)

### Vercel:
1. Go to **Settings** → **Environment Variables**
2. You should see 2 variables
3. Each should show "Production, Preview, Development"

---

## 🚨 Common Mistakes

### ❌ Mistake 1: Trailing Slashes
```
Wrong: https://projects.benjaminblack.consulting/
Right: https://projects.benjaminblack.consulting
```

### ❌ Mistake 2: Including /api in Frontend URL
```
Wrong: https://etps-production.up.railway.app/api/v1
Right: https://etps-production.up.railway.app
```

### ❌ Mistake 3: Forgetting https://
```
Wrong: etps-production.up.railway.app
Right: https://etps-production.up.railway.app
```

### ❌ Mistake 4: Not Checking All Environments in Vercel
```
Wrong: Only "Production" checked
Right: Production ✅ Preview ✅ Development ✅
```

---

## 📋 Copy-Paste Template

### For Railway (fill in your values):

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
QDRANT_URL=https://YOUR_CLUSTER.aws.cloud.qdrant.io
QDRANT_API_KEY=qdrant_YOUR_KEY_HERE
ENVIRONMENT=production
ALLOWED_ORIGINS=https://projects.benjaminblack.consulting
```

### For Vercel (fill in your Railway URL):

```
NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_URL.up.railway.app
NEXT_PUBLIC_USER_NAME=Benjamin Black
```

---

## 🔐 Security Reminders

1. ✅ **Never commit API keys to Git**
2. ✅ **Never share API keys publicly**
3. ✅ **Rotate keys if accidentally exposed**
4. ✅ **Use environment variables, not hardcoded values**

---

## 🆘 Troubleshooting

### "Environment variable not found"

**Railway:**
- Make sure you clicked **Add** after entering each variable
- Check spelling matches exactly (case-sensitive)
- Redeploy after adding variables

**Vercel:**
- Make sure all three environments are checked
- Redeploy after adding variables
- Variable names must start with `NEXT_PUBLIC_` for frontend access

### "CORS error" in browser console

**Fix:**
1. Check `ALLOWED_ORIGINS` in Railway matches your Vercel domain
2. Check `NEXT_PUBLIC_API_URL` in Vercel matches your Railway URL
3. Make sure no trailing slashes
4. Redeploy both services

### "Failed to connect to Qdrant"

**Fix:**
1. Verify `QDRANT_URL` includes `https://`
2. Verify `QDRANT_API_KEY` is correct
3. Check Qdrant Cloud dashboard - cluster should be running
4. Test connection: Railway → Deployments → View logs

---

## ✅ Final Checklist

Before deploying, verify:

- [ ] All Railway variables are set (7 total including DATABASE_URL)
- [ ] All Vercel variables are set (2 total)
- [ ] No trailing slashes in any URLs
- [ ] `https://` included in all URLs
- [ ] All three environments checked in Vercel
- [ ] API keys are valid and active
- [ ] Qdrant cluster is running
- [ ] PostgreSQL addon is added to Railway

---

**Need the full deployment guide?** See `DEPLOYMENT_WALKTHROUGH_BEGINNERS.md`
