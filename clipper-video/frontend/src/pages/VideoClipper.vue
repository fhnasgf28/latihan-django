<template>
  <section class="clipper">
    <div class="form-card">
      <h2>Mulai Job</h2>
      <p class="muted">Semua proses berjalan lokal via Celery + ffmpeg + yt-dlp.</p>

      <div class="field">
        <label>URL YouTube</label>
        <input
          v-model.trim="form.youtube_url"
          type="text"
          placeholder="https://www.youtube.com/watch?v=..."
        />
      </div>

      <div class="field">
        <label>Mode</label>
        <div class="toggle">
          <button
            :class="{ active: form.mode === 'auto' }"
            type="button"
            @click="form.mode = 'auto'"
          >
            Auto Split
          </button>
          <button
            :class="{ active: form.mode === 'manual' }"
            type="button"
            @click="form.mode = 'manual'"
          >
            Manual Ranges
          </button>
        </div>
      </div>

      <div v-if="form.mode === 'auto'" class="field">
        <label>Interval (menit)</label>
        <input v-model.number="form.interval_minutes" type="number" min="1" />
      </div>

      <div v-else class="ranges">
        <div class="ranges-header">
          <label>Ranges (HH:MM:SS)</label>
          <button type="button" class="ghost" @click="addRange">Tambah Range</button>
        </div>
        <div class="range-row" v-for="(range, index) in form.ranges" :key="index">
          <input v-model.trim="range.start" type="text" placeholder="00:00:00" />
          <span>to</span>
          <input v-model.trim="range.end" type="text" placeholder="00:00:30" />
          <button
            v-if="form.ranges.length > 1"
            type="button"
            class="ghost"
            @click="removeRange(index)"
          >
            Hapus
          </button>
        </div>
      </div>

      <div class="field">
        <label>Quality</label>
        <div class="checkbox-row">
          <input id="strict1080" type="checkbox" v-model="form.strict_1080" />
          <label for="strict1080">Strict 1080p (fail kalau tidak tersedia)</label>
        </div>
        <div v-if="!form.strict_1080" class="fallback">
          <label>Fallback minimum</label>
          <select v-model.number="form.min_height_fallback">
            <option :value="720">720p</option>
            <option :value="480">480p</option>
          </select>
        </div>
      </div>

      <div class="field">
        <label>Subtitle Priority</label>
        <div class="subtitle-grid">
          <div>
            <span class="muted">Primary</span>
            <select v-model="form.subtitle_primary">
              <option value="id">Bahasa Indonesia</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <span class="muted">Fallback</span>
            <div class="checkbox-row">
              <input id="fallback" type="checkbox" v-model="form.subtitle_fallback_enabled" />
              <label for="fallback">Aktifkan</label>
            </div>
            <select v-model="form.subtitle_fallback" :disabled="!form.subtitle_fallback_enabled">
              <option value="en">English</option>
              <option value="id">Bahasa Indonesia</option>
            </select>
          </div>
        </div>
      </div>

      <button class="primary" type="button" @click="submitJob" :disabled="loading">
        {{ loading ? 'Mengirim...' : 'Jalankan Job' }}
      </button>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div class="status-card">
      <h2>Status</h2>
      <div v-if="!job" class="muted">Belum ada job berjalan.</div>

      <div v-else class="status-body">
        <div class="status-line">
          <span class="pill" :class="job.status">{{ job.status }}</span>
          <span class="muted">Job ID: {{ jobId }}</span>
        </div>
        <p class="message">{{ job.message }}</p>
        <div class="progress">
          <div class="progress-bar" :style="{ width: `${job.progress}%` }"></div>
        </div>
        <div v-if="job.error" class="error">{{ job.error }}</div>

        <div v-if="job.results && job.results.length" class="results">
          <div class="results-header">
            <h3>Outputs</h3>
            <a class="ghost" :href="zipUrl" target="_blank" rel="noreferrer">Download ZIP</a>
          </div>
          <ul>
            <li v-for="file in job.results" :key="file.filename">
              <a :href="resolveUrl(file.url)" target="_blank" rel="noreferrer">
                {{ file.filename }}
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { jobAPI } from '@/services/api'

const form = ref({
  youtube_url: '',
  mode: 'auto',
  interval_minutes: 3,
  ranges: [{ start: '00:00:00', end: '00:01:00' }],
  strict_1080: true,
  min_height_fallback: 720,
  subtitle_primary: 'id',
  subtitle_fallback_enabled: true,
  subtitle_fallback: 'en'
})

