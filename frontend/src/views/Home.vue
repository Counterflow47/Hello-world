<template>
  <div class="home-page" ref="homePageRef" :style="homePageStyle">
    <!-- 首屏大标题区域 -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-title">
          <h1 class="main-title">SZU图寻</h1>
          <p class="subtitle">基于DIVOv2和MobileSAM的智能寻图系统</p>
        </div>
        <div class="hero-scroll-indicator">
          <div class="scroll-arrow"></div>
          <p>向下滚动探索</p>
        </div>
      </div>
    </div>

    <!-- 搜图区域 -->
    <div class="search-section" :class="{ 'visible': isSearchVisible }">
      <div class="search-container">
        <!-- 上传搜索区域 -->
        <div class="search-row">
          <!-- 左侧：上传和搜索区域 -->
          <div class="search-column">
            <el-card class="search-card card" shadow="never">

              <!-- 上传搜索区域 -->
              <div class="upload-section">
                <el-upload
                  ref="uploadRef"
                  class="upload-demo"
                  drag
                  :auto-upload="false"
                  :on-change="handleFileChange"
                  :show-file-list="false"
                  accept="image/*"
                >

                    <el-icon class="el-icon--upload" size="48">
                      <UploadFilled />
                    </el-icon>
                    <div class="el-upload__text">
                      将图片拖到此处，或<em>点击上传</em>
                    </div>

                </el-upload>
                  <!-- OR 分隔线 -->
                  <div class="separator">
                    <span class="separator-text">OR</span>
                  </div>

                  <!-- URL输入区域 -->
                  <div class="url-section">
                    <el-input
                      v-model="imageUrl"
                      placeholder="输入图片地址"
                      size="large"
                      clearable
                      class="url-input"
                    >
                      <template #prepend>
                        <el-icon><Link /></el-icon>
                      </template>
                    </el-input>
                  </div>
                

                <!-- 预览上传的图片 -->
                <div v-if="uploadedFile" class="preview-section fade-in">
                  <el-divider content-position="left">图片预览</el-divider>
                  <div class="preview-container">
                    <img :src="previewUrl" class="preview-image" alt="预览图片" />
                    <div class="preview-info">
                      <p><strong>文件名：</strong>{{ uploadedFile.name }}</p>
                      <p><strong>大小：</strong>{{ formatFileSize(uploadedFile.size) }}</p>
                      <p><strong>类型：</strong>{{ uploadedFile.type }}</p>
                    </div>
                  </div>
                </div>
                
              </div>

              

              <!-- 搜索按钮 -->
              <div class="search-actions">
                <el-button
                  type="primary"
                  size="large"
                  :loading="searching"
                  :disabled="!canSearch"
                  @click="performSearch"
                  class="btn-primary search-btn"
                >
                  <el-icon><Search /></el-icon>
                  开始搜索
                </el-button>
              </div>
            </el-card>
          </div>

          <!-- 右侧：看板娘 -->
          <div class="mascot-column" :class="{ 'visible': isMascotVisible }">
            <div class="mascot-area">
              <div class="mascot-character">
                <img src="/kanban/a.png" alt="看板娘" class="mascot-image" />
              </div>
              <div class="mascot-text">
                <p>欢迎来到SZU图寻！</p>
                <p>我可以帮你找图哟！</p>
              </div>
            </div>
          </div>
        </div>

        <!-- OR 分隔线 -->
        <div class="separator-large">
          <span class="separator-text">OR</span>
        </div>

        <!-- SAM智能抠图搜索区域 -->
        <div class="search-row">
          <!-- 左侧：SAM搜索区域 -->
          <div class="search-column">
            <SamSearch />
          </div>

          <!-- 右侧：看板娘 -->
          <div class="mascot-column" :class="{ 'visible': isMascotVisible }">
            <div class="mascot-area">
              <div class="mascot-character">
                <img src="/kanban/b.png" alt="看板娘" class="mascot-image" />
              </div>
              <div class="mascot-text">
                <p>我是智能抠图助手！</p>
                <p>点击图片中的物体吧！</p>
              </div>
            </div>
          </div>
        </div>

        <!-- OR 分隔线 -->
        <div class="separator-large">
          <span class="separator-text">OR</span>
        </div>

        <!-- 手绘搜索区域 -->
        <div class="search-row">
          <!-- 左侧：手绘搜索区域 -->
          <div class="search-column">
            <SketchSearch />
          </div>

          <!-- 右侧：看板娘 -->
          <div class="mascot-column" :class="{ 'visible': isMascotVisible }">
            <div class="mascot-area">
              <div class="mascot-character">
                <img src="/kanban/c.png" alt="看板娘" class="mascot-image" />
              </div>
              <div class="mascot-text">
                <p>我是手绘搜索助手！</p>
                <p>画出你想要的图片吧！</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 搜索结果展示（如果有结果才显示，并跳转到结果页） -->

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { UploadFilled, Search, Link, Picture } from '@element-plus/icons-vue'
import { searchApi, searchByUrl } from '@/api/search'
import SamSearch from '@/components/SamSearch.vue'
import SketchSearch from '@/components/SketchSearch.vue'

