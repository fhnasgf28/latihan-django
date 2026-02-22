<template>
  <section class="mt-10 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
    <div class="order-2 glass rounded-3xl p-6 md:p-8 lg:order-1">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="text-2xl font-semibold text-white">Mulai Job</h2>
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
            <div v-for="(range, index) in form.ranges" :key="index" class="space-y-2">
              <div class="grid gap-2 sm:grid-cols-[1fr_auto_1fr_auto] sm:items-center">
                <input
                  v-model.trim="range.start"
                  type="text"
                  placeholder="Mulai (00:00:00)"
                  class="rounded-xl border bg-slate-900/70 px-3 py-2 text-sm text-white"
                  :class="getRangeError(range) ? 'border-rose-300/70' : 'border-white/10'"
                />
                <span class="hidden text-xs text-slate-400 sm:block">to</span>
                <input
                  v-model.trim="range.end"
                  type="text"
                  placeholder="Selesai (00:00:30)"
                  class="rounded-xl border bg-slate-900/70 px-3 py-2 text-sm text-white"
                  :class="getRangeError(range) ? 'border-rose-300/70' : 'border-white/10'"
                />
                <button
                  v-if="form.ranges.length > 1"
                  type="button"
                  class="justify-self-start text-xs text-rose-300 sm:justify-self-auto"
                  @click="removeRange(index)"
                >
                  Hapus
                </button>
              </div>
              <p v-if="getRangeError(range)" class="text-xs font-semibold text-rose-300">
                {{ getRangeError(range) }}
              </p>
            </div>
          </div>
          <p class="mt-2 text-xs text-slate-400">Format wajib HH:MM:SS, dan waktu selesai harus lebih besar dari mulai.</p>
        </div>

        <div>
          <label class="text-sm font-medium text-slate-200">Maksimum clip diproses</label>
          <div class="mt-2 flex items-center gap-3">
            <input
              v-model.number="form.max_clips"
              type="number"
              min="1"
              max="10"
              class="w-32 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-white"
            />
            <span class="text-xs text-slate-400">Maksimal 10 clip per job</span>
          </div>
          <p v-if="form.max_clips > 10" class="mt-2 text-xs font-semibold text-amber-300">
            Maksimum clip hanya 10. Turunkan nilainya untuk melanjutkan.
          </p>
        </div>

        <!-- This part should be hidden because it is correct, should be use stream mode -->
        <div v-if="false">
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

        <div v-if="false">
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

        <div v-if="false">
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
        <div class="rounded-2xl border border-emerald-300/30 bg-emerald-500/5 p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-emerald-200">SRT terpisah untuk aplikasi lain(capcut)</p>
              <p class="text-xs text-emerald-100/80">Saat ON: video tanpa caption, tapi file .srt tetap dibuat.</p>
            </div>
            <label class="inline-flex cursor-pointer items-center gap-2">
              <input
                v-model="form.generate_srt"
                type="checkbox"
                class="peer sr-only"
              />
              <span class="relative h-6 w-11 rounded-full bg-slate-700/90 transition-colors duration-200 peer-checked:bg-emerald-400 peer-checked:shadow-[0_0_16px_rgba(74,222,128,0.85)] after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow after:transition-transform after:duration-200 after:content-[''] peer-checked:after:translate-x-5"></span>
              <span class="text-xs font-semibold" :class="form.generate_srt ? 'text-emerald-300' : 'text-slate-400'">
                {{ form.generate_srt ? 'ON' : 'OFF' }}
              </span>
            </label>
          </div>
        </div>

        <div class="mt-3 space-y-3" :class="!burnSubtitlesEnabled ? 'opacity-50' : ''">
          <div class="flex items-center justify-between">
            <span class="text-xs text-slate-400">Style subtitle (font + ukuran)</span>
            <label class="inline-flex cursor-pointer items-center gap-2">
              <input
                v-model="form.subtitle_style_enabled"
                :disabled="!burnSubtitlesEnabled"
                type="checkbox"
                class="peer sr-only"
              />
              <span class="relative h-6 w-11 rounded-full bg-slate-700/90 transition-colors duration-200 peer-checked:bg-emerald-400 peer-checked:shadow-[0_0_14px_rgba(74,222,128,0.75)] after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow after:transition-transform after:duration-200 after:content-[''] peer-checked:after:translate-x-5"></span>
              <span class="text-xs font-semibold" :class="form.subtitle_style_enabled ? 'text-emerald-300' : 'text-slate-400'">
                {{ form.subtitle_style_enabled ? 'ON' : 'OFF' }}
              </span>
            </label>
          </div>
          <div v-if="form.subtitle_style_enabled && burnSubtitlesEnabled" class="grid gap-3 md:grid-cols-2">
            <div>
              <span class="text-xs text-slate-400">Font subtitle</span>
              <select
                v-model="form.subtitle_font"
                :disabled="!burnSubtitlesEnabled"
                class="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white"
              >
                <option value="Arial">Arial</option>
                <option value="Roboto">Roboto</option>
                <option value="Noto Sans">Noto Sans</option>
                <option value="Helvetica">Helvetica</option>
                <option value="Verdana">Verdana</option>
              </select>
            </div>
            <div>
              <span class="text-xs text-slate-400">Ukuran subtitle</span>
              <input
                v-model.number="form.subtitle_size"
                :disabled="!burnSubtitlesEnabled"
                type="number"
                min="10"
                max="72"
                class="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-white"
              />
            </div>
          </div>
        </div>

        <button
          class="mt-2 w-full rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5"
          type="button"
          @click="submitJob"
          :disabled="loading || isMaxClipsInvalid || hasRangeValidationError"
        >
          {{ loading ? 'Mengirim...' : 'Jalankan Job' }}
        </button>

        <p v-if="error" class="text-sm font-semibold text-rose-300">{{ error }}</p>
        <div v-if="activeLimitJobs.length" class="rounded-2xl border border-amber-300/40 bg-amber-500/10 p-4">
          <p class="text-sm font-semibold text-amber-200">Job aktif saat ini (realtime)</p>
          <ul class="mt-3 space-y-3">
            <li v-for="activeJob in activeLimitJobs" :key="activeJob.id" class="space-y-1">
              <div class="flex items-center justify-between text-xs text-amber-100/90">
                <span class="uppercase tracking-wide">{{ activeJob.status }}</span>
                <span class="font-semibold">{{ activeJob.progress }}%</span>
              </div>
              <div class="h-2 rounded-full bg-slate-800/90">
                <div class="h-2 rounded-full bg-gradient-to-r from-amber-300 to-orange-400" :style="{ width: `${activeJob.progress}%` }"></div>
              </div>
              <p class="text-xs text-amber-100/80">{{ activeJob.message || '-' }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="order-1 glass rounded-3xl p-6 md:p-8 lg:order-2">
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
const FORM_STATE_STORAGE_KEY = 'clipper_form_state_v1'

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
  burn_subtitles: true,
  generate_srt: true,
  auto_captions: true,
  auto_caption_lang: 'id',
  whisper_model: 'small',
  subtitle_primary: 'id',
  subtitle_fallback_enabled: false,
  subtitle_fallback: 'en',
  subtitle_style_enabled: false,
  subtitle_font: 'Arial',
  subtitle_size: 10
})

