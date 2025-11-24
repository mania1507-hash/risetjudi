<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

// ===== Base URL Backend Flask =====
const BASE_URL = "https://nonsinkable-ulnar-staci.ngrok-free.dev"

// ===== State =====
const selectedInputType = ref('text')
const inputText = ref('')
const inputUrl = ref('')
const youtubeUrl = ref('')
const result = ref(null)
const imageFile = ref(null)
const videoFile = ref(null)
const imagePreview = ref(null)
const isDetec = ref(false)
const textInput = ref(null)
const fileInputImage = ref(null)
const fileInputVideo = ref(null)

// ===== Methods =====
const resetAllInputs = () => {
  // Reset semua input values
  inputText.value = ''
  inputUrl.value = ''
  youtubeUrl.value = ''
  imageFile.value = null
  videoFile.value = null
  imagePreview.value = null
  result.value = null
  isDetec.value = false

  // Reset file inputs
  if (fileInputImage.value) {
    fileInputImage.value.value = ''
  }
  if (fileInputVideo.value) {
    fileInputVideo.value.value = ''
  }
}

const resetDetectionResult = () => {
  result.value = null
  isDetec.value = false
}

const handleImageUpload = (e) => {
  const file = e.target.files[0]
  if (file) {
    imageFile.value = file
    imagePreview.value = URL.createObjectURL(file)
    resetDetectionResult() // Reset hasil saat upload file baru
  }
}

const clearImagePreview = () => {
  imageFile.value = null
  imagePreview.value = null
  if (fileInputImage.value) {
    fileInputImage.value.value = ''
  }
  resetDetectionResult()
}

const focusTextInput = () => {
  nextTick(() => {
    textInput.value?.focus()
  })
}

const changeInputType = (type) => {
  // Reset semua input dan hasil ketika berpindah tab
  resetAllInputs()
  selectedInputType.value = type
  if (type === 'text') {
    nextTick(() => focusTextInput())
  }
}

onMounted(() => {
  if (selectedInputType.value === 'text') focusTextInput()
})

const handleVideoUpload = (e) => {
  const file = e.target.files[0]
  if (!file) return
  videoFile.value = file
  resetDetectionResult() // Reset hasil saat upload file baru
}

const clearVideoFile = () => {
  videoFile.value = null
  if (fileInputVideo.value) {
    fileInputVideo.value.value = ''
  }
  resetDetectionResult()
}

// Fungsi untuk validasi URL YouTube
const isValidYoutubeUrl = (url) => {
  const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})(\S*)?$/
  return youtubeRegex.test(url)
}

// Fungsi untuk menangani paste dari clipboard
const handlePasteYoutubeUrl = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (isValidYoutubeUrl(text)) {
      youtubeUrl.value = text
      resetDetectionResult() // Reset hasil saat paste URL baru
      toast.success('URL YouTube berhasil dipaste!')
    } else {
      toast.error('URL YouTube tidak valid!')
    }
  } catch (err) {
    console.error('Gagal membaca clipboard:', err)
    toast.error('Gagal membaca clipboard')
  }
}

// Fungsi untuk membersihkan URL YouTube
const clearYoutubeUrl = () => {
  youtubeUrl.value = ''
  resetDetectionResult()
}

// Fungsi untuk membersihkan input teks
const clearTextInput = () => {
  inputText.value = ''
  resetDetectionResult()
  focusTextInput()
}

// Fungsi untuk membersihkan input URL
const clearUrlInput = () => {
  inputUrl.value = ''
  resetDetectionResult()
}

