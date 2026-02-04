# API Documentation - Video Clipper

## Base URL
```
http://localhost:8000/api/clips
```

## Authentication
Saat ini API menggunakan `AllowAny` permission. Untuk production, implementasikan JWT atau Token authentication.

---

## Videos Endpoint

### 1. List All Videos
```
GET /videos/
```

**Query Parameters:**
- `search` (string): Search by title or description
- `ordering` (string): Order by field (created_at, title)

**Example:**
```bash
GET /videos/?search=tutorial&ordering=-created_at
```

**Response (200 OK):**
```json
{
  "count": 5,
  "next": "http://localhost:8000/api/clips/videos/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "My First Video",
      "description": "This is my first video",
      "thumbnail": "http://localhost:8000/media/thumbnails/video_1.jpg",
      "duration": 120.5,
      "uploaded_by": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "first_name": "",
        "last_name": ""
      },
      "created_at": "2026-02-04T12:00:00Z",
      "clips_count": 3
    }
  ]
}
```

---

### 2. Get Video Detail
```
GET /videos/{id}/
```

**Example:**
```bash
GET /videos/1/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "My First Video",
  "description": "This is my first video",
  "video_file": "http://localhost:8000/media/videos/video_1.mp4",
  "duration": 120.5,
  "thumbnail": "http://localhost:8000/media/thumbnails/video_1.jpg",
  "uploaded_by": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "",
    "last_name": ""
  },
  "created_at": "2026-02-04T12:00:00Z",
  "updated_at": "2026-02-04T12:00:00Z",
  "clips": [
    {
      "id": 1,
      "title": "Best Moment",
      "description": "The best part",
      "video": 1,
      "start_time": 10.5,
      "end_time": 30.2,
      "thumbnail": null,
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2026-02-04T13:00:00Z",
      "updated_at": "2026-02-04T13:00:00Z",
      "is_public": true,
      "duration": 19.7
    }
  ],
  "clips_count": 1
}
```

---

### 3. Upload Video
```
POST /videos/
Content-Type: multipart/form-data
```

**Request Body:**
```
title: "My Video"
description: "A great video"
duration: 120.5
video_file: [binary file data]
thumbnail: [optional binary image data]
```

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/clips/videos/ \
  -F "title=My Video" \
  -F "description=A great video" \
  -F "duration=120.5" \
  -F "video_file=@/path/to/video.mp4"
```

**Response (201 Created):**
```json
{
  "id": 2,
  "title": "My Video",
  "description": "A great video",
  "video_file": "http://localhost:8000/media/videos/video_2.mp4",
  "duration": 120.5,
  "thumbnail": null,
  "uploaded_by": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "",
    "last_name": ""
  },
  "created_at": "2026-02-04T14:00:00Z",
  "updated_at": "2026-02-04T14:00:00Z",
  "clips": [],
  "clips_count": 0
}
```

---

### 4. Update Video
```
PUT /videos/{id}/
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Updated Title",
  "description": "Updated description",
  ...
}
```

---

### 5. Delete Video
```
DELETE /videos/{id}/
```

**Response (204 No Content)**

---

### 6. Get Clips for Video
```
GET /videos/{id}/clips/
```

**Example:**
```bash
GET /videos/1/clips/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Best Moment",
    "description": "The best part",
    "video": 1,
    "start_time": 10.5,
    "end_time": 30.2,
    "thumbnail": null,
    "created_by": {
      "id": 1,
      "username": "admin"
    },
    "created_at": "2026-02-04T13:00:00Z",
    "updated_at": "2026-02-04T13:00:00Z",
    "is_public": true,
    "duration": 19.7
  }
]
```

---

## Clips Endpoint

### 1. List All Clips
```
GET /clips/
```

**Query Parameters:**
- `search` (string): Search by title or description
- `video_id` (integer): Filter by video ID
- `ordering` (string): Order by field (created_at, start_time)

**Example:**
```bash
GET /clips/?video_id=1&ordering=-created_at
```

**Response (200 OK):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Best Moment",
      "description": "The best part",
      "video": 1,
      "start_time": 10.5,
      "end_time": 30.2,
      "thumbnail": null,
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2026-02-04T13:00:00Z",
      "updated_at": "2026-02-04T13:00:00Z",
      "is_public": true,
      "duration": 19.7
    }
  ]
}
```

