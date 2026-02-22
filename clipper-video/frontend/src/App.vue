<template>
  <div class="min-h-screen">
    <header class="mx-auto max-w-6xl px-6 pt-10">
      <div class="glass rounded-3xl p-8 md:p-12">
        <div class="flex flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <div class="max-w-xl">
            <p class="text-xs uppercase tracking-[0.3em] text-sky-200">YouTube Clipper + Captions</p>
            <h1 class="mt-4 text-3xl font-semibold text-white md:text-5xl">
              Clip cepat, subtitle rapi, semua lokal.
            </h1>
          </div>
          <div class="rounded-2xl border border-white/10 bg-slate-900/70 p-6 text-sm text-slate-200">
            <div class="flex items-center gap-2 text-sky-200">
              <span class="h-2 w-2 rounded-full bg-rose-400"></span>
              <span class="h-2 w-2 rounded-full bg-amber-300"></span>
              <span class="h-2 w-2 rounded-full bg-emerald-300"></span>
            </div>
            <p class="mt-4 text-lg font-semibold text-white">Workflow ringkas</p>
            <p class="mt-4 text-base text-slate-200">
              Masukkan URL YouTube, tentukan mode, dan biarkan worker mengerjakan semuanya,
              <span class="text-orange-300"> lakukan aktivitas yang lain, sementara job sedang berjalan.</span>
            </p>
          </div>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-6 pb-16">
      <router-view />
    </main>

    <footer class="py-8 text-center text-xs text-slate-400">
      Jalankan semuanya lokal: Django + Celery + Redis + Vue.
    </footer>
  </div>
</template>