const jobId = ref('')
const job = ref(null)
const loading = ref(false)
const error = ref('')
const polling = ref(null)

const zipUrl = computed(() => (jobId.value ? jobAPI.downloadZipUrl(jobId.value) : '#'))

const subtitleLangs = computed(() => {
  const langs = [form.value.subtitle_primary]
  if (form.value.subtitle_fallback_enabled) {
    if (!langs.includes(form.value.subtitle_fallback)) {
      langs.push(form.value.subtitle_fallback)
    }
  }
  return langs
})

const resolveUrl = (url) => {
  if (!url) return '#'
  if (url.startsWith('http')) return url
  return `http://localhost:8000${url}`
}

const addRange = () => {
  form.value.ranges.push({ start: '00:00:00', end: '00:00:30' })
}

const removeRange = (index) => {
  form.value.ranges.splice(index, 1)
}

const buildPayload = () => ({
  youtube_url: form.value.youtube_url,
  mode: form.value.mode,
  interval_minutes: form.value.mode === 'auto' ? form.value.interval_minutes : null,
  ranges: form.value.mode === 'manual' ? form.value.ranges : null,
  strict_1080: form.value.strict_1080,
  min_height_fallback: form.value.strict_1080 ? 720 : form.value.min_height_fallback,
  subtitle_langs: subtitleLangs.value
})

const submitJob = async () => {
  error.value = ''
  if (!form.value.youtube_url) {
    error.value = 'URL YouTube wajib diisi.'
    return
  }
  loading.value = true
  try {
    const response = await jobAPI.create(buildPayload())
    jobId.value = response.data.id
    job.value = { status: response.data.status, progress: 0, message: 'Queued', error: null }
    startPolling()
  } catch (err) {
    error.value = err.response?.data?.detail || err.response?.data?.error || err.message
  } finally {
    loading.value = false
  }
}

const fetchJob = async () => {
  if (!jobId.value) return
  try {
    const response = await jobAPI.get(jobId.value)
    job.value = response.data
    if (['done', 'failed'].includes(job.value.status)) {
      stopPolling()
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message
    stopPolling()
  }
}

const startPolling = () => {
  stopPolling()
  fetchJob()
  polling.value = setInterval(fetchJob, 1500)
}

const stopPolling = () => {
  if (polling.value) {
    clearInterval(polling.value)
    polling.value = null
  }
}

onBeforeUnmount(stopPolling)
</script>

<style scoped>
.clipper {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  gap: 24px;
}

.form-card,
.status-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(8px);
}

h2 {
  margin: 0 0 8px;
}

.field {
  margin-bottom: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 600;
}

input[type='text'],
input[type='number'],
select {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #d0d7e2;
  font-size: 14px;
  background: #fff;
}

.toggle {
  display: inline-flex;
  gap: 8px;
  background: #eef2ff;
  padding: 6px;
  border-radius: 999px;
}

.toggle button {
  border: none;
  background: transparent;
  padding: 8px 16px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
}

.toggle button.active {
  background: #111827;
  color: #fff;
}

.ranges {
  margin-bottom: 18px;
}

.ranges-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.range-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  gap: 8px;
  margin-bottom: 10px;
}

.checkbox-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.fallback {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.subtitle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.primary {
  width: 100%;
  padding: 12px 16px;
  background: #111827;
  color: #fff;
  border: none;
  border-radius: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(17, 24, 39, 0.2);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.ghost {
  background: transparent;
  border: 1px dashed #c7d2fe;
  color: #4f46e5;
  padding: 6px 12px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
}

.status-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.pill.queued {
  background: #fef3c7;
  color: #92400e;
}

.pill.running {
  background: #dbeafe;
  color: #1d4ed8;
}

.pill.done {
  background: #dcfce7;
  color: #166534;
}

.pill.failed {
  background: #fee2e2;
  color: #991b1b;
}

.progress {
  background: #e5e7eb;
  border-radius: 999px;
  height: 10px;
  overflow: hidden;
}

.progress-bar {
  background: linear-gradient(90deg, #fb7185, #facc15, #34d399);
  height: 100%;
  transition: width 0.4s ease;
}

.results ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.results a {
  color: #111827;
  text-decoration: none;
  font-weight: 600;
}

.results a:hover {
  text-decoration: underline;
}

.muted {
  color: #6b7280;
  font-size: 14px;
}

.message {
  margin: 0;
}

.error {
  color: #b91c1c;
  font-weight: 600;
}

@media (max-width: 900px) {
  .clipper {
    grid-template-columns: 1fr;
  }
}
</style>
