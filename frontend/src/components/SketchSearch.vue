<template>
  <el-card class="sketch-card card" shadow="never">
    <div class="sketch-container">
      <div class="sketch-header">
        <h3>手绘搜索</h3>
      </div>
      
      <div class="sketch-canvas-wrapper">
        <canvas
          ref="canvasRef"
          width="600"
          height="400"
          @mousedown="startDrawing"
          @mousemove="draw"
          @mouseup="stopDrawing"
          @mouseleave="stopDrawing"
          class="sketch-canvas"
        ></canvas>
      </div>
      
      <div class="sketch-controls">
        <div class="control-row">
          <label>画笔大小:</label>
          <input 
            type="range" 
            v-model="brushSize" 
            min="1" 
            max="20"
            class="brush-slider"
          />
          <span>{{ brushSize }}px</span>
        </div>
        
        <div class="control-row">
          <label>画笔颜色:</label>
          <div class="color-buttons">
            <button 
              v-for="color in colors" 
              :key="color"
              :style="{ backgroundColor: color }"
              :class="['color-btn', { active: brushColor === color }]"
              @click="brushColor = color"
            ></button>
          </div>
        </div>
        
        <div class="action-buttons">
          <el-button @click="clearCanvas" class="btn btn-secondary">清空</el-button>
          <el-button @click="undo" :disabled="history.length <= 1" class="btn btn-secondary">撤销</el-button>
          <el-button @click="search" class="btn btn-primary">搜索相似图片</el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { searchApi } from '@/api/search'

const router = useRouter()

const canvasRef = ref(null)
const isDrawing = ref(false)
const brushSize = ref(5)
const brushColor = ref('#000000')
const history = ref([])

const colors = ['#000000', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff']

const initCanvas = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  history.value = [canvas.toDataURL()]
}

const saveState = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  history.value.push(canvas.toDataURL())
  if (history.value.length > 10) {
    history.value.shift()
  }
}

const startDrawing = (e) => {
  isDrawing.value = true
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  saveState()
  
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  ctx.beginPath()
  ctx.moveTo(x, y)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.lineWidth = brushSize.value
  ctx.strokeStyle = brushColor.value
}

const draw = (e) => {
  if (!isDrawing.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  ctx.lineTo(x, y)
  ctx.stroke()
}

const stopDrawing = () => {
  isDrawing.value = false
}

const clearCanvas = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  saveState()
  
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
}

const undo = () => {
  if (history.value.length <= 1) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  history.value.pop()
  const img = new Image()
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0)
  }
  img.src = history.value[history.value.length - 1]
}

const search = async () => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  try {
    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, 'image/png')
    })
    
    const formData = new FormData()
    formData.append('file', blob, 'sketch.png')
    formData.append('k', 10)
    
    const response = await searchApi.searchByUpload(formData)
    
    if (response.success) {
      router.push({
        name: 'SearchResults',
        state: {
          results: response.data.results,
          searchParams: response.data.search_params,
          queryImage: canvas.toDataURL(),
          queryType: 'sketch'
        }
      })
    }
  } catch (error) {
    console.error('Search error:', error)
  }
}

onMounted(() => {
  initCanvas()
})
</script>

<style scoped>
.sketch-card {
  border: none;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-light);
}

.sketch-card :deep(.el-card__body) {
  padding: 40px;
}

.sketch-container {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 30px;
  background: white;
  margin-top: 0;
  max-width: 100%;
  box-sizing: border-box;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.sketch-header {
  margin-bottom: 25px;
  text-align: center;
}

.sketch-header h3 {
  margin: 0;
  color: #333;
  font-size: 24px;
  font-weight: 700;
}

.sketch-canvas-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 30px;
}

.sketch-canvas {
  border: 2px solid #ccc;
  border-radius: 4px;
  cursor: crosshair;
  background: white;
  max-width: 100%;
  height: auto;
}

.sketch-controls {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.control-row label {
  font-weight: 600;
  color: #555;
  min-width: 100px;
  font-size: 16px;
}

.brush-slider {
  flex: 1;
  max-width: 400px;
}

.color-buttons {
  display: flex;
  gap: 12px;
}

.color-btn {
  width: 40px;
  height: 40px;
  border: 3px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
}

.color-btn:hover {
  transform: scale(1.1);
}

.color-btn.active {
  border-color: #4a90e2;
  transform: scale(1.1);
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.btn {
  padding: 14px 28px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #4a90e2;
  color: white;
}

.btn-primary:hover {
  background: #3a80d2;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background: #d0d0d0;
}
</style>