const restorePersistedFormState = (state) => {
  if (!state || typeof state !== 'object') return
  const simpleFields = [
    'source',
    'youtube_url',
    'local_name',
    'mode',
    'interval_minutes',
    'max_clips',
    'download_sections',
    'orientation',
    'strict_1080',
    'min_height_fallback',
    'burn_subtitles',
    'generate_srt',
    'auto_captions',
    'auto_caption_lang',
    'whisper_model',
    'subtitle_primary',
    'subtitle_fallback_enabled',
    'subtitle_fallback',
    'subtitle_style_enabled',
    'subtitle_font',
    'subtitle_size',
  ]

  for (const key of simpleFields) {
    if (Object.prototype.hasOwnProperty.call(state, key)) {
      form.value[key] = state[key]
    }
  }

  if (Array.isArray(state.ranges) && state.ranges.length > 0) {
    const validRanges = state.ranges
      .filter((item) => item && typeof item.start === 'string' && typeof item.end === 'string')
      .map((item) => ({ start: item.start, end: item.end }))
    if (validRanges.length > 0) {
      form.value.ranges = validRanges
    }
  }
}

const jobId = ref('')
const job = ref(null)
const loading = ref(false)
const error = ref('')
const polling = ref(null)
const progressPoints = ref([])
const activeLimitJobs = ref([])
const activeJobsPolling = ref(null)
const etaNowMs = ref(Date.now())
const etaTicker = ref(null)

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

const burnSubtitlesEnabled = computed(() => form.value.burn_subtitles && !form.value.generate_srt)

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
  const estimate = liveEtaSeconds()
  if (estimate == null || estimate === Infinity) return 'Menghitung...'
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

const parseHmsToSeconds = (value) => {
  const text = String(value || '').trim()
  const match = text.match(/^(\d{1,2}):([0-5]\d):([0-5]\d)$/)
  if (!match) return null
  const hours = Number(match[1])
  const minutes = Number(match[2])
  const seconds = Number(match[3])
  return (hours * 3600) + (minutes * 60) + seconds
}