const router = useRouter()

// 响应式数据
const uploadedFile = ref(null)
const previewUrl = ref('')
const imageUrl = ref('')
const searching = ref(false)
const scrollY = ref(0)
const isSearchVisible = ref(false)
const isMascotVisible = ref(false)
const homePageRef = ref(null)
const scrollProgress = ref(0)

// 搜索参数
const searchParams = ref({
  k: 10
})

// 背景样式计算
const homePageStyle = computed(() => {
  return {
    backgroundPositionY: `${scrollProgress.value}%`,
    transition: 'background-position 0.1s ease-out'
  }
})

// 滚动事件处理
const handleScroll = () => {
  scrollY.value = window.scrollY
  
  // 计算滚动进度
  if (homePageRef.value) {
    const scrollTop = scrollY.value
    const scrollHeight = homePageRef.value.scrollHeight
    const windowHeight = window.innerHeight
    const progress = (scrollTop / (scrollHeight - windowHeight)) * 100
    scrollProgress.value = Math.min(Math.max(progress, 0), 100)
  }
  
  // 控制搜索区域显示 - 使用更平滑的触发点
  const searchThreshold = window.innerHeight * 0.3
  if (scrollY.value > searchThreshold) {
    isSearchVisible.value = true
  } else {
    isSearchVisible.value = false
  }
  
  // 控制看板娘显示 - 使用更平滑的触发点
  const mascotThreshold = window.innerHeight * 0.5
  if (scrollY.value > mascotThreshold) {
    isMascotVisible.value = true
  } else {
    isMascotVisible.value = false
  }
}

// 组件挂载时添加滚动监听
onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  nextTick(() => {
    handleScroll() // 初始化
  })
})

// 组件卸载时移除滚动监听
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// 计算属性
const canSearch = computed(() => {
  return uploadedFile.value !== null || imageUrl.value.trim() !== ''
})

// 处理文件上传
const handleFileChange = (file) => {
  const { raw } = file
  
  // 检查文件类型
  if (!raw.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  
  // 检查文件大小（10MB）
  if (raw.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }
  
  uploadedFile.value = raw
  
  // 创建预览URL
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target.result
  }
  reader.readAsDataURL(raw)
}

