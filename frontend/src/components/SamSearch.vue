<template>
  <div class="sam-container">
    <div class="sam-header">
      <h3><el-icon><MagicStick /></el-icon> SAM 智能抠图搜索</h3>
      <p class="sam-tip">上传图片后点击想要搜索的物体，系统会自动识别并抠出该物体</p>
    </div>

    <!-- 上传区域 -->
    <div class="sam-upload-section">
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
    </div>

    <!-- 图片预览和点击区域 -->
    <div v-if="previewUrl" class="sam-preview-section">
      <!-- 操作提示 -->
      <div class="action-tip">
        <el-tag type="info" effect="light">
          <el-icon><Mouse /></el-icon>
          点击图片中的物体进行抠图
        </el-tag>
      </div>

      <div class="preview-wrapper">
        <div class="preview-container" @click="handleImageClick">
          <img 
            :src="previewUrl" 
            ref="imageRef"
            class="preview-image" 
            alt="预览图片" 
            :style="{ cursor: searching ? 'wait' : 'crosshair' }"
          />
          
          <!-- 点击位置指示器 - 增强版 -->
          <div 
            v-if="clickPosition && !searching" 
            class="click-indicator-enhanced"
            :style="{
              left: clickPosition.x + 'px',
              top: clickPosition.y + 'px'
            }"
          >
            <div class="target-cross"></div>
            <div class="pulse-ring-large"></div>
            <div class="pulse-ring-medium"></div>
            <div class="pulse-ring-small"></div>
          </div>
          
          <!-- 抠图遮罩预览 -->
          <div 
            v-if="segmentationMask && !searching" 
            class="segmentation-overlay"
            :style="maskStyle"
          ></div>
          
          <!-- 加载遮罩 - 增强版 -->
          <div v-if="searching" class="loading-overlay-enhanced">
            <div class="loading-content">
              <div class="progress-steps">
                <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
                  <div class="step-icon"><el-icon><MagicStick /></el-icon></div>
                  <span class="step-text">识别物体</span>
                </div>
                <div class="step-divider"></div>
                <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
                  <div class="step-icon"><el-icon><Crop /></el-icon></div>
                  <span class="step-text">智能抠图</span>
                </div>
                <div class="step-divider"></div>
                <div class="step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
                  <div class="step-icon"><el-icon><Search /></el-icon></div>
                  <span class="step-text">搜索相似</span>
                </div>
              </div>
              
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
              
              <p class="loading-text">{{ loadingText }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 抠图结果 - 增强版 -->
      <div v-if="croppedImage" class="cropped-result-enhanced">
        <div class="result-header">
          <h4><el-icon><Crop /></el-icon> 抠图结果</h4>
          <el-tag :type="segmentScore > 0.7 ? 'success' : 'warning'" :effect="segmentScore > 0.7 ? 'dark' : 'light'">
            置信度: {{ segmentScore.toFixed(3) }}
          </el-tag>
        </div>
        <div class="cropped-container-enhanced">
          <div class="cropped-preview">
            <div class="before-after-container">
              <div class="image-wrapper before">
                <img :src="previewUrl" class="small-preview" alt="原图" />
                <div class="image-label">原图</div>
              </div>
              <div class="arrow-icon">→</div>
              <div class="image-wrapper after">
                <img :src="croppedImage" class="small-preview" alt="抠图结果" />
                <div class="image-label">抠图</div>
              </div>
            </div>
          </div>
          <div class="cropped-details">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="点击位置">
                ({{ Math.round(clickPosition?.x || 0) }}, {{ Math.round(clickPosition?.y || 0) }})
              </el-descriptions-item>
              <el-descriptions-item label="置信度评分">
                <el-progress :percentage="Math.round(segmentScore * 100)" :status="segmentScore > 0.7 ? 'success' : 'warning'" />
              </el-descriptions-item>
              <el-descriptions-item label="搜索状态">
                <el-tag type="success" effect="light">
                  <el-icon><Check /></el-icon> 已完成
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>

      <!-- 搜索按钮 -->
      <div class="sam-actions">
        <el-button
          v-if="!croppedImage"
          type="primary"
          size="large"
          :loading="searching"
          @click.prevent="performSearch"
          :disabled="!canSearch"
          class="btn-primary search-btn"
        >
          <el-icon><Search /></el-icon>
          开始抠图搜索
        </el-button>
        <el-button
          v-else
          type="success"
          size="large"
          @click.prevent="navigateToResults"
          class="btn-success search-btn"
        >
          <el-icon><Search /></el-icon>
          查看相似图片
        </el-button>
        <el-button
          type="default"
          size="large"
          @click.prevent="reset"
          class="btn-secondary"
        >
          <el-icon><Refresh /></el-icon>
          重新上传
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Search, Refresh, Loading, MagicStick, Mouse, Crop, Check } from '@element-plus/icons-vue'
import { searchApi } from '@/api/search'

