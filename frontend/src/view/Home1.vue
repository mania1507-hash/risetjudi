<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

// State
const selectedInputType = ref('text')
const inputText = ref('')
const result = ref(null)
const imageFile = ref(null)
const videoFile = ref(null)
const imagePreview = ref(null)
const isDetec = ref(false)
const textInput = ref(null)
const webUrl = ref('')
const videoPreview = ref(null)

// Methods
const handleImageUpload = (e) => {
  const file = e.target.files[0]
  if (file) {
    imageFile.value = file
    imagePreview.value = URL.createObjectURL(file)
    // Reset result ketika upload file baru
    resetResult()
    // Auto detect jika ada file
    if (file) {
      setTimeout(() => {
        handleDetect()
      }, 500)
    }
  }
}

const handleVideoUpload = (e) => {
  const file = e.target.files[0]
  if (!file) return
  videoFile.value = file
  videoPreview.value = URL.createObjectURL(file)
  // Reset result ketika upload file baru
  resetResult()
  // Auto detect jika ada file
  if (file) {
    setTimeout(() => {
      handleDetect()
    }, 500)
  }
}

// FUNGSI BARU: Reset semua input dan result
const resetAllInputs = () => {
  result.value = null
  inputText.value = ''
  imageFile.value = null
  imagePreview.value = null
  videoFile.value = null
  videoPreview.value = null
  webUrl.value = ''
}

// FUNGSI BARU: Reset hanya result saja
const resetResult = () => {
  result.value = null
}

// FUNGSI BARU: Ganti input type dengan reset
const changeInputType = (type) => {
  selectedInputType.value = type
  resetResult() // Reset hasil deteksi sebelumnya
  if (type === 'text') {
    nextTick(() => {
      textInput.value?.focus()
    })
  }
}

// FUNGSI BARU: Handle key press untuk Enter
const handleKeyPress = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleDetect()
  }
}

// FUNGSI BARU: Handle key press untuk textarea (Shift+Enter untuk new line, Enter untuk submit)
const handleTextareaKeyPress = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleDetect()
  }
}

onMounted(() => {
  if (selectedInputType.value === 'text') {
    focusTextInput()
  }
})

const focusTextInput = () => {
  nextTick(() => {
    textInput.value?.focus()
  })
}

// Fungsi untuk paste URL dari clipboard
const pasteUrl = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (text) {
      webUrl.value = text
      toast.success('URL berhasil dipaste')
      // Auto focus ke input URL setelah paste
      nextTick(() => {
        const urlInput = document.querySelector('input[type="url"]')
        if (urlInput) {
          urlInput.focus()
        }
      })
    }
  } catch (error) {
    console.error('Gagal paste URL:', error)
    toast.error('Gagal paste URL dari clipboard')
  }
}

