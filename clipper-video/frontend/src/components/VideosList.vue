<template>
  <div class="videos-list">
    <h2>All Videos</h2>
    <div class="search-bar">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search videos..."
        @input="searchVideos"
      />
    </div>
    
    <div class="loading" v-if="loading">Loading videos...</div>
    <div class="error" v-else-if="error">{{ error }}</div>
    
    <div class="videos-grid" v-else>
      <div v-for="video in videos" :key="video.id" class="video-card">
        <img v-if="video.thumbnail" :src="video.thumbnail" :alt="video.title" />
        <div class="video-info">
          <h3>{{ video.title }}</h3>
          <p class="description">{{ video.description }}</p>
          <div class="meta">
            <span class="duration">⏱️ {{ formatDuration(video.duration) }}</span>
            <span class="clips">📎 {{ video.clips_count }} clips</span>
          </div>
          <p class="uploader">By: {{ video.uploaded_by.username }}</p>
          <router-link :to="`/video/${video.id}`" class="btn-primary">View & Clip</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { videoAPI } from '@/services/api'

export default {
  name: 'VideosList',
  data() {
    return {
      videos: [],
      loading: false,
      error: null,
      searchQuery: ''
    }
  },
  mounted() {
    this.fetchVideos()
  },
  methods: {
    fetchVideos() {
      this.loading = true
      this.error = null
      videoAPI.getAll()
        .then(response => {
          this.videos = response.data.results || response.data
        })
        .catch(error => {
          this.error = 'Failed to load videos: ' + error.message
          console.error(error)
        })
        .finally(() => {
          this.loading = false
        })
    },
    searchVideos() {
      this.loading = true
      videoAPI.getAll({ search: this.searchQuery })
        .then(response => {
          this.videos = response.data.results || response.data
        })
        .catch(error => {
          this.error = 'Search failed: ' + error.message
        })
        .finally(() => {
          this.loading = false
        })
    },
    formatDuration(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.videos-list {
  padding: 20px;
}

.search-bar {
  margin: 20px 0;
}

.search-bar input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
}

.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.video-card {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.video-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.video-card img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  background: #f0f0f0;
}

.video-info {
  padding: 15px;
}

.video-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
}

.description {
  color: #666;
  font-size: 14px;
  margin: 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #888;
  margin: 10px 0;
}

.uploader {
  font-size: 13px;
  color: #999;
  margin: 8px 0;
}

.btn-primary {
  display: inline-block;
  padding: 8px 16px;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 14px;
  transition: background 0.2s;
  margin-top: 10px;
}

.btn-primary:hover {
  background: #0056b3;
}

.loading, .error {
  text-align: center;
  padding: 40px 20px;
  font-size: 18px;
}

.error {
  color: #dc3545;
  background: #f8d7da;
  padding: 20px;
  border-radius: 5px;
  margin: 20px 0;
}
</style>
