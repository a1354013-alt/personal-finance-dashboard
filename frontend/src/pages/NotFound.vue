<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>Page Not Found</h2>
      <p class="auth-subtitle">The page you are looking for does not exist or has moved.</p>
      <router-link class="btn btn-primary auth-submit" to="/">Back to Dashboard</router-link>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
}

.auth-card {
  width: 100%;
  max-width: 520px;
  padding: 30px;
  text-align: center;
}

.auth-subtitle {
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.auth-submit {
  text-decoration: none;
}
</style>
