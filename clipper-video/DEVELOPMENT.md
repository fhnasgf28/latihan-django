# Development Guide - Video Clipper

## 🏗️ Project Architecture

### Backend Structure

```
backend/
├── clipper/              # Project settings
│   ├── settings.py       # Django settings & config
│   ├── urls.py          # Root URL configuration
│   ├── asgi.py          # ASGI config
│   └── wsgi.py          # WSGI config
├── clips/               # Main app
│   ├── models.py        # Video & Clip models
│   ├── views.py         # ViewSets for API
│   ├── serializers.py   # DRF serializers
│   ├── urls.py          # App URL routing
│   ├── admin.py         # Admin config
│   └── migrations/      # Database migrations
├── users/               # Users app (untuk future)
├── manage.py            # Django management
├── db.sqlite3           # Database
└── venv/                # Virtual environment
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/      # Reusable Vue components
│   │   └── VideosList.vue
│   ├── pages/           # Page components
│   │   └── VideoClipper.vue
│   ├── services/        # API services
│   │   └── api.js
│   ├── router/          # Vue Router config
│   │   └── index.js
│   ├── App.vue          # Root component
│   ├── main.js          # Entry point
│   └── style.css        # Global styles
├── public/              # Static assets
├── vite.config.js       # Vite configuration
├── package.json         # Dependencies
└── index.html           # HTML template
```

## 🗄️ Database Models

### Video Model
```python
Video
├── id (PK)
├── title (String)
├── description (Text)
├── video_file (File)
├── duration (Float) - dalam seconds
├── thumbnail (Image)
├── uploaded_by (FK → User)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### Clip Model
```python
Clip
├── id (PK)
├── title (String)
├── description (Text)
├── video (FK → Video)
├── start_time (Float) - dalam seconds
├── end_time (Float) - dalam seconds
├── thumbnail (Image)
├── created_by (FK → User)
├── created_at (DateTime)
├── updated_at (DateTime)
└── is_public (Boolean)
```

## 📡 API Endpoints

### Video Endpoints
```
GET     /api/clips/videos/                    # List videos
POST    /api/clips/videos/                    # Create video
GET     /api/clips/videos/{id}/               # Get video detail
PUT     /api/clips/videos/{id}/               # Update video
DELETE  /api/clips/videos/{id}/               # Delete video
GET     /api/clips/videos/{id}/clips/         # Get clips for video
```

### Clip Endpoints
```
GET     /api/clips/clips/                     # List clips
POST    /api/clips/clips/                     # Create clip
GET     /api/clips/clips/{id}/                # Get clip detail
PUT     /api/clips/clips/{id}/                # Update clip
DELETE  /api/clips/clips/{id}/                # Delete clip
POST    /api/clips/clips/{id}/toggle_public/  # Toggle public status
GET     /api/clips/clips/my_clips/            # Get my clips
GET     /api/clips/clips/public_clips/        # Get public clips
```

## 🔧 Konfigurasi Environment

### Backend (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend (vite.config.js)
```javascript
alias: {
  '@': path.resolve(__dirname, './src'),
}
```

## 📦 Dependencies

### Backend
- Django 4.2.28
- Django REST Framework 3.15.2
- django-cors-headers 4.4.0
- Pillow 10.4.0
- python-decouple 3.8

### Frontend
- Vue 3
- Vue Router 4
- Axios
- Vite

## 🧪 Development Tips

### Debugging Backend
```bash
# Tambahkan breakpoint di views.py
import pdb; pdb.set_trace()

# Atau gunakan print statements
print("Debug:", variable_name)
```

### Debugging Frontend
```javascript
// Vue DevTools di browser
// Chrome DevTools Console

console.log('Debug:', variableName)
debugger;
```

### Creating Sample Data

```bash
# Django shell
python manage.py shell

# Python code
from django.contrib.auth.models import User
from clips.models import Video

user = User.objects.first()
video = Video.objects.create(
    title="Test Video",
    description="Test",
    duration=100.5,
    video_file="path/to/file.mp4",
    uploaded_by=user
)
```

## 🚀 Common Development Tasks

### Add New Model Field
1. Edit `models.py`
2. Run `python manage.py makemigrations clips`
3. Run `python manage.py migrate`
4. Update serializers if needed

### Add New API Endpoint
1. Add method ke ViewSet di `views.py`
2. Use `@action` decorator untuk custom endpoints
3. Test dengan Postman atau curl

### Add New Vue Component
1. Create file di `src/components/`
2. Import dan register di parent component
3. Style dengan scoped CSS

### Update Frontend Routes
1. Edit `src/router/index.js`
2. Add route object
3. Import component

## 🐛 Common Issues & Solutions

### CORS Error
**Issue:** `Access to XMLHttpRequest blocked by CORS`

**Solution:**
```python
# backend/clipper/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Add your frontend URL
]
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python manage.py runserver 8001
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
npm install
```

### Migration Conflicts
```bash
# Reset migrations (development only!)
python manage.py migrate clips 0001
python manage.py migrate --fake clips
python manage.py makemigrations
python manage.py migrate
```

## 📊 Performance Tips

### Backend
- Use `select_related()` untuk foreign keys
- Use `prefetch_related()` untuk many-to-many
- Add pagination di list endpoints
- Cache frequently accessed data

### Frontend
- Use lazy loading untuk components
- Optimize images
- Minimize API calls
- Use Vue DevTools untuk profiling

## 🔐 Security Considerations

### Backend
- Set `DEBUG=False` di production
- Use strong `SECRET_KEY`
- Validate file uploads
- Implement proper authentication
- Use HTTPS in production

### Frontend
- Never store sensitive data di localStorage
- Sanitize user input
- Use environment variables untuk API URLs
- Implement CSRF protection

## 📝 Code Style

### Python (Django)
```python
# Follow PEP 8
# Use meaningful names
# Add docstrings

def create_clip(self, request):
    """Create a new clip from video."""
    serializer = self.get_serializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### JavaScript/Vue
```javascript
// Use camelCase
// Add comments untuk complex logic
// Use const/let, bukan var

const createClip = async () => {
  if (!isFormValid.value) return;
  
  try {
    const response = await clipAPI.create(clipForm.value);
    clips.value.push(response.data);
  } catch (error) {
    console.error('Failed to create clip:', error);
  }
}
```

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Vue.js Guide](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)

---

Happy coding! 🚀