const handleDetect = async () => {
  const toastLoading = toast.loading('Sedang memproses...')
  result.value = null
  isDetec.value = true

  try {
    let res

    // ==== MODE TEKS ====
    if (selectedInputType.value === 'text') {
      if (!inputText.value.trim()) {
        toast.error('Masukkan teks terlebih dahulu.')
        return
      }
      res = await fetch(`${BASE_URL}/api/detect-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText.value }),
      })
    }

    // ==== MODE URL ====
    else if (selectedInputType.value === 'url') {
      if (!inputUrl.value.trim()) {
        toast.error('Masukkan URL terlebih dahulu.')
        return
      }
      res = await fetch(`${BASE_URL}/api/detect-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: inputUrl.value }),
      })
    }

    // ==== MODE GAMBAR ====
    else if (selectedInputType.value === 'image') {
      if (!imageFile.value) {
        toast.error('Pilih gambar terlebih dahulu.')
        return
      }
      const formData = new FormData()
      formData.append('image', imageFile.value)
      res = await fetch(`${BASE_URL}/api/detect-image`, { method: 'POST', body: formData })
    }

    // ==== MODE VIDEO ====
    else if (selectedInputType.value === 'video') {
      if (!videoFile.value && !youtubeUrl.value.trim()) {
        toast.error('Pilih video file atau masukkan URL YouTube terlebih dahulu.')
        return
      }
      
      const formData = new FormData()
      
      if (videoFile.value) {
        // Upload video file
        formData.append('video', videoFile.value)
        res = await fetch(`${BASE_URL}/api/detect-video`, { method: 'POST', body: formData })
      } else if (youtubeUrl.value.trim()) {
        // Gunakan URL YouTube
        if (!isValidYoutubeUrl(youtubeUrl.value)) {
          toast.error('URL YouTube tidak valid!')
          return
        }
        res = await fetch(`${BASE_URL}/api/detect-youtube`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ youtube_url: youtubeUrl.value }),
        })
      }
    }

    if (!res.ok) throw new Error(`Server error (${res.status})`)

    const data = await res.json()
    result.value = data

    if (data.success || data.status) {
      toast.success('Deteksi selesai.')
    } else {
      toast.error(data.error || 'Terjadi kesalahan di server.')
    }
  } catch (err) {
    console.error(err)
    toast.error('Gagal mengambil data dari server.')
  } finally {
    isDetec.value = false
    toast.remove(toastLoading)
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
    <div class="max-w-3xl mx-auto">
      <div class="text-center mb-8">
      </div>

      <!-- ====== Input Card ====== -->
      <div class="bg-white/90 shadow-xl backdrop-blur-md rounded-2xl p-6 transition hover:shadow-2xl">
        <div class="text-xl font-semibold text-blue-800 mb-4 border-b pb-2">
          Pilih Jenis Input
        </div>

        <!-- Tabs -->
        <div class="flex flex-wrap gap-2 justify-center mb-6">
          <button
            v-for="type in ['text', 'url', 'image', 'video']"
            :key="type"
            @click="() => changeInputType(type)"
            class="px-4 py-2 font-semibold rounded-full border-2 border-blue-700 transition-all duration-200"
            :class="selectedInputType === type
              ? 'bg-blue-700 text-white shadow-md scale-105'
              : 'bg-white text-blue-700 hover:bg-blue-700 hover:text-white'"
          >
            {{ type === 'text' ? 'Teks' : type === 'url' ? 'URL Web' : type === 'image' ? 'Gambar' : 'Video' }}
          </button>
        </div>

        <!-- Input Area -->
        <div v-if="selectedInputType === 'text'" class="flex flex-col gap-4">
          <div class="relative">
            <textarea
              ref="textInput"
              v-model="inputText"
              rows="4"
              placeholder="Masukkan teks untuk deteksi"
              class="border-2 border-blue-200 rounded-xl p-3 w-full focus:ring-2 focus:ring-blue-400 transition pr-10"
              @keydown.enter.exact.prevent="handleDetect"
            ></textarea>
            <button
              v-if="inputText"
              @click="clearTextInput"
              class="absolute right-3 top-3 text-gray-500 hover:text-red-500 transition"
              title="Hapus teks"
            >
              ❌
            </button>
          </div>
        </div>

        <div v-if="selectedInputType === 'url'" class="flex flex-col gap-4">
          <div class="relative">
            <input
              v-model="inputUrl"
              type="text"
              placeholder="Masukkan URL (contoh: https://example.com)"
              class="border-2 border-blue-200 rounded-xl p-3 w-full focus:ring-2 focus:ring-blue-400 transition pr-10"
              @keydown.enter="handleDetect"
            />
            <button
              v-if="inputUrl"
              @click="clearUrlInput"
              class="absolute right-3 top-3 text-gray-500 hover:text-red-500 transition"
              title="Hapus URL"
            >
              ❌
            </button>
          </div>
        </div>

        <div v-if="selectedInputType === 'image'" class="flex flex-col gap-4">
          <div class="flex gap-2">
            <input
              ref="fileInputImage"
              type="file"
              @change="handleImageUpload"
              accept="image/*"
              class="border-2 border-blue-200 rounded-xl p-2 w-full bg-gray-50 hover:bg-gray-100 transition"
            />
            <button
              v-if="imageFile"
              @click="clearImagePreview"
              class="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition whitespace-nowrap"
            >
              Hapus Gambar
            </button>
          </div>
          <div v-if="imagePreview" class="mt-3 text-center">
            <div class="relative inline-block">
              <img :src="imagePreview" class="max-h-64 mx-auto rounded-xl shadow-md border" />
              <button
                @click="clearImagePreview"
                class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600 transition"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div v-if="selectedInputType === 'video'" class="flex flex-col gap-4">
          <!-- Opsi 1: Upload File Video -->
          <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Upload File Video</label>
            <div class="flex gap-2">
              <input
                ref="fileInputVideo"
                type="file"
                accept="video/*"
                @change="handleVideoUpload"
                class="border-2 border-blue-200 rounded-xl p-2 w-full bg-gray-50 hover:bg-gray-100 transition"
              />
              <button
                v-if="videoFile"
                @click="clearVideoFile"
                class="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition whitespace-nowrap"
              >
                Hapus Video
              </button>
            </div>
          </div>

          <!-- Pembatas "ATAU" -->
          <div class="flex items-center my-4">
            <div class="flex-1 border-t border-gray-300"></div>
            <div class="px-3 text-sm text-gray-500 font-medium">ATAU</div>
            <div class="flex-1 border-t border-gray-300"></div>
          </div>

          <!-- Opsi 2: URL YouTube -->
          <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">URL YouTube</label>
            <div class="flex gap-2">
              <input
                v-model="youtubeUrl"
                type="text"
                placeholder="Tempel URL YouTube di sini (contoh: https://youtube.com/watch?v=...)"
                class="flex-1 border-2 border-blue-200 rounded-xl p-3 focus:ring-2 focus:ring-blue-400 transition"
                @keydown.enter="handleDetect"
              />
              <button
                @click="handlePasteYoutubeUrl"
                class="px-4 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition flex items-center gap-2 whitespace-nowrap"
                title="Paste dari clipboard"
              >
                📋 Paste
              </button>
              <button
                v-if="youtubeUrl"
                @click="clearYoutubeUrl"
                class="px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 transition flex items-center gap-2 whitespace-nowrap"
                title="Hapus URL"
              >
                ❌ Hapus
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              Format yang didukung: youtube.com/watch?v=... atau youtu.be/...
            </p>
          </div>
        </div>

        <!-- Tombol Deteksi -->
        <div class="flex justify-center mt-6">
          <button
            :disabled="isDetec"
            @click="handleDetect"
            class="flex items-center gap-2 px-6 py-2 font-bold text-white rounded-full bg-blue-700 hover:bg-blue-800 transition transform hover:scale-105 shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <svg
              v-if="isDetec"
              class="animate-spin h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>{{ isDetec ? 'Sedang Memproses...' : '🚀 Deteksi Sekarang' }}</span>
          </button>
        </div>
      </div>

      <!-- ===== Hasil Deteksi ===== -->
      <div v-if="result" class="mt-10 bg-white rounded-2xl shadow-xl p-6 border border-blue-100">
        <div class="text-2xl font-bold text-blue-800 mb-4 flex items-center gap-2">
          <span>📊 Hasil Deteksi</span>
          <button
            @click="resetDetectionResult"
            class="ml-auto text-sm bg-gray-500 text-white px-3 py-1 rounded-lg hover:bg-gray-600 transition"
          >
            ✕ Tutup Hasil
          </button>
        </div>

        <div class="space-y-4 text-gray-700">
          <div class="flex items-center gap-2">
            <div class="font-semibold text-lg">Status :</div>
            <div
              class="text-lg font-bold"
              :class="result.raw_confidence > 0.5 ? 'text-red-600' : 'text-green-600'"
            >
              {{ result.status || (result.raw_confidence > 0.5 ? '❌ Terindikasi Iklan Judi' : '✔️ Tidak Terindikasi Iklan Judi') }}
            </div>
          </div>

          <div class="flex items-center gap-2">
            <div class="font-semibold text-lg">Persentase :</div>
            <div class="text-lg font-bold">{{ result.confidence }}</div>
          </div>

          <div v-if="result.gambling_keywords?.length">
            <div class="font-semibold text-lg mb-1">Kata Kunci Ditemukan:</div>
            <ul class="list-disc list-inside text-red-600 font-medium">
              <li v-for="(kw, index) in result.gambling_keywords" :key="index">{{ kw }}</li>
            </ul>
          </div>

          <div v-if="result.source_url" class="text-sm">
            <b>Sumber URL:</b>
            <a :href="result.source_url" target="_blank" class="text-blue-600 underline">
              {{ result.source_url }}
            </a>
          </div>

          <div v-if="result.youtube_url" class="text-sm">
            <b>URL YouTube:</b>
            <a :href="result.youtube_url" target="_blank" class="text-blue-600 underline">
              {{ result.youtube_url }}
            </a>
          </div>

          <div v-if="result.ocr_text" class="mt-4">
            <div class="text-sm">
              <b>Teks yang Diekstrak:</b>
              <div class="mt-2 p-3 bg-gray-100 rounded-lg max-h-40 overflow-y-auto border border-gray-200">
                {{ result.ocr_text }}
              </div>
            </div>
          </div>

          <div v-if="result.audio_transcript" class="mt-4">
            <div class="text-sm">
              <b>Transkrip Audio:</b>
              <div class="mt-2 p-3 bg-gray-100 rounded-lg max-h-40 overflow-y-auto border border-gray-200">
                {{ result.audio_transcript }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>