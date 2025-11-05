<template>
  <!-- Full lebar & tinggi dengan background putih -->
  <div class="flex h-screen w-screen relative overflow-hidden bg-white">

    <!-- Background gradient putih dengan aksen biru subtle -->
    <div class="absolute inset-0 bg-gradient-to-br from-white via-blue-50 to-blue-100"></div>
    
    <!-- Animated background elements dalam nuansa biru sangat subtle -->
    <div class="absolute top-10 left-10 w-96 h-96 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-pulse-slow"></div>
    <div class="absolute top-10 right-10 w-96 h-96 bg-blue-50 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow animation-delay-2000"></div>
    <div class="absolute bottom-10 left-1/2 w-96 h-96 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-pulse-slow animation-delay-4000"></div>

    <!-- Main Content Area -->
    <main class="w-full h-full overflow-y-auto relative z-10">
      <div class="min-h-full p-6">
        <!-- Header dengan 3 Logo -->
        <div class="text-center mb-8 fade-in">
          <!-- Container untuk 3 logo sejajar dengan ukuran lebih kecil -->
          <div class="flex items-center justify-center gap-6 mb-6">
            <!-- Logo Kiri -->
            <div class="logo-container logo-left-animated rounded-lg p-3 bg-gradient-to-br from-blue-100 via-blue-150 to-blue-200 shadow-md border border-blue-200">
              <img 
                src="@/assets/logo-left.png" 
                alt="Logo Left"
                class="max-w-xs h-auto rounded"
                style="max-height: 120px;"
              >
            </div>

            <!-- Logo Utama -->
            <div class="logo-container logo-main-animated rounded-lg p-3 bg-gradient-to-br from-blue-100 via-blue-150 to-blue-200 shadow-md border border-blue-200">
              <img 
                src="@/assets/stop-judi-online.png" 
                alt="STOP JUDI ONLINE"
                class="max-w-xs h-auto rounded"
                style="max-height: 120px;"
              >
            </div>

            <!-- Logo Kanan -->
            <div class="logo-container logo-right-animated rounded-lg p-3 bg-gradient-to-br from-blue-100 via-blue-150 to-blue-200 shadow-md border border-blue-200">
              <img 
                src="@/assets/logo-right.png" 
                alt="Logo Right"
                class="max-w-xs h-auto rounded"
                style="max-height: 120px;"
              >
            </div>
          </div>
          
          <!-- Judul Deteksi Iklan Judi Online di Tengah -->
          <h1 class="text-4xl md:text-5xl font-bold text-slate-800 mb-6 text-center">
            Deteksi Iklan Judi Online
          </h1>
          
          <!-- Deskripsi -->
          <p class="text-2xl md:text-3xl font-light text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Sistem Deteksi Cerdas untuk Melindungi dari Konten Perjudian Online
          </p>
        </div>

        <!-- Area Deteksi -->
        <div class="w-full fade-in" style="animation-delay: 0.1s; min-height: 65vh;">
          <router-view />
        </div>

        <!-- Footer -->
        <footer class="mt-12 text-center text-slate-500 text-sm fade-in" style="animation-delay: 0.2s;">
          © 2025 Judol Detector Master - Advanced Gambling Content Protection
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
// Tidak perlu import sidebar
</script>

<style scoped>
.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}

/* Base style untuk semua logo container */
.logo-container {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Animasi untuk logo kiri */
.logo-left-animated {
  animation: left-swing 4s ease-in-out infinite;
}

@keyframes left-swing {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    box-shadow: 0 10px 20px -8px rgba(59, 130, 246, 0.2);
  }
  25% {
    transform: translateY(-3px) rotate(-1deg);
    box-shadow: 0 15px 25px -6px rgba(59, 130, 246, 0.3);
  }
  50% {
    transform: translateY(-1px) rotate(0deg);
  }
  75% {
    transform: translateY(-4px) rotate(1deg);
  }
}

/* Animasi untuk logo utama */
.logo-main-animated {
  animation: main-pulse 3s ease-in-out infinite;
}

@keyframes main-pulse {
  0%, 100% {
    transform: translateY(0px) scale(1);
    box-shadow: 0 10px 20px -8px rgba(59, 130, 246, 0.2);
  }
  50% {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 15px 25px -6px rgba(59, 130, 246, 0.3);
  }
}

/* Animasi untuk logo kanan */
.logo-right-animated {
  animation: right-bounce 5s ease-in-out infinite;
}

@keyframes right-bounce {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    box-shadow: 0 10px 20px -8px rgba(59, 130, 246, 0.2);
  }
  30% {
    transform: translateY(-5px) rotate(2deg);
    box-shadow: 0 15px 25px -6px rgba(59, 130, 246, 0.3);
  }
  60% {
    transform: translateY(-2px) rotate(-1deg);
  }
}

/* Hover effects untuk semua logo */
.logo-container:hover {
  animation-play-state: paused;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 20px 35px -4px rgba(59, 130, 246, 0.4);
}

/* Animasi fade in */
.fade-in {
  animation: fadeIn 0.8s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Custom animation untuk background */
@keyframes pulse-slow {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.4;
  }
}

.animate-pulse-slow {
  animation: pulse-slow 8s ease-in-out infinite;
}
</style>