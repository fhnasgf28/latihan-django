<template>
  <section class="mt-10 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
    <div class="glass rounded-3xl p-6 md:p-8">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="text-2xl font-semibold text-white">Mulai Job</h2>
          <p class="mt-2 text-sm text-slate-300">Lebih cepat dengan opsi burn subtitle yang bisa dimatikan.</p>
        </div>
        <span class="rounded-full bg-emerald-500/20 px-3 py-1 text-xs text-emerald-200">Local</span>
      </div>

      <div class="mt-6 space-y-5">
        <VideoSourcePicker v-model="form" />

        <div>
          <label class="text-sm font-medium text-slate-200">Mode</label>
          <div class="mt-2 inline-flex rounded-full bg-slate-900/80 p-1">
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm"
              :class="form.mode === 'auto' ? 'bg-white text-slate-900' : 'text-slate-300'"
              @click="form.mode = 'auto'"
            >
              Auto Split
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm"
              :class="form.mode === 'manual' ? 'bg-white text-slate-900' : 'text-slate-300'"
              @click="form.mode = 'manual'"
            >
              Manual Ranges
            </button>
          </div>
        </div>

        <div v-if="form.mode === 'auto'">
          <label class="text-sm font-medium text-slate-200">Interval (menit)</label>
          <input
            v-model.number="form.interval_minutes"
            type="number"
            min="1"
            class="mt-2 w-full rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-white"
          />
        </div>

        <div v-else>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-slate-200">Ranges (HH:MM:SS)</label>
            <button type="button" class="text-xs font-semibold text-sky-300" @click="addRange">
              Tambah Range
            </button>
          </div>
          <div class="mt-3 space-y-3">
            <div v-for="(range, index) in form.ranges" :key="index" class="grid grid-cols-[1fr_auto_1fr_auto] items-center gap-2">
              <input v-model.trim="range.start" type="text" placeholder="00:00:00" class="rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white" />
              <span class="text-xs text-slate-400">to</span>
              <input v-model.trim="range.end" type="text" placeholder="00:00:30" class="rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white" />
              <button
                v-if="form.ranges.length > 1"
                type="button"
                class="text-xs text-rose-300"
                @click="removeRange(index)"
              >
                Hapus
              </button>
            </div>
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-slate-200">Maksimum clip diproses</label>
          <div class="mt-2 flex items-center gap-3">
            <input
              v-model.number="form.max_clips"
              type="number"
              min="0"
              max="60"
              class="w-32 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-white"
            />
            <span class="text-xs text-slate-400">0 = proses semua</span>
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-slate-200">Mode download</label>
          <div class="mt-2 flex items-center gap-3">
            <label class="flex items-center gap-2 text-sm text-slate-300">
              <input type="checkbox" v-model="form.download_sections" :disabled="form.source === 'local'" class="h-4 w-4 rounded border-white/20" />
              Download sections (streaming)
            </label>
          </div>
          <p class="mt-2 text-xs text-slate-400">Mode ini hanya download bagian clip yang dibutuhkan (YouTube saja).</p>
        </div>

        <div>
          <label class="text-sm font-medium text-slate-200">Orientasi output</label>
          <div class="mt-2 inline-flex rounded-full bg-slate-900/80 p-1">
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm"
              :class="form.orientation === 'landscape' ? 'bg-white text-slate-900' : 'text-slate-300'"
              @click="form.orientation = 'landscape'"
            >
              Landscape (16:9)
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm"
              :class="form.orientation === 'portrait' ? 'bg-white text-slate-900' : 'text-slate-300'"
              @click="form.orientation = 'portrait'"
            >
              Portrait (9:16)
            </button>
          </div>
          <p class="mt-2 text-xs text-slate-400">Portrait akan lebih lambat karena perlu re-encode.</p>
        </div>

        <div>
          <label class="text-sm font-medium text-slate-200">Quality</label>
          <div class="mt-2 flex flex-wrap items-center gap-3">
            <label class="flex items-center gap-2 text-sm text-slate-300">
              <input type="checkbox" v-model="form.strict_1080" class="h-4 w-4 rounded border-white/20" />
              Strict 1080p
            </label>
            <div v-if="!form.strict_1080" class="flex items-center gap-2">
              <span class="text-xs text-slate-400">Fallback</span>
              <select v-model.number="form.min_height_fallback" class="rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-xs text-white">
                <option :value="720">720p</option>
                <option :value="480">480p</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-slate-200">Subtitle</label>
          <div class="mt-2 flex items-center gap-3">
            <label class="flex items-center gap-2 text-sm text-slate-300">
              <input type="checkbox" v-model="form.burn_subtitles" class="h-4 w-4 rounded border-white/20" />
              Burn subtitle (lebih lama)
            </label>
          </div>
          <div class="mt-3 flex items-center gap-3">
            <label class="flex items-center gap-2 text-sm text-slate-300">
              <input type="checkbox" v-model="form.auto_captions" class="h-4 w-4 rounded border-white/20" />
              Auto captions jika tidak ada di YouTube
            </label>
          </div>
          <div class="mt-3 grid gap-3 md:grid-cols-2" :class="!form.auto_captions ? 'opacity-50' : ''">
            <div>
              <span class="text-xs text-slate-400">Whisper model</span>
              <select
                v-model="form.whisper_model"
                :disabled="!form.auto_captions"
                class="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white"
              >
                <option value="tiny">Tiny (paling cepat)</option>
                <option value="base">Base</option>
                <option value="small">Small</option>
              </select>
            </div>
            <div>
              <span class="text-xs text-slate-400">Auto caption lang</span>
              <select
                v-model="form.auto_caption_lang"
                :disabled="!form.auto_captions"
                class="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white"
              >
                <option value="id">Bahasa Indonesia</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
          <div class="mt-3 grid gap-3 md:grid-cols-2" :class="!form.burn_subtitles ? 'opacity-50' : ''">
            <div>
              <span class="text-xs text-slate-400">Primary</span>
              <select v-model="form.subtitle_primary" :disabled="!form.burn_subtitles" class="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white">
                <option value="id">Bahasa Indonesia</option>
                <option value="en">English</option>
              </select>
            </div>
            <div>
              <span class="text-xs text-slate-400">Fallback</span>
              <div class="mt-2 flex items-center gap-2">
                <input id="fallback" type="checkbox" v-model="form.subtitle_fallback_enabled" :disabled="!form.burn_subtitles" class="h-4 w-4 rounded border-white/20" />
                <label for="fallback" class="text-xs text-slate-300">Aktifkan</label>
              </div>
              <select
                v-model="form.subtitle_fallback"
                :disabled="!form.burn_subtitles || !form.subtitle_fallback_enabled"
                class="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white"
              >
                <option value="en">English</option>
                <option value="id">Bahasa Indonesia</option>
              </select>
            </div>
          </div>
        </div>

        <button
          class="mt-2 w-full rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5"
          type="button"
          @click="submitJob"
          :disabled="loading"
        >
          {{ loading ? 'Mengirim...' : 'Jalankan Job' }}
        </button>

        <p v-if="error" class="text-sm font-semibold text-rose-300">{{ error }}</p>
      </div>
    </div>

    <div class="glass rounded-3xl p-6 md:p-8">
      <h2 class="text-2xl font-semibold text-white">Status</h2>
      <p v-if="!job" class="mt-3 text-sm text-slate-400">Belum ada job berjalan.</p>

      <div v-else class="mt-4 space-y-4">
        <div class="flex items-center justify-between">
          <span class="rounded-full px-3 py-1 text-xs uppercase tracking-widest" :class="statusClass">
            {{ job.status }}
          </span>
          <span class="text-xs text-slate-400">Job ID: {{ jobId }}</span>
        </div>
        <button
          v-if="canCancel"
          type="button"
          class="rounded-xl border border-rose-300/40 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-500/20"
          @click="cancelJob"
        >
          Cancel Job
        </button>
        <p class="text-sm text-slate-200">{{ job.message }}</p>

        <div class="flex items-center justify-between text-xs text-slate-300">
          <span>Progress</span>
          <span class="font-semibold">{{ numericProgress }}%</span>
        </div>
        <div class="h-2 rounded-full bg-slate-800">
          <div class="h-2 rounded-full bg-gradient-to-r from-sky-400 via-purple-400 to-emerald-400" :style="{ width: `${numericProgress}%` }"></div>
        </div>
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>Estimasi waktu</span>
          <span>{{ etaText }}</span>
        </div>

        <p v-if="job.error" class="text-sm font-semibold text-rose-300">{{ job.error }}</p>

        <div v-if="job.results && job.results.length" class="space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-white">Outputs</h3>
            <a :href="zipUrl" target="_blank" rel="noreferrer" class="text-xs text-sky-300">Download ZIP</a>
          </div>
          <ul class="space-y-2 text-sm text-slate-200">
            <li v-for="file in job.results" :key="file.filename">
              <a :href="resolveUrl(file.url)" target="_blank" rel="noreferrer" class="hover:text-white">
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { jobAPI } from '@/services/api'
import { jobStorage } from "@/services/jobStorage";
import VideoSourcePicker from '@/components/VideoSourcePicker.vue'