// FUNGSI BARU: Fetch dengan approach yang lebih smart
const fetchWebContent = async (url) => {
  try {
    let processedUrl = url.trim()
    if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://')) {
      processedUrl = 'https://' + processedUrl
    }
    
    try {
      new URL(processedUrl)
    } catch (e) {
      throw new Error('Format URL tidak valid')
    }

    // Coba beberapa metode secara berurutan
    const methods = [
      {
        name: 'backend-direct',
        fetch: async () => {
          const response = await fetch(`/api/fetch-webpage?url=${encodeURIComponent(processedUrl)}`)
          if (!response.ok) throw new Error(`Backend error: ${response.status}`)
          const data = await response.json()
          if (!data.success) throw new Error(data.error || 'Backend failed')
          return {
            content: data.content,
            finalUrl: processedUrl,
            method: 'backend-direct'
          }
        }
      },
      {
        name: 'google-cache',
        fetch: async () => {
          // Gunakan Google Cache untuk bypass protection
          const cacheUrl = `https://webcache.googleusercontent.com/search?q=cache:${encodeURIComponent(processedUrl)}&strip=1&vwsrc=0`
          const response = await fetch(`/api/fetch-webpage?url=${encodeURIComponent(cacheUrl)}`)
          if (!response.ok) throw new Error('Google Cache tidak tersedia')
          const data = await response.json()
          if (!data.success) throw new Error('Gagal akses Google Cache')
          return {
            content: data.content,
            finalUrl: processedUrl,
            method: 'google-cache',
            source: 'google-cache'
          }
        }
      },
      {
        name: 'textise-dot-io',
        fetch: async () => {
          // Gunakan textise.iitty untuk ekstrak teks saja
          const textiseUrl = `https://r.jina.ai/${encodeURIComponent(processedUrl)}`
          const response = await fetch(textiseUrl, {
            headers: {
              'Accept': 'text/plain',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
          })
          if (!response.ok) throw new Error('Textise service error')
          const content = await response.text()
          if (!content || content.length < 50) throw new Error('Konten terlalu pendek')
          return {
            content: content,
            finalUrl: processedUrl,
            method: 'textise-dot-io'
          }
        }
      },
      {
        name: 'simple-proxy',
        fetch: async () => {
          // Proxy sederhana dengan user agent yang berbeda
          const response = await fetch(`/api/simple-proxy?url=${encodeURIComponent(processedUrl)}`)
          if (!response.ok) throw new Error('Simple proxy error')
          const data = await response.json()
          return {
            content: data.content,
            finalUrl: processedUrl,
            method: 'simple-proxy'
          }
        }
      }
    ]
    
    let lastError = null
    for (const method of methods) {
      try {
        console.log(`Mencoba metode: ${method.name}`)
        const result = await Promise.race([
          method.fetch(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout')), 25000)
          )
        ])
        console.log(`Berhasil dengan metode: ${method.name}`)
        return result
      } catch (error) {
        console.warn(`Metode ${method.name} gagal:`, error.message)
        lastError = error
        // Tunggu sebentar sebelum mencoba metode berikutnya
        await new Promise(resolve => setTimeout(resolve, 1500))
        continue
      }
    }
    
    throw new Error(`Semua metode gagal. Website mungkin memblokir akses otomatis. Coba gunakan Google Cache secara manual.`)
    
  } catch (error) {
    console.error('Fetch web content error:', error)
    throw new Error(`${error.message}`)
  }
}

// Fungsi untuk extract text dari HTML - DIPERBAIKI untuk handle berbagai format
const extractTextFromHTML = (html) => {
  if (!html) return ''
  
  try {
    // Skip detection untuk Google Cache dan sources lain yang sudah berupa teks
    if (html.includes('Google Cache') || html.includes('textise.iitty') || html.length < 1000) {
      // Jika konten sudah berupa teks atau dari cache, langsung return
      return html
    }
    
    // Cek jika halaman memblokir akses - DIPERBAIKI dengan pattern yang lebih spesifik
    const blockedPatterns = [
      /cloudflare/i,
      /captcha/i,
      /enable.?javascript/i,
      /enable.?cookies/i,
      /just.?a.?moment/i,
      /access.?denied/i,
      /security.?check/i,
      /ddos.?protection/i,
      /checking.?your.?browser/i
    ]
    
    const isBlocked = blockedPatterns.some(pattern => pattern.test(html))
    
    if (isBlocked) {
      throw new Error('Halaman memblokir akses otomatis (JavaScript/CAPTCHA required)')
    }
    
    // Buat DOM parser
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    
    // Hapus elemen yang tidak diinginkan
    const unwantedSelectors = [
      'script', 'style', 'nav', 'header', 'footer', 'aside',
      '.navbar', '.header', '.footer', '.sidebar', '.ads',
      '.advertisement', '.ad', '.popup', '.modal',
      'iframe', 'noscript', 'meta', 'link',
      '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
      '.comments', '.social-share', '.share-buttons'
    ]
    
    unwantedSelectors.forEach(selector => {
      const elements = doc.querySelectorAll(selector)
      elements.forEach(el => el.remove())
    })
    
    // Coba ambil konten utama dengan berbagai strategi
    let text = ''
    
    // Strategi 1: Cari element main content
    const mainContent = doc.querySelector('main, article, .content, .main, .post-content, #content')
    if (mainContent) {
      text = mainContent.textContent || mainContent.innerText || ''
    }
    
    // Strategi 2: Jika tidak ada, ambil dari body
    if (!text.trim()) {
      const body = doc.querySelector('body') || doc.documentElement
      text = body.textContent || body.innerText || ''
    }
    
    // Bersihkan teks
    text = text
      .replace(/\s+/g, ' ')
      .replace(/[\n\r\t]+/g, ' ')
      .replace(/[ ]{2,}/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#[0-9]+;/g, ' ')
      .trim()
    
    // Decode HTML entities
    const decodeHTML = (html) => {
      const textArea = document.createElement('textarea')
      textArea.innerHTML = html
      return textArea.value
    }
    
    text = decodeHTML(text)
    
    // Validasi hasil ekstraksi
    if (text.length < 50) {
      // Jika teks terlalu pendek, coba ambil semua teks tanpa filtering
      const body = doc.querySelector('body') || doc.documentElement
      let rawText = body.textContent || body.innerText || ''
      rawText = rawText.replace(/\s+/g, ' ').replace(/[ ]{2,}/g, ' ').trim()
      
      if (rawText.length > 100) {
        return rawText
      }
      throw new Error('Teks yang diekstrak terlalu pendek')
    }
    
    // Format ulang teks
    text = text.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 10) // Hanya baris dengan minimal 10 karakter
      .join('\n')
    
    return text
    
  } catch (error) {
    console.error('Error extracting text from HTML:', error)
    throw error
  }
}

