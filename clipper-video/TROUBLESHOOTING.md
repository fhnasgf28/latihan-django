# 🔧 Troubleshooting Guide

## Backend Issues

### 1. CORS Error: "Access to XMLHttpRequest blocked by CORS"

**Error Message:**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/clips/videos/' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solution:**
```python
# backend/clipper/settings.py

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
```

Restart Django server setelah perubahan.

---

### 2. ModuleNotFoundError: No module named 'rest_framework'

**Solution:**
```bash
# Activate venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Database Error: "table doesn't exist"

**Solution:**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 4. Port 8000 Already in Use

**Solution:**
```bash
# Option 1: Use different port
python manage.py runserver 8001

# Option 2: Kill process on port 8000
# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

### 5. "No such table: clips_video"

**Error:**
```
django.db.utils.OperationalError: no such table: clips_video
```

**Solution:**
```bash
python manage.py migrate clips
```

If still not working:
```bash
python manage.py makemigrations clips
python manage.py migrate
```

---

### 6. Static Files Not Found (404)

**Solution:** Add to `settings.py`:
```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

Then run:
```bash
python manage.py collectstatic
```

---

### 7. Media Files Not Serving

**Check `settings.py`:**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**Check `urls.py`:**
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [...]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### 8. "SECRET_KEY" Error or Missing Settings

**Solution:** Create `.env` file:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

Update `settings.py`:
```python
from decouple import config

DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

---

## Frontend Issues

### 1. "Failed to resolve import @/components/..."

**Error:**
```
Failed to resolve import "@/components/VideosList.vue"
```

**Solution:** Check `vite.config.js`:
```javascript
import path from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

Restart Vite server after changes.

---

### 2. Port 5173 Already in Use

**Solution:**
```bash
# Option 1: Use different port
npm run dev -- --port 5174

# Option 2: Kill process
# macOS/Linux:
lsof -ti:5173 | xargs kill -9

# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

---

### 3. "Cannot find module 'axios'" or other packages

**Solution:**
```bash
npm install
```

If still not working:
```bash
rm -rf node_modules package-lock.json
npm install
```

---

### 4. Blank Page or White Screen

**Troubleshooting:**
1. Check browser console for errors (F12)
2. Check Network tab for failed requests
3. Verify backend is running
4. Check vite server is running (`npm run dev`)

**Solution:**
```bash
# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

# Rebuild frontend
rm -rf node_modules
npm install
npm run dev
```

---

### 5. API Requests Failing (404 or Connection Refused)

**Check:**
1. Django server running on 8000: `http://localhost:8000/api/clips/videos/`
2. API URL in `src/services/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000/api/clips'
```

3. Check browser Network tab for actual request URL

**Solution:**
```bash
# Make sure Django is running
python manage.py runserver
```

---

### 6. Video Player Not Working

**Check:**
1. Video file format (supports MP4, WebM, etc.)
2. CORS headers for media files
3. Correct media URL in response

**Solution:**
```python
# backend/settings.py
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

---

### 7. Vue DevTools Not Showing

**Solution:**
1. Install Vue DevTools extension for Chrome/Firefox
2. Make sure you're in development mode
3. Restart browser

---

## Common API Errors

### 400 Bad Request
```json
{
  "title": ["This field may not be blank."],
  "start_time": ["Ensure this value is greater than or equal to 0."]
}
```

**Fix:** Check request body matches serializer fields

---

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Fix:** 
- Currently API allows any user
- When implementing auth, pass token in headers:
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

**Fix:** Check if object exists:
```bash
# Via Django admin or API
GET /api/clips/videos/999/  # If ID 999 doesn't exist
```

---

### 500 Internal Server Error

**Check Django logs:**
```
Traceback (most recent call last):
  File "...", line X, in ...
    ...
```

**Common causes:**
- Database not migrated
- Missing imports
- Syntax errors
- Invalid file paths

**Solution:**
```bash
# Check server terminal for detailed error
# Fix the issue mentioned in traceback
# Restart server
```

---

## Performance Issues

### 1. Slow API Responses

**Solution:**
```python
# Use select_related for foreign keys
class VideoViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Video.objects.select_related('uploaded_by').prefetch_related('clips')
```

---

### 2. Slow Page Load

**Solution:**
```javascript
// Use lazy loading for routes
const VideoClipper = defineAsyncComponent(() => 
  import('@/pages/VideoClipper.vue')
)
```

---

### 3. Large File Upload Failing

**Increase file upload limit:**
```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
```

---

## Database Issues

### 1. Reset Database (Development Only!)

```bash
# Option 1: Delete and recreate
rm db.sqlite3
python manage.py migrate

# Option 2: Full reset
python manage.py flush

# Option 3: Specific app reset
python manage.py migrate clips zero
python manage.py migrate clips
```

---

### 2. Duplicate Migration Files

```bash
# Check migration files
ls clips/migrations/

# If too many, manually clean up old ones
# Keep 0001_initial.py and latest
```

---

### 3. Migration Conflicts

```bash
# Revert to specific migration
python manage.py migrate clips 0001

# Fake migrate
python manage.py migrate --fake

# Create new migrations
python manage.py makemigrations
python manage.py migrate
```

---

## Environment & Configuration Issues

### 1. "python: command not found"

**Solution:**
```bash
# Use python3 explicitly
python3 -m venv venv
python3 manage.py runserver

# Or set alias
alias python=python3
```

---

### 2. "npm: command not found"

**Solution:**
- Install Node.js from https://nodejs.org/
- Verify: `node --version` and `npm --version`

---

### 3. Wrong Python Version

```bash
# Check version
python --version

# Should be 3.8+
# If not, use python3 or update Python
```

---

## Debug Mode

### Enable Verbose Logging

**Backend:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

**Frontend:**
```javascript
// src/services/api.js
apiClient.interceptors.response.use(
  response => {
    console.log('API Response:', response.config.url, response.data);
    return response;
  },
  error => {
    console.error('API Error:', error.config.url, error.response);
    return Promise.reject(error);
  }
);
```

---

## Getting Help

1. **Check logs:**
   - Django console output
   - Browser DevTools (F12)
   - Vite server output

2. **Search errors:**
   - Google the error message
   - Check Stack Overflow
   - Check package documentation

3. **Documentation:**
   - [Django Docs](https://docs.djangoproject.com/)
   - [DRF Docs](https://www.django-rest-framework.org/)
   - [Vue Docs](https://vuejs.org/)

---

## Quick Reset Script

```bash
#!/bin/bash
# reset.sh - Reset entire development environment

echo "🔄 Resetting development environment..."

# Backend reset
echo "📦 Resetting backend..."
cd backend
rm -rf db.sqlite3
rm -rf media/
source venv/bin/activate
python manage.py migrate
echo "✅ Backend reset"

# Frontend reset
echo "📦 Resetting frontend..."
cd ../frontend
rm -rf node_modules
npm install
echo "✅ Frontend reset"

echo "🎉 Development environment reset complete!"
```

Save as `reset.sh` and run:
```bash
chmod +x reset.sh
./reset.sh
```

---

**Last Updated:** February 4, 2026