// 执行搜索
const performSearch = async () => {
  if (!canSearch.value) return
  
  searching.value = true
  
  try {
    let response
    let queryType = ''
    let queryImage = ''
    
    if (uploadedFile.value) {
      // 文件上传搜索
      const formData = new FormData()
      formData.append('file', uploadedFile.value)
      formData.append('k', searchParams.value.k)
      
      response = await searchApi.searchByUpload(formData)
      queryType = 'upload'
      queryImage = previewUrl.value
    } else if (imageUrl.value.trim()) {
      // URL搜索
      response = await searchByUrl(imageUrl.value, {
        top_k: searchParams.value.k
      })
      queryType = 'url'
      queryImage = imageUrl.value
    }
    
    if (response.success) {
      // 跳转到搜索结果页面，传递数据
      router.push({
        name: 'SearchResults',
        state: {
          results: response.data.results,
          searchParams: response.data.search_params,
          queryImage: queryImage,
          queryType: queryType
        }
      })
    } else {
      ElMessage.error('搜索失败，请重试')
    }
  } catch (error) {
    console.error('搜索错误：', error)
    
    // 根据错误类型提供不同的提示
    let errorMessage = '搜索失败'
    if (error.response) {
      // 后端返回的错误
      const status = error.response.status
      const detail = error.response.data?.detail || error.response.data?.message || '未知错误'
      
      if (status === 400) {
        errorMessage = `请求错误: ${detail}`
      } else if (status === 500) {
        errorMessage = `服务器错误: ${detail}`
      } else {
        errorMessage = `HTTP ${status}: ${detail}`
      }
    } else if (error.message) {
      errorMessage = `网络错误: ${error.message}`
    }
    
    ElMessage.error(errorMessage)
  } finally {
    searching.value = false
  }
}


// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  // 页面加载完成后的初始化逻辑
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(to bottom, #667eea 0%, #764ba2 50%, #f8fbff 100%);
  background-attachment: fixed;
  background-size: 100% 300%;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 首屏区域 */
.hero-section {
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="50" cy="10" r="0.5" fill="rgba(255,255,255,0.05)"/><circle cx="10" cy="50" r="0.5" fill="rgba(255,255,255,0.05)"/><circle cx="90" cy="30" r="0.5" fill="rgba(255,255,255,0.05)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  pointer-events: none;
}

.hero-content {
  text-align: center;
  z-index: 1;
  position: relative;
}

.hero-title {
  margin-bottom: 60px;
}

.main-title {
  font-size: 6rem;
  font-weight: 900;
  color: white;
  margin: 0 0 20px 0;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  letter-spacing: 10px;
  animation: titleGlow 3s ease-in-out infinite alternate;
}

@keyframes titleGlow {
  from {
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 30px rgba(255, 255, 255, 0.3);
  }
  to {
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 50px rgba(255, 255, 255, 0.5);
  }
}

.subtitle {
  font-size: 1.8rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  font-weight: 300;
  letter-spacing: 4px;
}

.hero-scroll-indicator {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
  opacity: 0.8;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateX(-50%) translateY(0);
  }
  40% {
    transform: translateX(-50%) translateY(-10px);
  }
  60% {
    transform: translateX(-50%) translateY(-5px);
  }
}

.scroll-arrow {
  width: 30px;
  height: 30px;
  border-right: 3px solid white;
  border-bottom: 3px solid white;
  transform: rotate(45deg);
  margin-bottom: 10px;
  animation: arrowMove 1.5s infinite;
}

@keyframes arrowMove {
  0% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.5;
  }
}

.hero-scroll-indicator p {
  margin: 0;
  font-size: 14px;
  letter-spacing: 2px;
  font-weight: 500;
}

/* 搜图区域 */
.search-section {
  width: 100%;
  max-width: 1400px;
  opacity: 0;
  transform: translateY(60px);
  transition: all 1s cubic-bezier(0.2, 0.8, 0.2, 1);
  padding: 40px 20px;
  position: relative;
}

.search-container {
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 40px;
  align-items: start;
  width: 100%;
}

.search-row {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 40px;
  align-items: stretch;
}

.search-column {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.mascot-column {
  width: 100%;
  opacity: 0;
  transform: translateY(40px);
  transition: all 1.2s cubic-bezier(0.2, 0.8, 0.2, 1) 0.4s;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.mascot-column.visible {
  opacity: 1;
  transform: translateY(0);
}

.upload-search-area {
  width: 100%;
}

.search-card {
  border: none;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-light);
}

.search-card :deep(.el-card__body) {
  padding: 40px;
}


.upload-section {
  margin: 30px 0;
}

.upload-content {
  border-color: var(--border-color);
  background: var(--bg-secondary);
  transition: all 0.3s ease;
  padding: 40px 30px;
}

.upload-content:hover {
  border-color: var(--primary-color);
  background: var(--bg-light);
  transform: translateY(-2px);
}

.preview-section {
  margin-top: 20px;
}

.preview-container {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.preview-image {
  max-width: 160px;
  max-height: 160px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-light);
}

.preview-info {
  flex: 1;
  padding: 15px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
}

.preview-info p {
  margin: 8px 0;
  font-size: 14px;
  color: var(--text-primary);
}

/* OR 分隔线 */
.separator {
  text-align: center;
  margin: 25px 0;
  position: relative;
}

.separator::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-color);
}

