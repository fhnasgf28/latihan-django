# YouTube Clipper + Captions (Local)

Aplikasi lokal untuk membuat clip dari video YouTube plus burn-in subtitle. Dibangun dengan Django REST + Celery + Redis + Vue 3 (Vite). Semua berjalan di mesin lokal, tanpa cloud.

> ⚠️ **Legal / Ethics**: Gunakan hanya untuk video yang kamu miliki haknya atau memiliki izin resmi. Jangan gunakan untuk konten berhak cipta tanpa izin.

## Fitur MVP
- Input URL YouTube
- Mode **Auto-split** (tiap N menit) atau **Manual ranges** (HH:MM:SS)
- Kualitas minimum: **Strict 1080p** atau fallback ke 720p/480p
- Subtitle: optional burn-in (default OFF), ambil official dulu lalu auto-subs, pilihan bahasa (default id lalu en)
- Job async di background (Celery + Redis)
- Progress + status + hasil download

## Tech Stack
- Backend: Django + Django REST Framework + Celery + Redis
- Frontend: Vue 3 + Vite
- Tools: yt-dlp + ffmpeg

## Struktur Repo
```
clipper-video/
├── backend/
├── frontend/
└── README.md
```

## Setup (Linux/Mac)

### 1) System Dependencies
Install: **ffmpeg**, **redis**, **yt-dlp**

Contoh:
- macOS (brew):
```
brew install ffmpeg redis yt-dlp
```
- Ubuntu/Debian:
```
sudo apt update
sudo apt install ffmpeg redis yt-dlp
```

### 2) Backend (Django)
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Backend berjalan di `http://localhost:8000`

### 3) Redis
```
redis-server
```

### 4) Celery Worker
```
cd backend
source .venv/bin/activate
celery -A clipper worker -l info
```

### 5) Frontend (Vue)
```
cd frontend
npm install
npm run dev
```
Frontend berjalan di `http://localhost:5173`

## Output Files
Semua output ada di:
```
backend/media/jobs/<job_id>/
```
Intermediates disimpan di:
```
backend/media/jobs/<job_id>/work/
```

## API Spec
### 1) POST `/api/jobs/`
Request JSON:
```json
{
  "youtube_url": "https://...",
  "mode": "auto" | "manual",
  "interval_minutes": 3,
  "ranges": [{"start":"00:01:00","end":"00:02:30"}],
  "max_clips": 0,
  "download_sections": false,
  "strict_1080": true,
  "min_height_fallback": 720,
  "subtitle_langs": ["id","en"],
  "burn_subtitles": false
}
```
Response:
```json
{ "id": "<uuid>", "status": "queued" }
```

### 2) GET `/api/jobs/<id>/`
Response:
```json
{
  "id": "<uuid>",
  "status": "queued|running|done|failed",
  "progress": 0,
  "message": "human readable status",
  "error": null,
  "results": [
    {"filename":"clip_001_caption.mp4","url":"/media/jobs/<id>/clip_001_caption.mp4"},
    {"filename":"clip_001.srt","url":"/media/jobs/<id>/clip_001.srt"}
  ]
}
```

### 3) GET `/api/jobs/<id>/download-zip/` (optional)
Menghasilkan zip semua output.

## Catatan
- Max durasi video: 2 jam
- Max jumlah clip: 60 (bisa batasi via `max_clips`). Opsi `download_sections` hanya download bagian clip yang dibutuhkan.
- Valid URL: `youtube.com` atau `youtu.be`

## Jalankan Sekaligus (ringkas)
1. `redis-server`
2. `python manage.py runserver`
3. `celery -A clipper worker -l info`
4. `npm run dev`
