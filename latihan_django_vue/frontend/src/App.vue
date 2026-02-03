<script setup>
import { ref } from 'vue'
import axios from 'axios'

const youtubeUrl = ref("");
const downloadLoading = ref(false);
const downloadError = ref("");

function isValidYoutubeUrl(url) {
  const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/i;
  return pattern.test(url);
}

function getFilenameFromDisposition(disposition) {
  if (!disposition) return null;
  let match = /filename="([^"]+)"/i.exec(disposition);
  if (match && match[1]) return match[1];
  match = /filename=([^;]+)/i.exec(disposition);
  if (match && match[1]) return match[1].trim();
  return null;
}

async function downloadDirect(type) {
  const url = youtubeUrl.value.trim();
  downloadError.value = "";

  if (!url) {
    downloadError.value = "URL wajib diisi.";
    return;
  }
  if (!isValidYoutubeUrl(url)) {
    downloadError.value = "URL YouTube tidak valid.";
    return;
  }

  downloadLoading.value = true;
  try {
    const res = await axios.post(
      "/api/youtube/download/",
      { url, type }, // type: 'video' | 'audio'
      { responseType: "blob" }
    );

    const isAudio = type === 'audio';
    const contentType = res.headers["content-type"] || (isAudio ? "audio/mpeg" : "video/mp4");
    const blob = new Blob([res.data], { type: contentType });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const filename = getFilenameFromDisposition(res.headers["content-disposition"]);
    link.href = downloadUrl;
    link.download = filename || (isAudio ? "audio.mp3" : "video.mp4");
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  } catch (e) {
    if (e.response && e.response.data instanceof Blob) {
      try {
        const text = await e.response.data.text();
        const json = JSON.parse(text);
        downloadError.value = json.detail || "Gagal download.";
      } catch (inner) {
        downloadError.value = "Gagal download. Terjadi kesalahan server.";
      }
    } else {
      downloadError.value = e?.response?.data?.detail || "Gagal download. Coba lagi.";
    }
  } finally {
    downloadLoading.value = false;
  }
}
</script>

<template>
  <main class="app-shell">
    <div class="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-10 px-5 py-10 lg:px-10">
      <header class="text-center space-y-4">
        <p class="inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-ink shadow-soft">
          <span class="h-2 w-2 rounded-full bg-moss"></span>
          Django + Vue Studio
        </p>
        <h1 class="font-display text-4xl font-semibold text-ink sm:text-5xl">
          YouTube Downloader
        </h1>
        <p class="mx-auto max-w-lg text-slate-600">
          Unduh video atau audio dari YouTube dengan mudah. Tempel link, pilih format, selesai.
        </p>
      </header>

      <section>
        <!-- YouTube Downloader Section -->
        <div class="card-glass flex flex-col gap-8 rounded-3xl p-8 sm:p-10 shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 pb-6">
            <div>
              <h2 class="font-display text-xl font-semibold text-ink">Download</h2>
              <p class="text-sm text-slate-500">Pilih format yang diinginkan.</p>
            </div>
            <span class="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-700">
              MP4 / MP3
            </span>
          </div>

          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                URL Video
              </label>
              <input
                v-model="youtubeUrl"
                placeholder="https://www.youtube.com/watch?v=..."
                class="w-full rounded-2xl border border-slate-200 bg-white px-5 py-4 text-base text-ink shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <button
                @click="downloadDirect('video')"
                :disabled="downloadLoading"
                class="flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-4 py-4 text-sm font-semibold text-white shadow-soft transition hover:bg-slate-800 disabled:bg-slate-600 hover:-translate-y-0.5"
              >
                <span v-if="downloadLoading">Memproses...</span>
                <span v-else>Download MP4</span>
              </button>

              <button
                @click="downloadDirect('audio')"
                :disabled="downloadLoading"
                class="flex items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 py-4 text-sm font-semibold text-white shadow-soft transition hover:bg-emerald-700 disabled:bg-emerald-400 hover:-translate-y-0.5"
              >
                <span v-if="downloadLoading">Memproses...</span>
                <span v-else>Download MP3</span>
              </button>
            </div>

            <div v-if="downloadLoading" class="animate-pulse rounded-2xl border border-sky-200 bg-sky-50 px-4 py-4 text-center text-sm text-sky-700">
              Sedang mengunduh & memproses media... Mohon tunggu sebentar.
            </div>

            <div v-if="downloadError" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
              {{ downloadError }}
            </div>
          </div>
        </div>
      </section>

      <footer class="text-center text-xs text-slate-500">
        <p>Backend: Django REST • Frontend: Vue + Tailwind</p>
      </footer>
    </div>
  </main>
</template>