---

### 2. Get Clip Detail
```
GET /clips/{id}/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Best Moment",
  "description": "The best part",
  "video": 1,
  "start_time": 10.5,
  "end_time": 30.2,
  "thumbnail": null,
  "created_by": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "",
    "last_name": ""
  },
  "created_at": "2026-02-04T13:00:00Z",
  "updated_at": "2026-02-04T13:00:00Z",
  "is_public": true,
  "duration": 19.7
}
```

---

### 3. Create Clip
```
POST /clips/
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Amazing Moment",
  "description": "This is amazing",
  "video": 1,
  "start_time": 15.5,
  "end_time": 45.2,
  "is_public": true
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "title": "Amazing Moment",
  "description": "This is amazing",
  "video": 1,
  "start_time": 15.5,
  "end_time": 45.2,
  "thumbnail": null,
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2026-02-04T14:00:00Z",
  "updated_at": "2026-02-04T14:00:00Z",
  "is_public": true,
  "duration": 29.7
}
```

---

### 4. Update Clip
```
PUT /clips/{id}/
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "is_public": false
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Updated Title",
  "description": "Updated description",
  "is_public": false,
  ...
}
```

---

### 5. Delete Clip
```
DELETE /clips/{id}/
```

**Response (204 No Content)**

---

### 6. Toggle Public Status
```
POST /clips/{id}/toggle_public/
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Best Moment",
  "description": "The best part",
  "video": 1,
  "start_time": 10.5,
  "end_time": 30.2,
  "thumbnail": null,
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2026-02-04T13:00:00Z",
  "updated_at": "2026-02-04T14:30:00Z",
  "is_public": false,
  "duration": 19.7
}
```

---

### 7. Get My Clips
```
GET /clips/my_clips/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Best Moment",
    "description": "The best part",
    "video": 1,
    "start_time": 10.5,
    "end_time": 30.2,
    "thumbnail": null,
    "created_by": {
      "id": 1,
      "username": "admin"
    },
    "created_at": "2026-02-04T13:00:00Z",
    "updated_at": "2026-02-04T13:00:00Z",
    "is_public": true,
    "duration": 19.7
  }
]
```

---

### 8. Get Public Clips
```
GET /clips/public_clips/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Best Moment",
    "description": "The best part",
    "video": 1,
    "start_time": 10.5,
    "end_time": 30.2,
    "thumbnail": null,
    "created_by": {
      "id": 1,
      "username": "admin"
    },
    "created_at": "2026-02-04T13:00:00Z",
    "updated_at": "2026-02-04T13:00:00Z",
    "is_public": true,
    "duration": 19.7
  }
]
```

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}
```

---

## Testing API with cURL

### Get all videos
```bash
curl -X GET http://localhost:8000/api/clips/videos/
```

### Create a clip
```bash
curl -X POST http://localhost:8000/api/clips/clips/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Clip",
    "description": "A great clip",
    "video": 1,
    "start_time": 10.5,
    "end_time": 30.2,
    "is_public": true
  }'
```

### Update a video
```bash
curl -X PUT http://localhost:8000/api/clips/videos/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title"
  }'
```

### Delete a clip
```bash
curl -X DELETE http://localhost:8000/api/clips/clips/1/
```

---

## Pagination

List endpoints support pagination:

```bash
GET /videos/?page=1&page_size=10
```

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/clips/videos/?page=2",
  "previous": null,
  "results": [...]
}
```

Default page size: 10 items

---

## Filtering & Searching

### Search Videos
```bash
GET /videos/?search=tutorial
```

### Filter Clips by Video
```bash
GET /clips/?video_id=1
```

### Combine Multiple Filters
```bash
GET /clips/?video_id=1&search=amazing&ordering=-created_at
```

---

**Last Updated:** February 4, 2026
