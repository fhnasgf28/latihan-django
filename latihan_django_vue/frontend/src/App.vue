<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const notes = ref([]);
const title = ref("");
const loading = ref(false);
const error = ref("");

const youtubeUrl = ref("");
const downloadLoading = ref(false);
const downloadError = ref("");

async function fetchNotes() {
  error.value = ""
  const res = await fetch("/api/notes/");
  if (!res.ok) throw new Error("Gagal ambil data");
  notes.value = await res.json();
}

async function addNote() {
  const t = title.value.trim()
  if (!t) return;

  loading.value = true;
  error.value = "";
  try {
    const res = await fetch("/api/notes/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: t }),
    })
    if (!res.ok) throw new Error("Gagal tambah note");
    title.value = "";
    await fetchNotes();
  } catch (e) {
    error.value = e.message || "Terjadi Error";
  } finally {
    loading.value = false;
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString();
}

function isValidYoutubeUrl(url) {
  const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/i;
  return pattern.test(url);
}

function getFilenameFromDisposition(disposition) {
  if (!disposition) return null;
  const match = /filename="([^"]+)"/i.exec(disposition);
  return match ? match[1] : null;
}

async function downloadYoutube() {
  const url = youtubeUrl.value.trim();
  downloadError.value = "";

  if (!url) {
    downloadError.value = "URL wajib diisi.";
    return;
  }
  if (!isValidYoutubeUrl(url)) {
    downloadError.value = "URL YouTube tidak valid. Contoh: https://www.youtube.com/watch?v=...";
    return;
  }

  downloadLoading.value = true;
  try {
    const res = await axios.post(
      "/api/youtube/download/",
      { url },
      { responseType: "blob" }
    );

    const blob = new Blob([res.data], { type: "video/mp4" });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const filename = getFilenameFromDisposition(res.headers["content-disposition"]);
    link.href = downloadUrl;
    link.download = filename || "youtube-video.mp4";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  } catch (e) {
    downloadError.value = e?.response?.data?.detail || "Gagal download video. Coba lagi.";
  } finally {
    downloadLoading.value = false;
  }
}

onMounted(() => {
  fetchNotes().catch((e) => {
    error.value = e.message || "Terjadi Error";
  });
})
</script>

<template>
  <main class="app-shell">
    <div class="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-5 py-10 lg:px-10">
      <header class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div class="space-y-3">
          <p class="inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-ink shadow-soft">
            <span class="h-2 w-2 rounded-full bg-moss"></span>
            Django + Vue Studio
          </p>
          <h1 class="font-display text-3xl font-semibold text-ink sm:text-4xl">
            YouTube Downloader + Notes
          </h1>
          <p class="max-w-2xl text-sm text-slate-600 sm:text-base">
            Tempat sederhana untuk menyimpan catatan singkat dan mengunduh video YouTube
            dengan sekali tempel link.
          </p>
        </div>
        <div class="flex flex-wrap gap-3 text-sm text-slate-600">
          <div class="rounded-2xl bg-white/80 px-4 py-3 shadow-soft">
            <p class="font-semibold text-ink">Aman untuk belajar</p>
            <p class="text-xs text-slate-500">Gunakan konten yang kamu miliki haknya</p>
          </div>
          <div class="rounded-2xl bg-white/80 px-4 py-3 shadow-soft">
            <p class="font-semibold text-ink">Cepat &amp; rapi</p>
            <p class="text-xs text-slate-500">Desain fokus produktivitas</p>
          </div>
        </div>
      </header>

      <section class="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div class="card-glass flex flex-col gap-6 rounded-3xl p-6 sm:p-8">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="font-display text-xl font-semibold text-ink">Notes</h2>
              <p class="text-sm text-slate-500">Simpan ide cepat untuk proyek ini.</p>
            </div>
            <span class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
              {{ notes.length }} item
            </span>
          </div>

          <form @submit.prevent="addNote" class="flex flex-col gap-3 sm:flex-row">
            <input
              v-model="title"
              placeholder="Tulis note..."
              class="w-full flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink shadow-sm outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100"
            />
            <button
              :disabled="loading"
              class="rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-emerald-300"
            >
              {{ loading ? "Menyimpan..." : "Tambah" }}
            </button>
          </form>

          <div v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {{ error }}
          </div>

          <div class="space-y-3">
            <div v-if="notes.length === 0" class="rounded-2xl border border-dashed border-slate-200 bg-white/60 px-4 py-6 text-center text-sm text-slate-500">
              Belum ada notes. Tambahkan ide pertama kamu.
            </div>
            <ul v-else class="space-y-3">
              <li
                v-for="note in notes"
                :key="note.id"
                class="rounded-2xl border border-slate-100 bg-white px-4 py-4 shadow-sm"
              >
                <p class="text-sm font-semibold text-ink">{{ note.title }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ formatDate(note.created_at) }}</p>
              </li>
            </ul>
          </div>
        </div>

        <div class="card-glass flex flex-col gap-6 rounded-3xl p-6 sm:p-8">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="font-display text-xl font-semibold text-ink">Download YouTube</h2>
              <p class="text-sm text-slate-500">Tempel link video, langsung download.</p>
            </div>
            <span class="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-700">
              MP4
            </span>
          </div>

          <form @submit.prevent="downloadYoutube" class="space-y-4">
            <div class="space-y-2">
              <label class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                URL Video
              </label>
              <input
                v-model="youtubeUrl"
                placeholder="https://www.youtube.com/watch?v=..."
                class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
              />
              <div class="flex flex-wrap gap-2 text-xs text-slate-500">
                <span class="rounded-full bg-slate-100 px-3 py-1">youtube.com</span>
                <span class="rounded-full bg-slate-100 px-3 py-1">youtu.be</span>
                <span class="rounded-full bg-slate-100 px-3 py-1">Link langsung</span>
              </div>
            </div>
            <button
              :disabled="downloadLoading"
              class="w-full rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-600"
            >
              {{ downloadLoading ? "Mengunduh..." : "Download Video" }}
            </button>
          </form>

          <div v-if="downloadError" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {{ downloadError }}
          </div>

          <div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
            Tips: pastikan kamu punya izin untuk mengunduh video tersebut.
          </div>
        </div>
      </section>

      <footer class="flex flex-wrap items-center justify-between gap-3 rounded-3xl bg-white/80 px-6 py-4 text-xs text-slate-500 shadow-soft">
        <p>Backend: Django REST • Frontend: Vue + Tailwind</p>
        <p>Latency: lokal • Status: siap dipakai</p>
      </footer>
    </div>
  </main>
</template>