const FORM_YOUTUBE_URL_STORAGE_KEY = 'clipper_last_youtube_url'

// Job persistence
const currentJob = ref(null)
const pollingInterval = ref(null)

const form = ref({
  source: 'youtube',
  youtube_url: '',
  local_file: null,
  local_name: '',
  mode: 'auto',
  interval_minutes: 3,
  ranges: [{ start: '00:00:00', end: '00:01:00' }],
  max_clips: 1,
  download_sections: true,
  orientation: 'landscape',
  strict_1080: true,
  min_height_fallback: 720,
  burn_subtitles: false,
  auto_captions: false,
  auto_caption_lang: 'id',
  whisper_model: 'tiny',
  subtitle_primary: 'id',
  subtitle_fallback_enabled: true,
  subtitle_fallback: 'en'
})

const jobId = ref('')
const job = ref(null)
const loading = ref(false)
const error = ref('')
const polling = ref(null)
const progressPoints = ref([])

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

const statusClass = computed(() => {
  if (!job.value) return 'bg-slate-800 text-slate-300'
  if (job.value.status === 'done') return 'bg-emerald-500/20 text-emerald-200'
  if (job.value.status === 'canceled') return 'bg-slate-500/30 text-slate-200'
  if (job.value.status === 'failed') return 'bg-rose-500/20 text-rose-200'
  if (job.value.status === 'running') return 'bg-sky-500/20 text-sky-200'
  return 'bg-amber-500/20 text-amber-200'
})

