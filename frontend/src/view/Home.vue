<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

// ===== Base URL Backend Flask =====
const BASE_URL = "http://127.0.0.1:5000"

// ===== State =====
const selectedInputType = ref('text')
const inputText = ref('')
const inputUrl = ref('')
const result = ref(null)
const imageFile = ref(null)
const videoFile = ref(null)
const imagePreview = ref(null)
const isDetec = ref(false)
const textInput = ref(null)

// ===== Methods =====
const resetDetectionResult = () => {
  result.value = null
  isDetec.value = false
}

const handleImageUpload = (e) => {
  const file = e.target.files[0]
  if (file) {
    imageFile.value = file
    imagePreview.value = URL.createObjectURL(file)
  }
}

const focusTextInput = () => {
  nextTick(() => {
    textInput.value?.focus()
  })
}

const changeInputType = (type) => {
  resetDetectionResult()
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
      if (!videoFile.value) {
        toast.error('Pilih video terlebih dahulu.')
        return
      }
      const formData = new FormData()
      formData.append('video', videoFile.value)
      res = await fetch(`${BASE_URL}/api/detect-video`, { method: 'POST', body: formData })
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
          <textarea
            ref="textInput"
            v-model="inputText"
            rows="4"
            placeholder="Masukkan teks untuk deteksi"
            class="border-2 border-blue-200 rounded-xl p-3 w-full focus:ring-2 focus:ring-blue-400 transition"
            @keydown.enter.exact.prevent="handleDetect"
          ></textarea>
        </div>

        <div v-if="selectedInputType === 'url'" class="flex flex-col gap-4">
          <input
            v-model="inputUrl"
            type="text"
            placeholder="Masukkan URL (contoh: https://example.com)"
            class="border-2 border-blue-200 rounded-xl p-3 w-full focus:ring-2 focus:ring-blue-400 transition"
            @keydown.enter="handleDetect"
          />
        </div>

        <div v-if="selectedInputType === 'image'" class="flex flex-col gap-4">
          <input
            type="file"
            @change="handleImageUpload"
            accept="image/*"
            class="border-2 border-blue-200 rounded-xl p-2 w-full bg-gray-50 hover:bg-gray-100 transition"
          />
          <div v-if="imagePreview" class="mt-3 text-center">
            <img :src="imagePreview" class="max-h-64 mx-auto rounded-xl shadow-md border" />
          </div>
        </div>

        <div v-if="selectedInputType === 'video'" class="flex flex-col gap-4">
          <input
            type="file"
            accept="video/*"
            @change="handleVideoUpload"
            class="border-2 border-blue-200 rounded-xl p-2 w-full bg-gray-50 hover:bg-gray-100 transition"
          />
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

          <div v-if="result.ocr_text" class="mt-4">
            <div class="text-sm">
              <b>Teks yang Diekstrak:</b>
              <div class="mt-2 p-3 bg-gray-100 rounded-lg max-h-40 overflow-y-auto border border-gray-200">
                {{ result.ocr_text }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
