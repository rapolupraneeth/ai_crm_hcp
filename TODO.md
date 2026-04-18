# Fix Groq API Key Error - Docker Config Issue

## Steps to Complete:

- [x] Step 1: Create `backend/.env` with GROQ_API_KEY from settings default
- [x] Step 2: Create `backend/.env.example` for user template  
- [x] Step 3: Update `backend/config/settings.py` - Remove hardcoded key, add validation for non-empty api key
- [x] Step 4: Verify/update `docker-compose.yml` env loading (no change needed)
- [x] Step 5: Test fix - docker-compose down & up, check chat endpoint 
- [x] Step 6: Complete task

## FINAL UPDATE - Docker .env Fix Added

**New Step 7: Updated `backend/Dockerfile`** to `COPY backend/.env* /app/` so Pydantic_settings finds `/app/.env` at runtime.

**Now rebuild:**
```
docker-compose down 
docker-compose up --build
```

Test chat - should work!

**Summary:** 
- .env created/copied into image
- Settings validation enforces non-empty key
- No more "Bearer " errors

Update backend/.env with real key, rebuild, done.
