# Week 4: Deploy Evaluation Dashboard to Render

Yes! The Streamlit dashboard deploys beautifully to Render. Here's how.

## Quick Start (5 minutes)

### Step 1: Commit the Render Config

```bash
git add render.yaml .streamlit/config.toml
git commit -m "Add Render deployment configuration for Week 4 dashboard"
git push origin main
```

### Step 2: Deploy on Render Dashboard

1. Go to: https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the branch with Week 4 code
5. Fill in:
   - **Name:** `ai-engineering-week4-eval`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `streamlit run streamlit_week4_eval.py --server.port=$PORT --server.address=0.0.0.0`
   - **Plan:** Free (or Standard for production)

### Step 3: Set Environment Variables

In Render dashboard, go to **Environment** and add:

```
OPENAI_API_KEY = [your key]
GOOGLE_API_KEY = [your key]
PINECONE_API_KEY = [your key]
PINECONE_INDEX_NAME = ai-engineer-rag
RAG_API_URL = https://ai-engineering-wlqp.onrender.com
```

### Step 4: Deploy

Click **"Deploy"** and wait ~2-3 minutes

Your dashboard will be live at: `https://ai-engineering-week4-eval.onrender.com`

---

## Architecture Overview

You'll have **3 services on Render:**

```
1. Week 1-3 API (FastAPI)
   └─ https://ai-engineering-wlqp.onrender.com
      └─ /ask           (QA)
      └─ /agent         (Agent)
      └─ /debug/retrieve (RAG)

2. Week 3 Streamlit UI
   └─ https://ai-engineering-streamlit.onrender.com
      └─ Calls /agent endpoint

3. Week 4 Evaluation Dashboard (NEW)
   └─ https://ai-engineering-week4-eval.onrender.com
      └─ Calls /debug/retrieve for sample traces
      └─ Reads ./traces/ directory
```

---

## What Gets Deployed

**Files that go to Render:**

```
week4_trace_capture.py        ✓ Deployed
week4_checks.py               ✓ Deployed
streamlit_week4_eval.py       ✓ Deployed (main entry point)
agent_research_improved.py    ✓ Deployed (optional, not used)
week4_sample_traces.py        ✓ Deployed (optional, not used)
traces/                       ✓ Deployed (20 JSON files included)
requirements.txt              ✓ Deployed (dependencies)
.streamlit/config.toml        ✓ Deployed (Streamlit config)
```

**Your traces directory will be part of the deployment**, so all 20 sample traces will be available in production.

---

## Configuration Files Explained

### render.yaml
Render's deployment configuration:
- Specifies Python environment
- Sets build and start commands
- Configures environment variables
- Enables auto-deploy on git push

### .streamlit/config.toml
Streamlit-specific settings:
- Theme colors
- Server configuration
- Security settings
- Production optimizations

---

## Features on Deployed Dashboard

All 4 tabs work perfectly on Render:

### 📈 Metrics Tab
- Before/After comparison
- Live from Render-hosted traces
- No API calls needed

### 📝 Annotation Tab
- Read-only in production (traces loaded at deploy time)
- Shows all 20 annotated traces
- Can't modify (annotations are static)

### 🔍 Trace Detail Tab
- View any of the 20 traces
- Run automated checks
- Show detailed results

### 📋 Taxonomy Tab
- Failure categories
- Frequency analysis
- Priority matrix

**Note:** The annotation feature is read-only in production because we're serving static trace files. If you want live annotation, you'd need a database (see Advanced section below).

---

## Deployment Process Visualization

```
┌─ Your Local Machine ──────────────┐
│                                   │
│ Edit code                         │
│ Test locally                      │
│ Commit to git                     │
│ Push to GitHub                    │
│                                   │
└────────────┬──────────────────────┘
             │
             ▼
┌─ GitHub ──────────────────────────┐
│                                   │
│ Receives push                     │
│ Triggers webhook                  │
│                                   │
└────────────┬──────────────────────┘
             │
             ▼
┌─ Render ──────────────────────────┐
│                                   │
│ 1. Clone repository               │
│ 2. Install dependencies           │
│    pip install -r requirements.txt│
│ 3. Start Streamlit server         │
│    streamlit run streamlit_...    │
│ 4. Server ready on port 10000     │
│                                   │
└────────────┬──────────────────────┘
             │
             ▼
┌─ Live Dashboard ──────────────────┐
│                                   │
│ https://...week4-eval.onrender.com│
│ Public URL, anyone can access     │
│                                   │
└───────────────────────────────────┘
```

---

## Testing Before Deploying

### 1. Test Locally First

```bash
cd C:\Users\madhy\AI-Bootcamp\ai-engineering\ai-engineering-bootcamp-v2\week-1
.\venv\Scripts\Activate.ps1
streamlit run streamlit_week4_eval.py
```

Visit http://localhost:8501 and verify all tabs work.

### 2. Test Production Settings Locally

```bash
streamlit run streamlit_week4_eval.py \
  --server.port=10000 \
  --server.address=0.0.0.0 \
  --client.showErrorDetails=false
```

This simulates Render's environment.

### 3. Push to GitHub

```bash
git add render.yaml .streamlit/config.toml
git commit -m "Add Render deployment config for Week 4 dashboard"
git push origin main
```

### 4. Deploy on Render

