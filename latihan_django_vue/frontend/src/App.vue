<script setup>
import HelloWorld from './components/HelloWorld.vue'
import { ref, onMounted } from 'vue'
import axios from 'axios'
const notes = ref([]);
const title = ref("");
const loading = ref(false);
const error = ref("");

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

onMounted(() => {
  fetchNotes().catch((e) => {
    error.value = e.message || "Terjadi Error";
  });
})
</script>

<template>
  <main style="max-width: 720px; margin: 24px auto; font-family: Arial;">
    <h1>Latihan Django + Vue: Notes</h1>
    <form @submit.prevent="addNote" style="display: flex; gap: 8px; margin: 16px 0;">
      <input
        v-model="title"
        placeholder="Tulis note..."
        style="flex: 1; padding: 10px;"
      />
      <button :disabled="loading" style="padding: 10px 14px;">
        {{ loading ? "Loading..." : "Tambah" }}
      </button>
    </form>
    <p v-if="error" style="color: red;">{{ error }}}</p>
    <ul style="padding-left: 18px;">
      <li v-for="note in notes" :key="note.id">
        {{ note.title}} <small> ({{ formatDate(note.created_at) }}})</small>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