.separator-text {
  background: var(--bg-primary);
  padding: 0 16px;
  color: var(--text-secondary);
  font-size: 14px;
  position: relative;
  z-index: 1;
}

/* 大分隔线 */
.separator-large {
  text-align: center;
  margin: 40px 0;
  position: relative;
}

.separator-large::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 20%;
  right: 20%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}

.separator-large .separator-text {
  background: var(--bg-primary);
  padding: 0 20px;
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 600;
  position: relative;
  z-index: 1;
}

.url-section {
  margin: 0px 0;
}

.url-input {
  border-radius: 24px;
}

.url-tip {
  margin-top: 12px;
}

.search-params {
  margin: 20px 0;
}

.params-row {
  display: flex;
  gap: 20px;
  align-items: center;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.param-item label {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
}

.search-actions {
  text-align: center;
  margin-top: 30px;
}

.search-btn {
  background: linear-gradient(45deg, var(--primary-color), var(--primary-light));
  border: none;
  font-weight: 600;
  padding: 14px 35px;
  font-size: 16px;
  box-shadow: var(--shadow-light);
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-medium);
  background: linear-gradient(45deg, var(--primary-dark), var(--primary-color));
}

/* 看板娘区域 */
.mascot-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: transparent;
  margin-top: 40px;
  opacity: 0;
  transform: translateY(40px);
  transition: all 1.2s cubic-bezier(0.2, 0.8, 0.2, 1) 0.4s;
  position: relative;
}

.search-section.visible {
  opacity: 1;
  transform: translateY(0);
}

.mascot-section.visible {
  opacity: 1;
  transform: translateY(0);
}

.mascot-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0px;
  padding: 30px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.mascot-area:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.mascot-character {
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 4px solid #fff;
}

.mascot-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.mascot-text {
  text-align: center;
  color: var(--text-primary);
  margin-top: 20px;
}

.mascot-text p {
  margin: 6px 0;
  font-size: 1rem;
  line-height: 1.4;
  font-weight: 500;
  background: linear-gradient(45deg, #2196f3, #1565c0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Element Plus 输入框圆角样式覆盖 */
:deep(.el-input__wrapper) {
  border-radius: 24px;
  padding: 0 18px;
  border: 2px solid var(--border-color);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

:deep(.el-input-group__prepend) {
  border-radius: 24px 0 0 24px;
  border: 2px solid var(--border-color);
  border-right: none;
  background: var(--bg-secondary);
}

:deep(.el-input-group .el-input__wrapper) {
  border-radius: 0 24px 24px 0;
}

:deep(.el-input-group:hover .el-input-group__prepend) {
  border-color: var(--primary-color);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .main-title {
    font-size: 3rem;
    letter-spacing: 5px;
  }
  
  .subtitle {
    font-size: 1.2rem;
    letter-spacing: 2px;
  }
  
  .home-page {
    height: 100vh;
    height: 100dvh; /* 移动端精确视口高度 */
  }
  
  .search-section {
    padding: 15px;
  }
  
  .search-container {
    max-width: 95%;
  }
  
  .upload-content {
    padding: 20px 15px;
  }
  
  .preview-image {
    max-width: 120px;
    max-height: 120px;
  }
  
  .search-params {
    margin: 15px 0;
  }
  
  .separator {
    margin: 15px 0;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 2.2rem;
    letter-spacing: 3px;
  }
  
  .subtitle {
    font-size: 1rem;
    letter-spacing: 1px;
  }
  
  .hero-scroll-indicator {
    bottom: 40px;
  }
  
  .scroll-arrow {
    width: 24px;
    height: 24px;
  }
}


</style> 