Follow Quick Start steps above.

---

## Environment Variables on Render

### What Each Variable Does

| Variable | Purpose | Example |
|----------|---------|---------|
| `OPENAI_API_KEY` | Used by improved agent (optional) | `sk-...` |
| `GOOGLE_API_KEY` | Used by improved agent (optional) | `AQ.Ab8RN...` |
| `PINECONE_API_KEY` | For RAG calls | `(your key)` |
| `PINECONE_INDEX_NAME` | Vector DB index | `ai-engineer-rag` |
| `RAG_API_URL` | Calls your Week 1-3 API | `https://ai-engineering-wlqp.onrender.com` |

### Why RAG_API_URL Matters

The dashboard doesn't need to call your API for traces (they're in `./traces/`), but it's set in case you want to:
- Generate new traces in production
- Call `/debug/retrieve` for real-time queries
- Integrate with the live agent

---

## Troubleshooting

### Dashboard shows "No traces found"

**Cause:** Traces directory wasn't included in deployment  
**Fix:** Make sure `traces/` is committed to git and pushed

```bash
git add traces/
git commit -m "Add trace data"
git push origin main
```

Then redeploy on Render.

### Dashboard loads slowly

**Cause:** Render free plan has limited resources  
**Fix:** Upgrade to Standard plan ($7/month) for better performance

### Environment variables not showing up

**Cause:** Render hasn't redeployed after you added vars  
**Fix:** In Render dashboard, click **"Manual Deploy"** → **"Deploy latest commit"**

### Dashboard shows error about missing modules

**Cause:** Missing dependencies in requirements.txt  
**Fix:** Add to requirements.txt and push:

```
streamlit>=1.28.0
pandas>=2.0.0
```

Then redeploy.

---

## Advanced: Adding Live Annotation (Optional)

To make annotations persistent in production, you'd need:

1. **PostgreSQL database** on Render ($15/month)
2. **Update TraceStore** to use SQLAlchemy instead of JSON files
3. **REST API** to handle annotation updates

Example modification:

```python
# Instead of file-based:
# trace.failure_category = user_selection
# store.save_trace(trace)  # Saves to JSON

# Use database:
# db.session.query(Trace).filter_by(id=trace_id).update({
#     'failure_category': user_selection
# })
# db.session.commit()  # Saves to Postgres
```

For now, the static traces approach is simpler and works great for Week 4 submission.

---

## URLs After Deployment

| Service | URL | Purpose |
|---------|-----|---------|
| **Week 1-3 API** | https://ai-engineering-wlqp.onrender.com | FastAPI backend |
| **Week 3 Streamlit** | https://ai-engineering-streamlit.onrender.com | Agent UI |
| **Week 4 Dashboard** | https://ai-engineering-week4-eval.onrender.com | Evaluation UI (NEW!) |

---

## Monitoring on Render

### Check Deployment Status

In Render dashboard:
1. Go to **Services** → **ai-engineering-week4-eval**
2. View **Events** tab for deployment logs
3. Check **Health** for uptime status

### View Live Logs

```
Click "Logs" tab in service dashboard
Watch real-time output as users visit
```

### Common Render Issues

- **Out of memory:** Free tier has 512MB RAM limit
- **Timeout on first visit:** Streamlit takes ~30s to start on free tier
- **Frozen after 15 min inactivity:** Free tier spins down (Ctrl+F5 to reload)

---

## Cost Breakdown

| Service | Type | Cost | Notes |
|---------|------|------|-------|
| Week 1-3 API | Standard | $7/month | Always running |
| Week 3 Streamlit | Standard | $7/month | Always running |
| Week 4 Dashboard | Free | $0 | Spins down after 15 min |
| | OR Standard | $7/month | Always running |
| | OR Pro | $12/month | Better performance |

**Total:** $14-26/month depending on plan

---

## Next Steps

1. ✅ **Commit config files** to git
2. ✅ **Push to GitHub**
3. ✅ **Create new service** on Render
4. ✅ **Set environment variables**
5. ✅ **Deploy**
6. ✅ **Test dashboard**
7. ✅ **Share URL** with evaluators

---

## Deployment Checklist

- [ ] `render.yaml` committed to git
- [ ] `.streamlit/config.toml` committed to git
- [ ] `traces/` directory committed to git (with 20 JSON files)
- [ ] All Week 4 code committed and pushed
- [ ] Render service created
- [ ] Environment variables set in Render dashboard
- [ ] Initial deployment complete
- [ ] Dashboard loads at public URL
- [ ] All 4 tabs work (Metrics, Annotation, Detail, Taxonomy)
- [ ] Traces loaded correctly (20 visible)

---

## Summary

✅ **Streamlit deploys easily to Render**  
✅ **Takes 5 minutes to set up**  
✅ **Free tier available** (with spindown)  
✅ **All 4 dashboard tabs work perfectly**  
✅ **Traces included in deployment**  
✅ **Can share public URL with anyone**  

Your Week 4 evaluation dashboard will be live and ready to share!

---

## Questions?

If deployment fails:
1. Check Render **Events** tab for error logs
2. Verify environment variables are set
3. Ensure `render.yaml` is in correct location
4. Check that `traces/` has 20 JSON files
5. Try manual redeploy in Render dashboard

Good luck! 🚀
