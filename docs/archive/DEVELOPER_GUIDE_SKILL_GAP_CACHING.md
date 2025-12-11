# Developer Guide: Skill Gap Analysis Caching

## Quick Start

### Using Cached Skill Gap Analysis

```python
from services.skill_gap import analyze_skill_gap
from db.database import SessionLocal

db = SessionLocal()

# Automatically uses cache if available (default)
skill_gap = await analyze_skill_gap(
    job_profile_id=123,
    user_id=456,
    db=db
)

# Force fresh analysis (bypass cache)
skill_gap = await analyze_skill_gap(
    job_profile_id=123,
    user_id=456,
    db=db,
    use_cache=False  # Ignore cache, recompute from scratch
)
```

### Manual Cache Operations

```python
from services.skill_gap import (
    save_skill_gap_analysis,
    get_cached_skill_gap_analysis
)

# Retrieve cached analysis
cached = get_cached_skill_gap_analysis(
    db=db,
    job_profile_id=123,
    user_id=456,
    max_age_hours=24  # Default: 24 hours
)

if cached:
    print(f"Cache hit! Score: {cached.skill_match_score}")
else:
    print("Cache miss - need to run analysis")

# Save analysis manually (usually automatic)
save_skill_gap_analysis(
    db=db,
    job_profile_id=123,
    user_id=456,
    analysis=skill_gap_result
)
```

## Cache Architecture

### Storage Location
- **Table**: `job_profiles`
- **Column**: `skill_gap_analysis` (JSON)
- **Structure**:
```json
{
  "123": {  // user_id (string key)
    "skill_match_score": 75.5,
    "matched_skills": [...],
    "skill_gaps": [...],
    "weak_signals": [...],
    "user_id": 123,
    "cached_at": "2025-12-05T10:30:00",
    ...
  },
  "456": {  // another user's analysis
    ...
  }
}
```

### Cache Expiration
- **Default**: 24 hours
- **Configurable**: Pass `max_age_hours` to `get_cached_skill_gap_analysis()`
- **Time-based only**: No automatic invalidation on job profile updates

### Cache Key
- **Primary**: `job_profile_id` + `user_id`
- **Why**: Each user has different skills, so same job = different analysis per user

## Performance Characteristics

### Cache Hit (Fast Path)
```
1. Query job_profile by ID: ~5ms
2. JSON deserialize: ~1-2ms
3. Timestamp check: ~1ms
4. Reconstruct SkillGapResponse: ~2-5ms
Total: ~10-15ms (100-500x faster than full analysis)
```

### Cache Miss (Slow Path)
```
1. Build user skill profile: ~50-100ms
2. Compute matched skills (with embeddings): ~500-1000ms
3. LLM-based importance classification: ~500-1500ms
4. Generate positioning strategies: ~300-800ms
5. Save to database: ~10-20ms
Total: ~2-5 seconds
```

### Expected Hit Rates
- **Single user, multiple iterations**: 80-90%
- **Job reused across multiple users**: 60-70%
- **System-wide average**: 65-75%

## When Cache is Bypassed

### Automatic Bypass
1. `use_cache=False` parameter
2. Cache older than `max_age_hours`
3. Cache corrupt/invalid (logs warning)
4. No cached entry exists

### Manual Bypass Scenarios
```python
# User updated their resume significantly
skill_gap = await analyze_skill_gap(..., use_cache=False)

# Job profile was just updated
skill_gap = await analyze_skill_gap(..., use_cache=False)

# Debugging/testing
skill_gap = await analyze_skill_gap(..., use_cache=False)
```

## Monitoring & Debugging

### Logging
All cache operations are logged at INFO level:

```python
import logging
logger = logging.getLogger('services.skill_gap')
logger.setLevel(logging.INFO)
```

**Cache hit**:
```
INFO: Retrieved cached skill gap analysis (age: 2.3h)
INFO: Using cached skill gap analysis for job_profile_id=123, user_id=456
```

**Cache miss**:
```
INFO: Cached analysis expired (age: 25.1h > 24h)
INFO: Saved skill gap analysis for job_profile_id=123, user_id=456
```

**Cache errors**:
```
WARNING: Cached analysis for job_profile_id=123, user_id=456 missing timestamp
WARNING: Failed to parse cached analysis: Invalid JSON
WARNING: Failed to cache skill gap analysis: Database error
```

### Metrics to Track

```python
# In your monitoring system
cache_hit_rate = cache_hits / (cache_hits + cache_misses)
avg_cached_response_time = mean([t for t in cached_requests])
avg_uncached_response_time = mean([t for t in uncached_requests])
cache_error_rate = cache_errors / total_requests
```

### Database Queries

**Check cache size**:
```sql
SELECT
    id,
    job_title,
    jsonb_object_keys(skill_gap_analysis) as user_id,
    skill_gap_analysis -> jsonb_object_keys(skill_gap_analysis) ->> 'cached_at' as cached_at
FROM job_profiles
WHERE skill_gap_analysis IS NOT NULL;
```

**Clear expired caches** (manual cleanup):
```sql
-- Not automatic - for maintenance if needed
UPDATE job_profiles
SET skill_gap_analysis = NULL
WHERE skill_gap_analysis IS NOT NULL
  AND (skill_gap_analysis -> 'cached_at')::timestamp < NOW() - INTERVAL '7 days';
```

## Best Practices

### DO
- ✓ Use default caching for normal resume tailoring
- ✓ Bypass cache when user makes major resume changes
- ✓ Monitor cache hit rates in production
- ✓ Log cache operations for debugging
- ✓ Handle cache errors gracefully (analysis still works)