const canCancel = computed(() => {
  if (!job.value) return false
  return ['queued', 'running'].includes(job.value.status)
})

const numericProgress = computed(() => {
  if (!job.value || typeof job.value.progress !== 'number') return 0
  return Math.min(100, Math.max(0, Math.round(job.value.progress)))
})

const etaText = computed(() => {
  if (!job.value) return '-'
  if (job.value.status === 'done') return 'Selesai'
  if (job.value.status === 'failed') return '-'
  const estimate = estimateEtaSeconds()
  if (estimate == null || estimate === Infinity) return 'Menghitung...'
  if (estimate < 10) return '< 10 detik'
  const minutes = Math.floor(estimate / 60)
  const seconds = Math.round(estimate % 60)
  if (minutes > 0) return `${minutes}m ${seconds}s`
  return `${seconds}s`
})

const resolveUrl = (url) => {
  if (!url) return '#'
  if (url.startsWith('http')) return url
  // Jika URL sudah relatif (misal /media/...), biarkan saja.
  // Browser akan otomatis menambahkan host saat ini (misal 100.x.x.x:5173)
  // yang kemudian akan di-proxy ke backend.
  return url
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
  max_clips: form.value.max_clips,
  download_sections: form.value.download_sections,
  orientation: form.value.orientation,
  strict_1080: form.value.strict_1080,
  min_height_fallback: form.value.strict_1080 ? 720 : form.value.min_height_fallback,
  burn_subtitles: form.value.burn_subtitles,
  auto_captions: form.value.auto_captions,
  auto_caption_lang: form.value.auto_caption_lang,
  whisper_model: form.value.whisper_model,
  subtitle_langs: (form.value.burn_subtitles || form.value.auto_captions) ? subtitleLangs.value : []
})

const resetProgress = () => {
  progressPoints.value = []
}

const recordProgress = (progress) => {
  if (typeof progress !== 'number') return
  const now = Date.now()
  const last = progressPoints.value[progressPoints.value.length - 1]
  if (last && Math.round(last.progress) === Math.round(progress)) {
    return
  }
  progressPoints.value.push({ time: now, progress })
  if (progressPoints.value.length > 6) {
    progressPoints.value.shift()
  }
}

const estimateEtaSeconds = () => {
  if (progressPoints.value.length < 2) return null
  const first = progressPoints.value[0]
  const last = progressPoints.value[progressPoints.value.length - 1]
  const deltaProgress = last.progress - first.progress
  const deltaTime = (last.time - first.time) / 1000
  if (deltaProgress <= 0 || deltaTime <= 0) return null
  const rate = deltaProgress / deltaTime
  const remaining = Math.max(0, 100 - last.progress)
  return remaining / rate
}

