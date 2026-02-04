# Quick Start Guide - Video Clipper

## 🚀 Cara Cepat Menjalankan Project

### 1. Backend Setup

```bash
# Masuk ke folder backend
cd clipper-video/backend

# Aktivasi virtual environment
source venv/bin/activate  # Mac/Linux
# atau
venv\Scripts\activate     # Windows

# Install dependencies (jika belum)
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (jika belum ada)
python manage.py createsuperuser

# Jalankan server
python manage.py runserver
```

Django akan berjalan di: **http://localhost:8000**

### 2. Frontend Setup (Terminal baru)

```bash
# Masuk ke folder frontend
cd clipper-video/frontend

# Install dependencies (jika belum)
npm install

# Jalankan dev server
npm run dev
```

Vue akan berjalan di: **http://localhost:5173**

## 📋 Checklist

- ✅ Django backend running di http://localhost:8000
- ✅ Vue frontend running di http://localhost:5173
- ✅ Database migrations applied
- ✅ Superuser created

## 🔗 Akses URL

| Resource | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/api/clips/ |
| Admin Panel | http://localhost:8000/admin |

## 🎯 Features Siap Digunakan

### Video Management
- ✅ List semua video
- ✅ Upload video baru (perlu auth)
- ✅ View detail video
- ✅ Search video

### Clip Creation
- ✅ Create clip dari video
- ✅ Set start/end time
- ✅ Toggle public/private
- ✅ View clips untuk video tertentu

### Admin Features
- ✅ Manage videos
- ✅ Manage clips
- ✅ User management

## 📝 Credentials

### Admin Login
- **Username:** admin
- **Password:** (set saat `createsuperuser`)
- **URL:** http://localhost:8000/admin

## 🛠️ Troubleshooting

### Port Sudah Digunakan?

#### Django
```bash
python manage.py runserver 8001
```

#### Vue
```bash
npm run dev -- --port 5174
```

### CORS Error?
Pastikan URL frontend ada di `CORS_ALLOWED_ORIGINS` di `backend/clipper/settings.py`

### Database Error?
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔄 API Response Format

### List Videos
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Sample Video",
      "description": "Description here",
      "duration": 120.5,
      "thumbnail": "url_to_thumbnail",
      "clips_count": 3,
      "uploaded_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2026-02-04T12:00:00Z"
    }
  ]
}
```

### Create Clip
```json
{
  "id": 1,
  "title": "Awesome Moment",
  "description": "Best part of video",
  "video": 1,
  "start_time": 10.5,
  "end_time": 30.2,
  "is_public": true,
  "duration": 19.7,
  "created_by": {
    "id": 1,
    "username": "admin"
  }
}
```

## 🎓 Next Steps

1. **Authentication**: Implementasikan JWT atau session auth
2. **Video Processing**: Tambahkan backend untuk process video
3. **Export**: Fitur export/download clip
4. **Real-time**: WebSocket untuk real-time updates
5. **Testing**: Tambahkan unit tests
6. **Deployment**: Siapkan production setup

## 📚 Dokumentasi Lengkap

Lihat [README.md](./README.md) untuk dokumentasi lengkap.

---

**Selamat menggunakan Video Clipper! 🎬**