const getRangeError = (range) => {
  const startSeconds = parseHmsToSeconds(range.start)
  const endSeconds = parseHmsToSeconds(range.end)
  if (startSeconds == null || endSeconds == null) {
    return 'Format waktu tidak valid. Gunakan HH:MM:SS.'
  }
  if (endSeconds <= startSeconds) {
    return 'Waktu selesai harus lebih besar dari waktu mulai.'
  }
  return ''
}

const normalizeSubtitleFont = () => {
  if (!form.value.subtitle_style_enabled || !burnSubtitlesEnabled.value) return 'Arial'
  const value = String(form.value.subtitle_font || '').trim()
  return value || 'Arial'
}

const normalizeSubtitleSize = () => {
  if (!form.value.subtitle_style_enabled || !burnSubtitlesEnabled.value) return 28
  const parsed = Number(form.value.subtitle_size)
  if (!Number.isFinite(parsed)) return 20
  return Math.min(72, Math.max(14, Math.round(parsed)))
}

const isMaxClipsInvalid = computed(() => {
  const parsed = Number(form.value.max_clips)
  if (!Number.isFinite(parsed)) return true
  return parsed < 1 || parsed > 10
})

const hasRangeValidationError = computed(() => {
  if (form.value.mode !== 'manual') return false
  return form.value.ranges.some((range) => Boolean(getRangeError(range)))
})

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
  burn_subtitles: burnSubtitlesEnabled.value,
  generate_srt: form.value.generate_srt,
  auto_captions: form.value.auto_captions,
  auto_caption_lang: form.value.auto_caption_lang,
  whisper_model: form.value.whisper_model,
  subtitle_font: normalizeSubtitleFont(),
  subtitle_size: normalizeSubtitleSize(),
  subtitle_langs: (burnSubtitlesEnabled.value || form.value.auto_captions || form.value.generate_srt) ? subtitleLangs.value : []
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
  if (progressPoints.value.length >= 2) {
    const first = progressPoints.value[0]
    const last = progressPoints.value[progressPoints.value.length - 1]
    const deltaProgress = last.progress - first.progress
    const deltaTime = (last.time - first.time) / 1000
    if (deltaProgress > 0 && deltaTime > 0) {
      const rate = deltaProgress / deltaTime
      const remaining = Math.max(0, 100 - last.progress)
      return remaining / rate
    }
  }

  // Fallback: estimate from total progress vs elapsed time since job started.
  const progressNow = Number(job.value?.progress)
  const createdAt = currentJob.value?.created_at || job.value?.created_at
  if (!Number.isFinite(progressNow) || progressNow <= 0 || progressNow >= 100 || !createdAt) {
    return null
  }
  const startMs = new Date(createdAt).getTime()
  if (!Number.isFinite(startMs) || startMs <= 0) return null
  const elapsed = (Date.now() - startMs) / 1000
  if (elapsed <= 1) return null
  const rate = progressNow / elapsed
  if (rate <= 0) return null
  const remaining = Math.max(0, 100 - progressNow)
  return remaining / rate
}

const liveEtaSeconds = () => {
  const estimate = estimateEtaSeconds()
  if (estimate == null || estimate === Infinity) return estimate
  const last = progressPoints.value[progressPoints.value.length - 1]
  if (!last) return estimate
  const elapsed = (etaNowMs.value - last.time) / 1000
  return Math.max(0, estimate - elapsed)
}

const startEtaTicker = () => {
  stopEtaTicker()
  etaNowMs.value = Date.now()
  etaTicker.value = setInterval(() => {
    etaNowMs.value = Date.now()
  }, 1000)
}

const stopEtaTicker = () => {
  if (etaTicker.value) {
    clearInterval(etaTicker.value)
    etaTicker.value = null
  }
}

const startActiveJobsPolling = () => {
  if (!activeLimitJobs.value.length) return
  if (activeJobsPolling.value) return
  activeJobsPolling.value = setInterval(async () => {
    if (!activeLimitJobs.value.length) {
      return
    }
    const refreshed = await Promise.all(
      activeLimitJobs.value.map(async (item) => {
        try {
          const response = await jobAPI.get(item.id)
          return {
            id: item.id,
            status: response.data.status || item.status,
            progress: Math.min(100, Math.max(0, Math.round(response.data.progress || 0))),
            message: response.data.message || '',
          }
        } catch (_) {
          return item
        }
      })
    )
    const stillActive = refreshed.filter((item) => ['queued', 'running'].includes(item.status))
    activeLimitJobs.value = stillActive
    if (!stillActive.length) {
      stopActiveJobsPolling()
    }
  }, 2000)
}