const submitJob = async () => {
  error.value = ''
  if (form.value.source === 'youtube') {
    if (!form.value.youtube_url) {
      error.value = 'URL YouTube wajib diisi.'
      return
    }
  } else {
    if (!form.value.local_file) {
      error.value = 'File video wajib dipilih.'
      return
    }
  }
  loading.value = true
  try {
    let response
    const payload = buildPayload()
    if (form.value.source === 'youtube') {
      response = await jobAPI.create(payload)
    } else {
      const fd = new FormData()
      fd.append('video_file', form.value.local_file)
      Object.entries(payload).forEach(([key, value]) => {
        if (value === null || value === undefined) return
        if (key === 'youtube_url' || key === 'source_type') return
        if (Array.isArray(value) || typeof value === 'object') {
          fd.append(key, JSON.stringify(value))
        } else {
          fd.append(key, String(value))
        }
      })
      response = await jobAPI.createLocal(fd)
    }
    jobId.value = response.data.id
    job.value = { status: response.data.status, progress: 0, message: 'Queued', error: null }
    
    console.log('🆕 [VideoClipper] New job created:', response.data)
    
    // Save to localStorage for persistence
    currentJob.value = {
      id: response.data.id,
      access_token: response.data.access_token,
      status: response.data.status,
      progress: response.data.progress ?? 0,
      created_at: response.data.created_at || new Date().toISOString()
    }
    
    console.log('💾 [VideoClipper] Saving job to localStorage:', currentJob.value)
    jobStorage.saveJob(currentJob.value)
    
    resetProgress()
    startPolling()
    console.log('🔄 [VideoClipper] Started polling for new job')
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
    recordProgress(response.data.progress)
    if (['done', 'failed'].includes(job.value.status)) {
      stopPolling()
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message
    stopPolling()
  }
}

const checkJobStatus = async () => {
  if (!currentJob.value) return
  
  console.log('🔍 [VideoClipper] Checking job status for:', currentJob.value.id)
  
  try {
    jobId.value = currentJob.value.id
    const response = await jobAPI.get(currentJob.value.id, {
      params: { token: currentJob.value.access_token }
    })
    
    console.log('✅ [VideoClipper] Job status response:', response.data)
    
    // Update both currentJob and job for UI
    currentJob.value = {
      ...response.data,
      access_token: currentJob.value.access_token,
      created_at: currentJob.value.created_at || response.data.created_at
    }
    job.value = response.data
    
    jobStorage.saveJob(currentJob.value)
    console.log('💾 [VideoClipper] Job state updated and saved')
    
    if (['done', 'failed', 'canceled'].includes(currentJob.value.status)) {
      console.log('🎉 [VideoClipper] Job completed, stopping polling')
      stopPolling()
      jobStorage.clearJob()
    }
  } catch (error) {
    console.error('❌ [VideoClipper] Error checking job status:', error)
    if (error.response?.status === 403) {
      console.log('🔒 [VideoClipper] Access denied, clearing job')
      stopPolling()
      jobStorage.clearJob()
      currentJob.value = null
      job.value = null
    }
  }
}

const cancelJob = async () => {
  if (!currentJob.value?.id || !currentJob.value?.access_token) {
    error.value = 'Tidak bisa cancel: token job tidak tersedia.'
    return
  }
  try {
    const response = await jobAPI.cancel(currentJob.value.id, currentJob.value.access_token)
    if (['canceled', 'failed', 'done'].includes(response.data.status)) {
      stopPolling()
      jobStorage.clearJob()
      job.value = null
      currentJob.value = null
      jobId.value = ''
    } else {
      job.value = response.data
      currentJob.value = {
        ...response.data,
        id: currentJob.value.id,
        access_token: currentJob.value.access_token,
        created_at: currentJob.value.created_at
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Gagal cancel job.'
  }
}

const startPolling = () => {
  stopPolling()
  checkJobStatus()
  pollingInterval.value = setInterval(checkJobStatus, 2000)
}

const stopPolling = () => {
  if (polling.value) {
    clearInterval(polling.value)
    polling.value = null
  }
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

onMounted(async () => {
  const savedYoutubeUrl = sessionStorage.getItem(FORM_YOUTUBE_URL_STORAGE_KEY)
  if (savedYoutubeUrl) {
    form.value.youtube_url = savedYoutubeUrl
  }

  console.log('🚀 [VideoClipper] Component mounted, checking for stored job...')
  const storedJob = jobStorage.getJob()
  console.log('🔍 [VideoClipper] Stored job found:', storedJob)
  
  if (storedJob && jobStorage.isJobValid(storedJob)) {
    console.log('✅ [VideoClipper] Valid job found, restoring...')
    currentJob.value = storedJob
    jobId.value = storedJob.id
    await checkJobStatus()
    if (currentJob.value && ['queued', 'running'].includes(currentJob.value.status)) {
      startPolling()
    }
  } else {
    console.log('ℹ️ [VideoClipper] No valid stored job found')
  }
})

watch(
  () => form.value.youtube_url,
  (url) => {
    sessionStorage.setItem(FORM_YOUTUBE_URL_STORAGE_KEY, url || '')
  }
)

onBeforeUnmount(stopPolling)
</script>
