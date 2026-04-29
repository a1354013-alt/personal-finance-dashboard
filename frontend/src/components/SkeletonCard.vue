<template>
  <section class="card skeleton-card">
    <div class="skeleton-line skeleton-title" />
    <div class="skeleton-line skeleton-value" />
    <div class="skeleton-line skeleton-meta" />
  </section>
</template>

<style scoped>
.skeleton-card {
  overflow: hidden;
}

.skeleton-line {
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(217, 227, 238, 0.72), rgba(244, 247, 251, 0.96), rgba(217, 227, 238, 0.72));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.skeleton-title {
  width: 45%;
  height: 14px;
  margin-bottom: 16px;
}

.skeleton-value {
  width: 72%;
  height: 28px;
  margin-bottom: 16px;
}

.skeleton-meta {
  width: 55%;
  height: 12px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