const stopActiveJobsPolling = () => {
  if (activeJobsPolling.value) {
    clearInterval(activeJobsPolling.value)
    activeJobsPolling.value = null
  }
}

const submitJob = async () => {
  error.value = ''
  if (isMaxClipsInvalid.value) {
    error.value = 'Maksimum clip harus di antara 1 sampai 10.'
    return
  }
  if (hasRangeValidationError.value) {
    error.value = 'Periksa range: format harus HH:MM:SS dan waktu selesai harus lebih besar dari mulai.'
    return
  }
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
    activeLimitJobs.value = []
    stopActiveJobsPolling()
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
    recordProgress(0)
    startPolling()
    console.log('🔄 [VideoClipper] Started polling for new job')
  } catch (err) {
    const data = err.response?.data
    if (err.response?.status === 429 && Array.isArray(data?.active_job_details)) {
      activeLimitJobs.value = data.active_job_details.map((item) => ({
        id: item.id,
        status: item.status || 'queued',
        progress: Math.min(100, Math.max(0, Math.round(item.progress || 0))),
        message: item.message || '',
      }))
      startActiveJobsPolling()
    } else {
      activeLimitJobs.value = []
      stopActiveJobsPolling()
    }
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      const firstKey = Object.keys(data)[0]
      const firstVal = data[firstKey]
      if (Array.isArray(firstVal) && firstVal.length > 0) {
        error.value = `${firstKey}: ${firstVal[0]}`
      } else if (typeof firstVal === 'string') {
        error.value = `${firstKey}: ${firstVal}`
      } else {
        error.value = data.detail || data.error || err.message
      }
    } else {
      error.value = err.response?.data?.detail || err.response?.data?.error || err.message
    }
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
    recordProgress(response.data.progress)
    
    jobStorage.saveJob(currentJob.value)
    console.log('💾 [VideoClipper] Job state updated and saved')
    
    if (['done', 'failed', 'canceled'].includes(currentJob.value.status)) {
      console.log('🎉 [VideoClipper] Job reached terminal state, stopping polling')
      stopPolling()
      // Keep successful job in localStorage so user can refresh and still download outputs.
      // Failed/canceled jobs are still cleared to avoid restoring stale error states.
      if (currentJob.value.status !== 'done') {
        jobStorage.clearJob()
      }
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
  startEtaTicker()
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
  stopEtaTicker()
}

onMounted(async () => {
  const savedFormState = sessionStorage.getItem(FORM_STATE_STORAGE_KEY)
  if (savedFormState) {
    try {
      restorePersistedFormState(JSON.parse(savedFormState))
    } catch (_) {
      sessionStorage.removeItem(FORM_STATE_STORAGE_KEY)
    }
  }

  // Backward compatibility for old storage key.
  const savedYoutubeUrl = sessionStorage.getItem(FORM_YOUTUBE_URL_STORAGE_KEY)
  if (savedYoutubeUrl && !form.value.youtube_url) {
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
  form,
  (currentForm) => {
    sessionStorage.setItem(FORM_YOUTUBE_URL_STORAGE_KEY, currentForm.youtube_url || '')
    const persistable = {
      source: currentForm.source,
      youtube_url: currentForm.youtube_url || '',
      local_name: currentForm.local_name || '',
      mode: currentForm.mode,
      interval_minutes: currentForm.interval_minutes,
      ranges: currentForm.ranges,
      max_clips: currentForm.max_clips,
      download_sections: currentForm.download_sections,
      orientation: currentForm.orientation,
      strict_1080: currentForm.strict_1080,
      min_height_fallback: currentForm.min_height_fallback,
      burn_subtitles: currentForm.burn_subtitles,
      generate_srt: currentForm.generate_srt,
      auto_captions: currentForm.auto_captions,
      auto_caption_lang: currentForm.auto_caption_lang,
      whisper_model: currentForm.whisper_model,
      subtitle_primary: currentForm.subtitle_primary,
      subtitle_fallback_enabled: currentForm.subtitle_fallback_enabled,
      subtitle_fallback: currentForm.subtitle_fallback,
      subtitle_style_enabled: currentForm.subtitle_style_enabled,
      subtitle_font: currentForm.subtitle_font,
      subtitle_size: currentForm.subtitle_size,
    }
    sessionStorage.setItem(FORM_STATE_STORAGE_KEY, JSON.stringify(persistable))
  },
  { deep: true }
)

onBeforeUnmount(() => {
  stopPolling()
  stopActiveJobsPolling()
  stopEtaTicker()
})
</script>