### DON'T
- ✗ Don't bypass cache unnecessarily (wastes compute)
- ✗ Don't rely on cache for real-time job profile updates
- ✗ Don't manually edit `skill_gap_analysis` JSON (use functions)
- ✗ Don't set `max_age_hours` too high (stale data)
- ✗ Don't panic if cache save fails (analysis still returns)

## Troubleshooting

### Problem: Cache never hits
**Symptoms**: Every request is slow (~2-5 seconds)
**Diagnosis**:
```python
cached = get_cached_skill_gap_analysis(db, job_profile_id, user_id)
print(f"Cached result: {cached}")
```
**Solutions**:
1. Check database: `SELECT skill_gap_analysis FROM job_profiles WHERE id = ?`
2. Verify `cached_at` timestamp format
3. Check logs for save errors

### Problem: Stale cache results
**Symptoms**: Old skill gaps appearing after user resume update
**Solution**:
```python
# Force fresh analysis after resume update
skill_gap = await analyze_skill_gap(..., use_cache=False)
```

### Problem: Cache save failures
**Symptoms**: `WARNING: Failed to cache skill gap analysis`
**Diagnosis**:
1. Check database connection
2. Verify `job_profiles.skill_gap_analysis` column exists
3. Check JSON serialization of SkillGapResponse
**Solution**: Analysis still works, caching is non-critical

### Problem: Memory/storage concerns
**Symptoms**: Large database size growth
**Analysis**:
- Each cached analysis: ~5-20 KB JSON
- 1000 job profiles × 10 users = 10,000 entries = ~50-200 MB
- Generally negligible for modern databases
**Solution**: Implement periodic cleanup if needed (see SQL above)

## Migration Guide

### From No Caching to Caching

**No code changes required!** Caching is automatic:

```python
# Old code (still works)
skill_gap = await analyze_skill_gap(job_profile_id, user_id, db)

# New behavior:
# - First call: Slow, saves to cache
# - Subsequent calls: Fast, uses cache
# - No breaking changes
```

### Gradual Rollout

1. **Phase 1**: Deploy with caching enabled (default)
   - Monitor cache hit rates
   - Watch for errors in logs

2. **Phase 2**: Tune cache expiration if needed
   ```python
   # Adjust based on usage patterns
   cached = get_cached_skill_gap_analysis(db, jp_id, u_id, max_age_hours=48)
   ```

3. **Phase 3**: Add metrics/alerting
   - Cache hit rate < 50% → investigate
   - Cache errors > 1% → investigate

## Advanced Usage

### Custom Cache Expiration
```python
# Short cache for active job search (1 hour)
cached = get_cached_skill_gap_analysis(
    db=db,
    job_profile_id=job_id,
    user_id=user_id,
    max_age_hours=1
)

# Long cache for exploration (7 days)
cached = get_cached_skill_gap_analysis(
    db=db,
    job_profile_id=job_id,
    user_id=user_id,
    max_age_hours=168  # 7 * 24
)
```

### Batch Pre-warming
```python
# Pre-compute analyses for all jobs
for job_profile in job_profiles:
    skill_gap = await analyze_skill_gap(
        job_profile_id=job_profile.id,
        user_id=current_user.id,
        db=db,
        use_cache=False  # Force computation
    )
    # Subsequent tailoring will be fast
```

### Cache Invalidation Hook
```python
# After job profile update
def on_job_profile_update(job_profile_id: int, db: Session):
    # Clear cached analyses for this job
    job_profile = db.query(JobProfile).filter_by(id=job_profile_id).first()
    if job_profile:
        job_profile.skill_gap_analysis = None
        db.commit()
```

## API Impact

### Resume Tailoring API
```python
POST /api/v1/resume/tailor
{
  "job_profile_id": 123,
  "user_id": 456,
  ...
}

# Response now includes skill_gap_summary
{
  "skill_gap_summary": {
    "skill_match_score": 75.5,
    "recommendation": "moderate_match",
    "confidence": 0.8,
    "matched_skills_count": 10,
    "skill_gaps_count": 5,
    "critical_gaps_count": 1,
    "key_positioning_angles": [...],
    "top_matched_skills": [...],
    "critical_gaps": [...]
  },
  ...
}
```

### Direct Skill Gap API (if exposed)
```python
GET /api/v1/skill-gap/{job_profile_id}/{user_id}?use_cache=true

# Query params:
# - use_cache: bool (default true)
# - max_age_hours: int (default 24)
```

## Future Enhancements

### Planned
1. Redis caching layer (distributed systems)
2. Cache warming on job profile creation
3. Automatic invalidation on profile updates
4. Cache analytics dashboard

### Under Consideration
1. ML-based cache expiration (adaptive)
2. Predictive pre-caching
3. Cross-user skill gap aggregation
4. Cache compression for large analyses

---

## Summary

**Key Points**:
- ✅ Automatic caching - no code changes needed
- ✅ 100-500x faster for cached requests
- ✅ Non-breaking - gracefully handles errors
- ✅ Configurable expiration (default 24h)
- ✅ Per-user caching (accurate for each user)

**When to Bypass Cache**:
- User updated resume significantly
- Job profile just changed
- Debugging/testing
- Need real-time analysis

**Monitoring**:
- Log cache hit rates
- Track response times
- Alert on high error rates
- Monitor database size (if applicable)

For questions or issues, check logs first, then consult this guide.
