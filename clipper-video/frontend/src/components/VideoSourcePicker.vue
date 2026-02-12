<template>
  <div class="rounded-3xl border border-white/10 bg-slate-900/50 p-4">
    <div class="flex items-center justify-between">
      <p class="text-sm font-semibold text-white">Sumber Video</p>
      <span class="text-xs text-slate-400">Local lebih cepat</span>
    </div>

    <div class="mt-3 inline-flex rounded-full bg-slate-900/80 p-1">
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm"
        :class="modelValue.source === 'youtube' ? 'bg-white text-slate-900' : 'text-slate-300'"
        @click="setSource('youtube')"
      >
        YouTube Link
      </button>
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm"
        :class="modelValue.source === 'local' ? 'bg-white text-slate-900' : 'text-slate-300'"
        @click="setSource('local')"
      >
        File Komputer
      </button>
    </div>

    <div v-if="modelValue.source === 'youtube'" class="mt-4">
      <label class="text-sm font-medium text-slate-200">URL YouTube</label>
      <input
        :value="modelValue.youtube_url"
        type="text"
        placeholder="https://www.youtube.com/watch?v=..."
        class="mt-2 w-full rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-white placeholder:text-slate-500"
        @input="$emit('update:modelValue', { ...modelValue, youtube_url: $event.target.value })"
      />
    </div>

    <div v-else class="mt-4">
      <label class="text-sm font-medium text-slate-200">Pilih file video</label>
      <input
        type="file"
        accept="video/*"
        class="mt-2 w-full rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-200 file:mr-4 file:rounded-xl file:border-0 file:bg-white file:px-3 file:py-2 file:text-sm file:font-semibold file:text-slate-900"
        @change="onFileChange"
      />
      <p v-if="modelValue.local_name" class="mt-2 text-xs text-slate-400">{{ modelValue.local_name }}</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const setSource = (source) => {
  emit('update:modelValue', { ...props.modelValue, source })
}

const onFileChange = (event) => {
  const file = event.target.files?.[0] || null
  emit('update:modelValue', {
    ...props.modelValue,
    local_file: file,
    local_name: file?.name || ''
  })
}
</script>