const router = useRouter()

const uploadRef = ref(null)
const imageRef = ref(null)
const uploadedFile = ref(null)
const previewUrl = ref('')
const searching = ref(false)
const clickPosition = ref(null)
const croppedImage = ref('')
const segmentScore = ref(0)
const imageBase64 = ref('')
const searchParams = ref({
  k: 10
})

// 新增：进度相关状态
const currentStep = ref(0)
const progressPercent = ref(0)
const loadingText = ref('')
const segmentationMask = ref(null)
const searchResults = ref([])
const searchParamsResponse = ref({})
let progressTimer = null

const canSearch = computed(() => {
  return clickPosition.value !== null && !searching.value
})

// 新增：进度更新函数
const updateProgress = (step, percent, text) => {
  currentStep.value = step
  progressPercent.value = percent
  loadingText.value = text
}

// 新增：模拟进度动画
const startProgressAnimation = () => {
  let progress = 0
  updateProgress(1, 0, '正在识别物体...')
  
  progressTimer = setInterval(() => {
    progress += 2
    if (progress <= 33) {
      updateProgress(1, progress, '正在识别物体...')
    } else if (progress <= 66) {
      updateProgress(2, progress, '正在智能抠图...')
    } else if (progress < 100) {
      updateProgress(3, progress, '正在搜索相似图片...')
    }
  }, 100)
}

// 新增：停止进度动画
const stopProgressAnimation = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

// 新增：清理定时器
onUnmounted(() => {
  stopProgressAnimation()
})

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
    imageBase64.value = e.target.result
  }
  reader.readAsDataURL(raw)
  
  // 重置状态
  clickPosition.value = null
  croppedImage.value = ''
  segmentScore.value = 0
}

const handleImageClick = (e) => {
  if (searching.value) return
  if (!imageRef.value) return
  
  const rect = imageRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  clickPosition.value = { x, y }
  
  ElMessage.success(`已选择位置: (${Math.round(x)}, ${Math.round(y)})`)
}