// Fungsi validasi URL
const isValidUrl = (string) => {
  try {
    new URL(string)
    return true
  } catch (_) {
    return false
  }
}

// Fungsi untuk mengekstrak kata-kata yang terkait judi
const extractGamblingKeywords = (text, prediction) => {
  if (!text || typeof text !== 'string') return []
  
  const gamblingKeywords = [
    // Kata kunci judi online komprehensif
    'judi online', 'perjudian online', 'judi daring', 'perjudian daring',
    'kasino online', 'casino online', 'taruhan online', 'pertaruhan online',
    'slot online', 'slot88', 'slothoki', 'slot gacor', 'slot maxwin',
    'slot pragmatic', 'slot pgsoft', 'slot joker', 'slot habanero',
    'slot spadegaming', 'slot microgaming', 'slot playtech', 'slot yggdrasil',
    'slot rtp', 'slot bocoran', 'slot gampang menang', 'slot jackpot',
    'poker online', 'idnpoker', 'idn poker', 'pkv games', 'pkvgames',
    'dominoqq online', 'domino online', 'bandarq online', 'ceme online',
    'capsa online', 'qiuqiu online', 'togel online', 'toto online', 'lotre online',
    'sbobet', 'maxbet', 'cmd368', 'bet365', '188bet', 'betway', 'dafabet',
    '1xbet', 'melbet', 'parimatch', 'fun88', 'pinnacle', 'sportsbook online',
    'sabung ayam online', 'sv388', 'sv388 online', 'deposit judi', 'deposit slot',
    'wd judi', 'withdraw judi', 'tarik dana judi', 'depo slot', 'wd cepat slot',
    'bonus new member', 'bonus deposit pertama', 'welcome bonus judi',
    'freebet slot', 'free spin slot', 'freespin judi', 'gratis spin slot',
    'cashback judi', 'rollingan slot', 'rollingan harian judi', 'referral judi',
    'jackpot slot', 'jackpot judi', 'jp slot', 'maxwin slot', 'winrate slot',
    'rtp slot', 'rtp live slot', 'rtp tinggi slot', 'bocoran slot gacor',
    'pragmatic play', 'pragmatic slot', 'pg soft', 'pg slot', 'joker gaming',
    'situs judi online', 'agen judi online', 'bandar judi online',
    'situs slot online', 'agen slot online', 'bandar slot online',
    'judi deposit pulsa', 'slot deposit dana', 'slot ovo', 'slot gopay',
    'main slot online', 'main poker online', 'main domino online',
    'main togel online', 'bermain judi online', 'bermain slot online',
    
    // Kata kunci tambahan untuk variasi
    'judi', 'slot', 'poker', 'togel', 'casino', 'taruhan', 'betting',
    'bonus', 'deposit', 'withdraw', 'jackpot', 'gacor', 'maxwin', 'rtp'
  ]
  
  const foundKeywords = []
  const textLower = text.toLowerCase()
  
  gamblingKeywords.forEach(keyword => {
    const keywordLower = keyword.toLowerCase()
    const regex = new RegExp(`\\b${keywordLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi')
    
    if (regex.test(textLower)) {
      foundKeywords.push(keyword)
    }
  })
  
  return [...new Set(foundKeywords)]
}

// Fungsi untuk mendapatkan teks yang akan dianalisis
const getTextForKeywordAnalysis = () => {
  if (selectedInputType.value === 'text') {
    return inputText.value
  } else if (selectedInputType.value === 'web' && result.value) {
    if (result.value.extracted_text && result.value.extracted_text.length > 10) {
      return result.value.extracted_text
    } else if (result.value.full_text) {
      return result.value.full_text
    }
  } else if (result.value?.ocr_text) {
    return result.value.ocr_text
  } else if (result.value?.combined_ocr_text) {
    return result.value.combined_ocr_text
  } else if (result.value?.text) {
    return result.value.text
  }
  return ''
}

// Fungsi untuk mendapatkan kata kunci yang terdeteksi
const getDetectedKeywords = () => {
  if (!result.value) return []
  
  // Prioritas 1: Kata kunci dari backend
  if (result.value.gambling_keywords && result.value.gambling_keywords.length > 0) {
    return result.value.gambling_keywords
  }
  
  // Prioritas 2: Ekstrak manual dari teks
  const analysisText = getTextForKeywordAnalysis()
  if (analysisText) {
    const manualKeywords = extractGamblingKeywords(analysisText, result.value.raw_confidence || 0)
    if (manualKeywords.length > 0) {
      return manualKeywords
    }
  }
  
  return []
}

// Fungsi untuk highlight kata kunci dalam teks
const highlightKeywordsInText = (text, keywords) => {
  if (!text || !keywords || keywords.length === 0) return text
  
  let highlightedText = text
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-300 font-bold">$1</mark>')
  })
  
  return highlightedText
}

// Fungsi untuk mendapatkan semua teks OCR dari video - DIPERBAIKI
const getAllVideoOcrText = () => {
  if (!result.value || selectedInputType.value !== 'video') return ''
  
  // Prioritas: combined_ocr_text dari backend yang sudah diproses
  if (result.value.combined_ocr_text && result.value.combined_ocr_text.trim().length > 0) {
    return result.value.combined_ocr_text
  }
  
  // Fallback: ocr_text biasa
  if (result.value.ocr_text && result.value.ocr_text.trim().length > 0) {
    return result.value.ocr_text
  }
  
  // Fallback: text biasa
  if (result.value.text && result.value.text.trim().length > 0) {
    return result.value.text
  }
  
  return ''
}

const handleDetect = async () => {
  // Validasi input sebelum proses
  if (selectedInputType.value === 'text' && !inputText.value.trim()) {
    toast.error('Masukkan teks terlebih dahulu')
    return
  } else if (selectedInputType.value === 'image' && !imageFile.value) {
    toast.error('Pilih gambar terlebih dahulu')
    return
  } else if (selectedInputType.value === 'video' && !videoFile.value) {
    toast.error('Pilih video terlebih dahulu')
    return
  } else if (selectedInputType.value === 'web' && !webUrl.value.trim()) {
    toast.error('Masukkan URL web terlebih dahulu')
    return
  } else if (selectedInputType.value === 'web' && !isValidUrl(webUrl.value)) {
    toast.error('Format URL tidak valid. Contoh: https://example.com')
    return
  }

  const toastLoading = toast.loading('Loading...')
  result.value = null
  isDetec.value = true

  try {
    if (selectedInputType.value === 'text') {
      const res = await fetch('/api/detect-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText.value }),
      })

      if (!res.ok) {
        throw new Error('Gagal melakukan deteksi teks')
      }

      result.value = await res.json()

    } else if (selectedInputType.value === 'image') {
      const formData = new FormData()
      formData.append('image', imageFile.value)

      const res = await fetch('/api/detect-image', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        throw new Error('Gagal melakukan deteksi gambar')
      }

      result.value = await res.json()

    } else if (selectedInputType.value === 'video') {
      const formData = new FormData()
      formData.append('video', videoFile.value)

      toast.info('Memproses video... Ini mungkin memerlukan waktu beberapa saat.')

      const res = await fetch('/api/detect-video', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || 'Gagal melakukan deteksi video')
      }

      result.value = await res.json()

      // DEBUG: Log hasil video untuk memastikan OCR bekerja
      console.log('Video detection result:', result.value)

    } else if (selectedInputType.value === 'web') {
      toast.info('Mengambil konten web...')
      
      let webContent
      try {
        webContent = await fetchWebContent(webUrl.value)
        console.log(`Berhasil mengambil konten dengan metode: ${webContent.method}`)
      } catch (error) {
        console.error('Semua metode fetch gagal:', error)
        throw new Error(`${error.message}`)
      }
      
      let extractedText
      try {
        extractedText = extractTextFromHTML(webContent.content)
        console.log(`Berhasil mengekstrak teks, panjang: ${extractedText.length}`)
      } catch (extractError) {
        // Jika gagal ekstrak, coba gunakan konten langsung
        if (webContent.content && webContent.content.length > 100) {
          console.log('Menggunakan konten langsung karena ekstraksi gagal')
          extractedText = webContent.content.substring(0, 5000) // Batasi panjang
        } else {
          throw new Error(`Gagal mengekstrak teks dari halaman: ${extractError.message}`)
        }
      }

      // Langsung analisis teks yang diekstrak
      toast.info('Menganalisis konten...')
      const res = await fetch('/api/detect-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: extractedText }),
      })

      if (!res.ok) {
        throw new Error('Gagal melakukan analisis teks')
      }

      const detectionResult = await res.json()
      
      // Gabungkan hasil deteksi dengan informasi web
      result.value = {
        ...detectionResult,
        extracted_text: extractedText.substring(0, 2000) + (extractedText.length > 2000 ? '...' : ''),
        source_url: webContent.finalUrl,
        full_text_length: extractedText.length,
        method_used: webContent.method,
        full_text: extractedText
      }

    }

  } catch (error) {
    console.error('Detection error:', error)
    toast.error(`Error: ${error.message}`)
  } finally {
    isDetec.value = false
    toast.remove(toastLoading)
    if (result.value) {
      toast.success('Deteksi Selesai')
    }
  }
}
</script>

<template>
  <div class="text-slate-800">
    <!-- Container Input -->
    <div class="grid gap-8 px-8 py-8 mb-8 rounded-3xl bg-gradient-to-br from-blue-100 via-blue-75 to-blue-50 shadow-2xl border-2 border-blue-200">
      <div class="text-2xl font-bold text-slate-800 text-center">Pilih Jenis Input</div>
      
      <!-- Tab Buttons - DIPERBAIKI: Gunakan changeInputType() -->
      <div class="flex justify-center font-semibold">
        <button
          class="px-6 py-3 rounded-l-lg border-2 border-blue-400 transition-all duration-300 font-bold"
          :class="selectedInputType === 'text' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-2xl' 
            : 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-800 hover:from-blue-200 hover:to-blue-300 border-blue-400 shadow-lg'"
          @click="() => changeInputType('text')"
        >
          Teks
        </button>
        <button
          class="px-6 py-3 border-t-2 border-b-2 border-blue-400 transition-all duration-300 font-bold"
          :class="selectedInputType === 'image' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-2xl' 
            : 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-800 hover:from-blue-200 hover:to-blue-300 border-blue-400 shadow-lg'"
          @click="() => changeInputType('image')"
        >
          Gambar
        </button>
        <button
          class="px-6 py-3 border-t-2 border-b-2 border-blue-400 transition-all duration-300 font-bold"
          :class="selectedInputType === 'video' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-2xl' 
            : 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-800 hover:from-blue-200 hover:to-blue-300 border-blue-400 shadow-lg'"
          @click="() => changeInputType('video')"
        >
          Video
        </button>
        <button
          class="px-6 py-3 rounded-r-lg border-2 border-blue-400 transition-all duration-300 font-bold"
          :class="selectedInputType === 'web' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-2xl' 
            : 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-800 hover:from-blue-200 hover:to-blue-300 border-blue-400 shadow-lg'"
          @click="() => changeInputType('web')"
        >
          URL Web
        </button>
      </div>

      <!-- Input Content -->
      <div v-if="selectedInputType === 'text'" class="flex flex-col gap-4">
        <div class="bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 rounded-3xl p-4 shadow-inner border-2 border-blue-300">
          <textarea
            ref="textInput"
            v-model="inputText"
            rows="4"
            placeholder="Masukkan teks untuk deteksi... (Tekan Enter untuk deteksi otomatis, Shift+Enter untuk baris baru)"
            @keydown="handleTextareaKeyPress"
            class="w-full p-4 border-2 border-blue-300 rounded-2xl focus:ring-4 focus:ring-blue-400 focus:border-blue-500 resize-none transition-all duration-300 bg-white/95 text-slate-800 placeholder-blue-600 backdrop-blur-sm focus:bg-white font-medium"
          ></textarea>
          <div class="text-xs text-blue-600 mt-2 text-center">
            💡 Tips: Tekan <kbd class="px-2 py-1 bg-blue-200 rounded border border-blue-300">Enter</kbd> untuk deteksi, <kbd class="px-2 py-1 bg-blue-200 rounded border border-blue-300">Shift+Enter</kbd> untuk baris baru
          </div>
        </div>
      </div>

      <div v-if="selectedInputType === 'image'" class="flex flex-col gap-4">
        <label class="cursor-pointer">
          <div class="bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 rounded-3xl p-4 shadow-inner border-2 border-blue-300">
            <div class="border-2 border-dashed border-blue-400 rounded-2xl p-12 text-center hover:border-blue-600 hover:bg-blue-200/90 transition-all duration-300 bg-white/95 backdrop-blur-sm group shadow-lg">
              <svg class="w-16 h-16 mx-auto mb-4 text-blue-600 group-hover:text-blue-700 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <span class="text-blue-900 font-bold text-lg group-hover:text-blue-950 transition-colors duration-300">Pilih Gambar</span>
              <p class="text-blue-700 text-base mt-2 group-hover:text-blue-800 transition-colors duration-300">Klik untuk mengupload gambar (Deteksi otomatis)</p>
            </div>
          </div>
          <input type="file" @change="handleImageUpload" accept="image/*" class="hidden" />
        </label>
        <div v-if="imagePreview" class="mt-4 bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 rounded-3xl p-4 shadow-inner border-2 border-blue-300">
          <img :src="imagePreview" class="max-w-md mx-auto rounded-2xl shadow-lg border-2 border-blue-300 w-full hover:border-blue-500 transition-all duration-300" />
        </div>
      </div>

      <div v-if="selectedInputType === 'video'" class="flex flex-col gap-4">
        <label class="cursor-pointer">
          <div class="bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 rounded-3xl p-4 shadow-inner border-2 border-blue-300">
            <div class="border-2 border-dashed border-blue-400 rounded-2xl p-12 text-center hover:border-blue-600 hover:bg-blue-200/90 transition-all duration-300 bg-white/95 backdrop-blur-sm group shadow-lg">
              <svg class="w-16 h-16 mx-auto mb-4 text-blue-600 group-hover:text-blue-700 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
              </svg>
              <span class="text-blue-900 font-bold text-lg group-hover:text-blue-950 transition-colors duration-300">Pilih Video</span>
              <p class="text-blue-700 text-base mt-2 group-hover:text-blue-800 transition-colors duration-300">Klik untuk mengupload video (Deteksi otomatis)</p>
            </div>
          </div>
          <input type="file" accept="video/*" @change="handleVideoUpload" class="hidden" />
        </label>
        <div v-if="videoPreview" class="mt-4 bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 rounded-3xl p-4 shadow-inner border-2 border-blue-300">
          <video
            :src="videoPreview"
            controls
            class="max-w-md mx-auto rounded-2xl shadow-lg border-2 border-blue-300 w-full hover:border-blue-500 transition-all duration-300"
          ></video>
        </div>
      </div>

      <div v-if="selectedInputType === 'web'" class="flex flex-col gap-4">
        <div class="bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 rounded-3xl p-4 shadow-inner border-2 border-blue-300">
          <div class="flex flex-col gap-4">
            <div class="flex gap-2">
              <input
                v-model="webUrl"
                type="url"
                placeholder="Masukkan URL website (contoh: https://example.com) - Tekan Enter untuk deteksi otomatis"
                @keydown="handleKeyPress"
                class="flex-1 p-4 border-2 border-blue-300 rounded-2xl focus:ring-4 focus:ring-blue-400 focus:border-blue-500 transition-all duration-300 bg-white/95 text-slate-800 placeholder-blue-600 backdrop-blur-sm focus:bg-white font-medium"
              />
              <button
                @click="pasteUrl"
                class="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-bold px-6 py-4 rounded-2xl transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-xl border-2 border-blue-400"
                title="Paste URL dari clipboard"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                Paste
              </button>
            </div>
            <div class="text-sm text-blue-700 bg-blue-100/50 p-3 rounded-xl border border-blue-200">
              <strong>Tips:</strong> Untuk website yang memblokir akses, sistem akan mencoba berbagai metode termasuk Google Cache. 
              <span class="font-semibold">Tekan Enter untuk deteksi otomatis!</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detect Button -->
      <div class="flex justify-center">
        <button
          :disabled="isDetec"
          @click="handleDetect"
          class="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 hover:from-blue-700 hover:via-blue-800 hover:to-blue-900 text-white font-bold px-12 py-4 rounded-2xl transition-all duration-300 flex items-center gap-3 shadow-3xl hover:shadow-4xl disabled:opacity-70 disabled:cursor-not-allowed transform hover:scale-110 text-xl border-2 border-blue-500"
        >
          <svg
            v-if="isDetec"
            class="animate-spin h-6 w-6 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            ></path>
          </svg>
          <span class="text-xl">{{ isDetec ? 'Sedang Memproses...' : 'Deteksi Sekarang' }}</span>
        </button>
      </div>
    </div>

    <!-- Result Container - DIPERBAIKI untuk Video dan URL -->
    <div v-if="result" class="grid gap-6 px-8 py-8 rounded-3xl bg-gradient-to-br from-blue-200 via-blue-100 to-blue-50 shadow-3xl border-2 border-blue-300">
      <div class="text-3xl font-bold text-slate-800 text-center mb-8">Hasil Deteksi</div>
      
      <div class="flex flex-col items-center gap-8">
        <!-- Informasi URL untuk tipe web -->
        <div v-if="selectedInputType === 'web' && result.source_url" class="w-full max-w-4xl">
          <div class="flex items-center gap-4 bg-white/80 p-4 rounded-2xl border-2 border-blue-300">
            <div class="text-lg font-bold text-blue-800 min-w-max">URL yang dianalisis:</div>
            <div class="text-lg text-blue-600 break-all">{{ result.source_url }}</div>
            <div v-if="result.method_used" class="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
              {{ result.method_used === 'backend-direct' ? 'Metode Utama' : 
                 result.method_used === 'google-cache' ? 'Google Cache' : 
                 result.method_used === 'textise-dot-io' ? 'Textise API' :
                 result.method_used === 'simple-proxy' ? 'Simple Proxy' : 'Metode Alternatif' }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-6">
          <div class="text-xl font-bold text-slate-800">Status:</div>
          <div
  class="text-xl font-bold px-6 py-3 rounded-2xl border-2 backdrop-blur-sm shadow-2xl"
  :class="
    result?.raw_confidence != null
      ? (result.raw_confidence > 0.5 
          ? 'bg-gradient-to-r from-red-200 via-red-100 to-red-50 text-red-900 border-red-400' 
          : 'bg-gradient-to-r from-green-200 via-green-100 to-green-50 text-green-900 border-green-400')
      : 'bg-gradient-to-r from-yellow-200 via-yellow-100 to-yellow-50 text-yellow-900 border-yellow-400'
  "
>
  {{
    result?.raw_confidence != null
      ? (result.raw_confidence > 0.5
          ? '❌ Terindikasi Iklan Judi'
          : '✔️ Bukan Iklan Judi')
      : '⚠️ Teks tidak ditemukan'
  }}
</div>
        </div>
        
        <div class="flex items-center gap-6">
          <div class="text-xl font-bold text-slate-800">Persentase Kata Judi Online:</div>
          <div class="text-xl bg-gradient-to-r from-blue-200 via-blue-100 to-blue-50 text-blue-900 px-6 py-3 rounded-2xl border-2 border-blue-400 font-bold backdrop-blur-sm shadow-2xl">
            {{ result.confidence }}
          </div>
        </div>

        <!-- Kata Kunci yang Terdeteksi -->
        <div v-if="getDetectedKeywords().length > 0" class="w-full max-w-4xl">
          <div class="bg-white/80 p-6 rounded-2xl border-2 border-blue-300">
            <div class="text-xl font-bold text-slate-800 mb-4">
              Kata Kunci Judi Online Terdeteksi ({{ getDetectedKeywords().length }}):
            </div>
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="keyword in getDetectedKeywords()" 
                :key="keyword"
                class="bg-gradient-to-r from-orange-200 to-orange-300 text-orange-900 px-3 py-2 rounded-full text-sm font-semibold border border-orange-400 shadow-md hover:scale-105 transition-transform duration-200"
              >
                🔍 {{ keyword }}
              </span>
            </div>
          </div>
        </div>

        <!-- Teks dengan Highlight Kata Kunci untuk Text -->
        <div v-if="selectedInputType === 'text' && getDetectedKeywords().length > 0" class="w-full max-w-4xl">
          <div class="bg-white/80 p-6 rounded-2xl border-2 border-blue-300">
            <div class="text-xl font-bold text-slate-800 mb-4">
              Teks dengan Kata Kunci Terdeteksi:
            </div>
            <div class="text-slate-700 bg-blue-50/50 p-4 rounded-xl border border-blue-200 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
              <div v-html="highlightKeywordsInText(inputText, getDetectedKeywords())"></div>
            </div>
          </div>
        </div>

        <!-- HASIL VIDEO - DIPERBAIKI: Tampilkan OCR dan Keyword -->
        <div v-if="selectedInputType === 'video'" class="w-full max-w-4xl">
          <!-- OCR Text dari Video -->
          <div v-if="getAllVideoOcrText() && getAllVideoOcrText().trim().length > 0" class="mb-6">
            <div class="bg-white/80 p-6 rounded-2xl border-2 border-blue-300">
              <div class="text-xl font-bold text-slate-800 mb-4">
                Teks yang Dikenali dari Video (OCR):
                <span class="text-sm font-normal text-blue-600 ml-2">
                  {{ getAllVideoOcrText().length }} karakter
                </span>
              </div>
              <div class="text-slate-700 bg-blue-50/50 p-4 rounded-xl border border-blue-200 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                <div v-if="getDetectedKeywords().length > 0" v-html="highlightKeywordsInText(getAllVideoOcrText(), getDetectedKeywords())"></div>
                <div v-else>{{ getAllVideoOcrText() }}</div>
              </div>
            </div>
          </div>

          <!-- Pesan jika tidak ada teks yang terdeteksi -->
          <div v-else class="bg-white/80 p-6 rounded-2xl border-2 border-blue-300">
            <div class="text-center py-4 text-gray-500">
              <svg class="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <p class="text-lg">Tidak ada teks yang terdeteksi dalam video</p>
              <p class="text-sm mt-2">Video mungkin tidak mengandung teks atau kualitasnya terlalu rendah untuk OCR</p>
            </div>
          </div>
        </div>

        <!-- HASIL WEB - DIPERBAIKI: Tampilkan Keyword -->
        <div v-if="selectedInputType === 'web'" class="w-full max-w-4xl">
          <!-- Teks yang Diekstrak dari Web -->
          <div v-if="result.extracted_text" class="mb-6">
            <div class="bg-white/80 p-6 rounded-2xl border-2 border-blue-300">
              <div class="flex justify-between items-center mb-4">
                <div class="text-xl font-bold text-slate-800">Teks yang Diekstrak dari Website:</div>
                <div class="text-sm text-blue-600 bg-blue-100 px-3 py-1 rounded-full">
                  {{ result.full_text_length }} karakter
                </div>
              </div>
              <div class="text-slate-700 bg-blue-50/50 p-4 rounded-xl border border-blue-200 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                <div v-if="getDetectedKeywords().length > 0" v-html="highlightKeywordsInText(result.extracted_text, getDetectedKeywords())"></div>
                <div v-else>{{ result.extracted_text }}</div>
              </div>
              <div v-if="result.full_text_length > 2000" class="text-sm text-blue-600 mt-2 text-center">
                *Teks dipotong untuk tampilan. {{ result.full_text_length - 2000 }} karakter lainnya tidak ditampilkan.
              </div>
            </div>
          </div>
        </div>

        <!-- OCR Text (untuk gambar) -->
        <div v-if="selectedInputType === 'image' && result.ocr_text" class="w-full max-w-4xl">
          <div class="bg-white/80 p-6 rounded-2xl border-2 border-blue-300">
            <div class="text-xl font-bold text-slate-800 mb-4">Teks yang Dikenali (OCR):</div>
            <div class="text-slate-700 bg-blue-50/50 p-4 rounded-xl border border-blue-200 max-h-60 overflow-y-auto">
              <div v-if="getDetectedKeywords().length > 0" v-html="highlightKeywordsInText(result.ocr_text, getDetectedKeywords())"></div>
              <div v-else>{{ result.ocr_text }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>