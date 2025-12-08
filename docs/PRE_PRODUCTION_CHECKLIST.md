# ETPS Pre-Production Checklist

Before exposing ETPS as a portfolio project, complete these items:

## Security & Privacy

- [ ] **Remove debug console.logs** from frontend components
  - `src/components/job-intake/JobIntakeForm.tsx` (lines 61, 68)
  - Search for other `console.log` statements: `grep -r "console.log" src/`
  
- [ ] **Verify .env.local is gitignored** (contains PII)
  - Already configured in `.gitignore`
  
- [ ] **Review API keys and secrets**
  - Ensure no API keys committed to git history
  - Use `git log -p | grep -i "api_key\|secret\|password"` to check

- [ ] **Update backend CORS settings** for production domain
  - `backend/main.py` - add production frontend URL

## Code Quality

- [ ] **Remove unused imports and variables**
  - Run linter: `npm run lint`
  
- [ ] **Run backend tests**
  - `cd backend && python -m pytest -v`
  
- [ ] **Verify type safety**
  - `npm run build` (catches TypeScript errors)

## Documentation

- [ ] **Update README.md** with:
  - Project overview and screenshots
  - Quick start guide
  - Architecture overview
  - Tech stack
  
- [ ] **Create .env.example files** for both frontend and backend
  - Frontend: `/frontend/.env.example` (created)
  - Backend: `/backend/.env.example` (if needed)

- [ ] **Add LICENSE file** (if open-sourcing)

## Deployment

- [ ] **Database migrations**
  - Ensure schema is up to date
  - Document migration steps

- [ ] **Environment variables** for production:
  ```
  # Frontend
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
  NEXT_PUBLIC_USER_NAME=...
  NEXT_PUBLIC_USER_EMAIL=...
  etc.
  
  # Backend
  ANTHROPIC_API_KEY=...
  DATABASE_URL=...
  ```

- [ ] **HTTPS configuration**
  - Backend must serve over HTTPS in production
  - Update CORS to use HTTPS URLs

## Testing

- [ ] **End-to-end test flow:**
  1. Parse job description
  2. View skill gap analysis
  3. Generate resume
  4. Generate cover letter
  5. Download DOCX files
  
- [ ] **Test with real LLM** (not mock)
  - Enable Claude/GPT-4 integration
  - Verify quality of generated content

## Performance

- [ ] **Review bundle size**
  - Current: ~119 kB First Load JS (acceptable)
  
- [ ] **Add loading states** where missing

- [ ] **Consider caching strategies** for API responses

## Final Review

- [ ] **Security review** with reviewer agent
- [ ] **UI/UX review** - consistent styling, responsive design
- [ ] **Error handling** - all errors show user-friendly messages
- [ ] **Analytics** (optional) - add tracking for portfolio demo

---

## Notes

Items marked with priority indicators:
- **CRITICAL**: Must fix before any public exposure
- **HIGH**: Should fix for professional presentation  
- **MEDIUM**: Nice to have for polish
- **LOW**: Future enhancement

---

*Last updated: December 2025*