const performSearch = async () => {
  if (!canSearch.value) return
  
  searching.value = true
  startProgressAnimation()
  
  try {
    const data = {
      image_base64: imageBase64.value,
      x: Math.round(clickPosition.value.x),
      y: Math.round(clickPosition.value.y),
      k: searchParams.value.k
    }
    
    // 调试：打印发送的数据
    console.log('发送SAM搜索请求:', {
      x: data.x,
      y: data.y,
      k: data.k,
      image_base64_length: data.image_base64 ? data.image_base64.length : 0
    })
    
    const response = await searchApi.searchBySegment(data)
    
    // 完成进度
    stopProgressAnimation()
    updateProgress(3, 100, '抠图完成！')
    
    if (response.success) {
      // 安全处理响应数据
      if (response.data?.cropped_image) {
        croppedImage.value = response.data.cropped_image
      }
      if (response.data?.segment_score !== undefined) {
        segmentScore.value = response.data.segment_score
      }
      
      // 保存搜索结果，等待用户手动点击
      if (response.data?.results) {
        searchResults.value = response.data.results
      }
      if (response.data?.search_params) {
        searchParamsResponse.value = response.data.search_params
      }
      
      ElMessage.success('抠图成功！点击"查看相似图片"按钮查看结果')
    } else {
      ElMessage.error('抠图失败，请重试')
    }
  } catch (error) {
    stopProgressAnimation()
    updateProgress(0, 0, '')
    console.error('SAM搜索错误：', error)
    let errorMessage = '搜索失败'
    if (error.response) {
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
    setTimeout(() => {
      searching.value = false
    }, 500)
  }
}

// 新增：手动跳转到结果页面
const navigateToResults = () => {
  if (!searchResults.value || searchResults.value.length === 0) {
    ElMessage.warning('没有找到相似图片')
    return
  }
  
  // 调试：打印要发送的数据
  console.log('跳转到搜索结果页面:', {
    results_length: searchResults.value.length,
    searchParams: searchParamsResponse.value,
    queryImage_exists: !!croppedImage.value,
    queryType: 'sam',
    segmentScore: segmentScore.value
  })
  
  // 使用query参数传递搜索结果数据（JSON字符串）
  router.push({
    name: 'SearchResults',
    query: {
      queryType: 'sam',
      results: JSON.stringify(searchResults.value),
      searchParams: JSON.stringify(searchParamsResponse.value),
      queryImage: croppedImage.value,
      segmentScore: segmentScore.value
    }
  })
}

const reset = () => {
  uploadedFile.value = null
  previewUrl.value = ''
  clickPosition.value = null
  croppedImage.value = ''
  segmentScore.value = 0
  imageBase64.value = ''
  segmentationMask.value = null
  searchResults.value = []
  searchParamsResponse.value = {}
  stopProgressAnimation()
  updateProgress(0, 0, '')
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}
</script>

<style scoped>
.sam-container {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 30px;
  background: white;
  margin-top: 0;
  max-width: 100%;
  box-sizing: border-box;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.sam-header {
  margin-bottom: 25px;
  text-align: center;
}

.sam-header h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.sam-header h3 .el-icon {
  color: #4a90e2;
  animation: magic-glow 2s ease-in-out infinite;
}

@keyframes magic-glow {
  0%, 100% {
    filter: drop-shadow(0 0 5px rgba(74, 144, 226, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 15px rgba(74, 144, 226, 0.8));
  }
}

.sam-tip {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.sam-upload-section {
  margin-bottom: 25px;
}

.sam-preview-section {
  margin-top: 20px;
}

/* 操作提示 */
.action-tip {
  text-align: center;
  margin-bottom: 20px;
}

.action-tip .el-tag {
  font-size: 14px;
  padding: 8px 20px;
  border-radius: 20px;
}

.preview-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 25px;
}

.preview-container {
  position: relative;
  display: inline-block;
  border: 3px solid #4a90e2;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  display: block;
}

/* 点击位置指示器 - 增强版 */
.click-indicator-enhanced {
  position: absolute;
  width: 80px;
  height: 80px;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 10;
}

.target-cross {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 40px;
  height: 40px;
  transform: translate(-50%, -50%);
}

.target-cross::before,
.target-cross::after {
  content: '';
  position: absolute;
  background: #4a90e2;
  border-radius: 2px;
}

.target-cross::before {
  width: 100%;
  height: 3px;
  top: 50%;
  transform: translateY(-50%);
}

.target-cross::after {
  height: 100%;
  width: 3px;
  left: 50%;
  transform: translateX(-50%);
}

.pulse-ring-large {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid #4a90e2;
  border-radius: 50%;
  animation: pulse-large 2s infinite;
}

.pulse-ring-medium {
  position: absolute;
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  border: 2px solid #4a90e2;
  border-radius: 50%;
  animation: pulse-medium 1.5s infinite;
}

.pulse-ring-small {
  position: absolute;
  top: 20%;
  left: 20%;
  width: 60%;
  height: 60%;
  border: 2px solid #4a90e2;
  border-radius: 50%;
  animation: pulse-small 1s infinite;
}

@keyframes pulse-large {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

@keyframes pulse-medium {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.8);
    opacity: 0;
  }
}

@keyframes pulse-small {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}

/* 抠图遮罩 */
.segmentation-overlay {
  position: absolute;
  top: 0;
  left: 0;
  background: rgba(74, 144, 226, 0.3);
  border: 3px solid #4a90e2;
  border-radius: 8px;
  pointer-events: none;
  z-index: 15;
  animation: mask-appear 0.5s ease;
}

@keyframes mask-appear {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 加载遮罩 - 增强版 */
.loading-overlay-enhanced {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 20;
  backdrop-filter: blur(5px);
}

.loading-content {
  text-align: center;
  color: white;
  padding: 40px;
}

.progress-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 25px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.step .step-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #666;
  transition: all 0.3s ease;
}

.step.active .step-icon {
  background: #4a90e2;
  color: white;
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.5);
}

.step.completed .step-icon {
  background: #52c41a;
  color: white;
  box-shadow: 0 0 20px rgba(82, 196, 26, 0.5);
}

.step .step-text {
  font-size: 13px;
  color: #999;
  white-space: nowrap;
}

.step.active .step-text,
.step.completed .step-text {
  color: white;
  font-weight: 600;
}

.step-divider {
  width: 40px;
  height: 2px;
  background: #333;
  transition: all 0.3s ease;
}

.step.active ~ .step-divider {
  background: #4a90e2;
}

.step.completed ~ .step-divider {
  background: #52c41a;
}

.progress-bar {
  width: 300px;
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
  margin: 20px auto;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a90e2, #52c41a);
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(74, 144, 226, 0.5);
}

.loading-text {
  font-size: 16px;
  margin: 10px 0 0 0;
  color: #4a90e2;
  font-weight: 600;
}

/* 抠图结果 - 增强版 */
.cropped-result-enhanced {
  margin-top: 25px;
  padding: 25px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 2px solid #4a90e2;
  box-shadow: 0 4px 20px rgba(74, 144, 226, 0.15);
  animation: slide-up 0.6s ease;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-header h4 {
  margin: 0;
  color: #333;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-header .el-tag {
  font-size: 14px;
  padding: 6px 16px;
}

.cropped-container-enhanced {
  display: flex;
  gap: 30px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.cropped-preview {
  flex: 1;
  min-width: 300px;
}

.before-after-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.image-wrapper {
  text-align: center;
  position: relative;
}

.image-wrapper .small-preview {
  max-width: 150px;
  max-height: 150px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.image-wrapper.before .small-preview {
  border: 2px solid #909399;
}

.image-wrapper.after .small-preview {
  border: 2px solid #4a90e2;
}

.image-label {
  margin-top: 10px;
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.arrow-icon {
  font-size: 30px;
  color: #4a90e2;
  font-weight: bold;
  animation: arrow-pulse 1.5s infinite;
}

@keyframes arrow-pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.cropped-details {
  flex: 1;
  min-width: 250px;
}

.cropped-details :deep(.el-descriptions__label) {
  font-weight: 600;
  color: #666;
}

.cropped-details :deep(.el-descriptions__content) {
  color: #333;
}

.sam-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 25px;
}

.btn-primary {
  background: linear-gradient(45deg, #4a90e2, #3a80d2);
  border: none;
  font-weight: 600;
  padding: 14px 35px;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.4);
  background: linear-gradient(45deg, #3a80d2, #2a70c2);
}

.btn-success {
  background: linear-gradient(45deg, #52c41a, #389e0d);
  border: none;
  font-weight: 600;
  padding: 14px 35px;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.3);
  transition: all 0.3s ease;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(82, 196, 26, 0.4);
  background: linear-gradient(45deg, #389e0d, #237804);
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
  border: none;
  font-weight: 600;
  padding: 14px 35px;
  font-size: 16px;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: #d0d0d0;
  transform: translateY(-2px);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sam-container {
    padding: 20px;
  }
  
  .preview-container {
    border-width: 2px;
  }
  
  .before-after-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .arrow-icon {
    transform: rotate(90deg);
  }
  
  .cropped-container-enhanced {
    flex-direction: column;
    align-items: center;
  }
  
  .small-preview {
    max-width: 120px;
    max-height: 120px;
  }
  
  .sam-actions {
    flex-direction: column;
  }
  
  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
  
  .progress-steps {
    flex-wrap: wrap;
  }
  
  .progress-bar {
    width: 250px;
  }
}
</style>
