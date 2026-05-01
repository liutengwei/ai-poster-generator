<script setup lang="ts">
import { RouterLink } from 'vue-router'
import InputForm from '@/components/InputForm.vue'
import PreviewPanel from '@/components/PreviewPanel.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col page-enter">
    <!-- Navigation Bar -->
    <header class="navbar glass">
      <div class="navbar-content">
        <div class="logo animate-fade-in-up stagger-1">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="logo-text">AI 宣传助手</span>
        </div>
        <nav class="nav-links animate-fade-in-up stagger-2">
          <RouterLink to="/" class="nav-link active">创作</RouterLink>
          <RouterLink to="/history" class="nav-link">历史记录</RouterLink>
        </nav>
      </div>
      <div class="navbar-divider"></div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="split-view">
        <!-- Left Panel - Form -->
        <div class="left-panel animate-fade-in-up stagger-3">
          <InputForm />
        </div>

        <!-- Divider -->
        <div class="divider"></div>

        <!-- Right Panel - Preview -->
        <div class="right-panel animate-fade-in-up stagger-4">
          <PreviewPanel />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page-enter {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: #6366f1;
  filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.4));
}

.logo-text {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 600;
  color: #f3f4f6;
  letter-spacing: 1px;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #9ca3af;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #f3f4f6;
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  color: #6366f1;
  background: rgba(99, 102, 241, 0.12);
}

.navbar-divider {
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(99, 102, 241, 0.4) 20%,
    rgba(168, 85, 247, 0.4) 50%,
    rgba(236, 72, 153, 0.4) 80%,
    transparent 100%
  );
}

.main-content {
  flex: 1;
  padding: 32px 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.split-view {
  display: flex;
  height: calc(100vh - 140px);
  gap: 0;
}

.left-panel {
  width: 40%;
  overflow-y: auto;
  padding-right: 32px;
}

.divider {
  width: 1px;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.06) 20%,
    rgba(255, 255, 255, 0.06) 80%,
    transparent 100%
  );
  margin: 0 24px;
}

.right-panel {
  width: 60%;
  position: relative;
  overflow: hidden;
}

.right-panel::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 700px;
  height: 700px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

@media (max-width: 1024px) {
  .split-view {
    flex-direction: column;
    height: auto;
  }

  .left-panel {
    width: 100%;
    padding-right: 0;
    padding-bottom: 32px;
  }

  .divider {
    width: 100%;
    height: 1px;
    margin: 0 0 32px 0;
  }

  .right-panel {
    width: 100%;
    min-height: 500px;
  }
}
</style>
