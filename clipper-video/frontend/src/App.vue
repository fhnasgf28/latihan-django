<template>
  <div class="app-shell">
    <header class="hero">
      <div class="hero-left">
        <p class="hero-kicker">YouTube Clipper + Captions</p>
        <h1>Bikin clip tajam, subtitle nempel, semua lokal.</h1>
        <p class="hero-subtitle">
          Masukkan URL YouTube, pilih mode, dan biarkan worker memotong video + membakar subtitle.
        </p>
      </div>
      <div class="hero-card">
        <div class="hero-card-top">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <div class="hero-card-body">
          <p class="hero-card-title">Local-first workflow</p>
          <ul class="hero-card-list">
            <li>Prefer 1080p, fallback 720p bila perlu</li>
            <li>Auto-split atau manual ranges</li>
            <li>Subtitle official + auto</li>
          </ul>
        </div>
      </div>
    </header>

    <main class="main">
      <router-view />
    </main>

    <footer class="footer">
      <p>Jalankan semuanya lokal: Django + Celery + Redis + Vue.</p>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 32px;
  padding: 40px 48px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(255, 213, 153, 0.75), rgba(158, 216, 250, 0.75));
  box-shadow: 0 24px 60px rgba(17, 24, 39, 0.12);
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.35), transparent 45%),
    radial-gradient(circle at 80% 0%, rgba(255, 255, 255, 0.4), transparent 50%);
  opacity: 0.7;
  pointer-events: none;
}

.hero-left {
  position: relative;
  z-index: 1;
}

.hero-kicker {
  font-family: 'IBM Plex Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  font-size: 12px;
  margin-bottom: 16px;
}

.hero h1 {
  font-size: clamp(28px, 4vw, 44px);
  margin: 0 0 12px;
  line-height: 1.1;
}

.hero-subtitle {
  font-size: 16px;
  max-width: 420px;
  opacity: 0.8;
}

.hero-card {
  background: rgba(16, 24, 40, 0.85);
  color: #fff7ec;
  border-radius: 20px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.hero-card-top {
  display: flex;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ffbfa3;
}

.dot:nth-child(2) {
  background: #ffe28a;
}

.dot:nth-child(3) {
  background: #8be0ff;
}

.hero-card-title {
  font-weight: 600;
  margin: 0;
  font-size: 18px;
}

.hero-card-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.6;
}

.main {
  flex: 1;
}

.footer {
  text-align: center;
  font-size: 13px;
  opacity: 0.6;
  padding-bottom: 24px;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
  }
}
</style>
