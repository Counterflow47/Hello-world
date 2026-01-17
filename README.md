# 🔍 DINOv2 图像检索系统 (NumPy + MobileSAM + MySQL)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![NumPy](https://img.shields.io/badge/NumPy-1.21%2B-013243)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

**基于 Meta DINOv2 Vision Transformer 的企业级图像检索系统**  
*集成了 MobileSAM 语义分割、手绘草图检索与 MySQL 持久化管理的完整解决方案*

[核心特性](#-核心特性) • [安装部署](#-安装部署) • [数据库配置](#-数据库配置) • [使用指南](#-使用指南) • [Web 演示](#-web-演示)

</div>

---

## ✨ 核心特性

本系统不仅验证了 **Vision Transformer (ViT)** 在轻量化场景下的能力，更探索了多模态交互与工业级数据管理的最佳实践。

### 🚀 1. 纯 NumPy 推理引擎 (Zero-Dependency)
- **极致轻量**：完全剥离 PyTorch/TensorFlow，推理阶段仅需 `numpy` + `scipy`。
- **透明可控**：手写复现 Transformer 各层结构，便于理解模型底层原理。

### 📐 2. 动态分辨率自适应
- **位置编码插值**：使用双三次插值动态调整 Positional Embedding，支持任意尺寸输入。
- **智能预处理**：`resize_short_side` 策略确保 Patch 对齐，最大程度保留图像细节。

### 🛠️ 3. 混合后端架构
- **DINOv2 (NumPy)**：负责全局特征提取与向量检索（高频、低延迟）。
- **MobileSAM (PyTorch)**：负责交互式图像分割（按需加载、高精度）。

### 🎨 4. 极致视觉体验 (New)
- **樱花动效主页**：基于 Canvas 渲染的动态樱花飘落背景，提供沉浸式的交互体验。
- **现代 UI 设计**：响应式布局，流畅的前端动效。

### 👆 5. 多模态交互与智能分割 (New)
- **MobileSAM 目标提取**：支持**点击图像触发自动分割**。后端即时抠出目标物体并重新提取特征，实现“指哪搜哪”的精准物体检索。
- **灵魂画手 (Sketch-to-Image)**：内置 HTML5 画板，支持通过**简笔画草图**检索真实图像。充分利用 DINOv2 强大的形状感知与语义理解能力，让搜索不再局限于现成图片。

### 🗄️ 6. 工业级数据管理 (New)
- **MySQL 存储引擎**：取代轻量级 JSON，使用 MySQL 持久化存储图片元数据（路径、特征 ID、上传时间、标签等），支持千万级数据量。
- **动态图库管理**：支持后台**实时上传**与**单条/批量删除**。系统自动维护数据一致性，同步更新磁盘文件、MySQL 记录与 Faiss 向量索引。

---

## 📂 项目结构

```text
faiss-image-search-main/
├── 📁 backend/                 # FastAPI 后端服务
│   ├── 📁 app/
│   │   ├── 📁 api/             # API 路由和端点
│   │   │   ├── 📁 endpoints/   # 具体的 API 端点
│   │   │   │   ├── admin.py    # 管理员接口
│   │   │   │   ├── auth.py     # 认证接口
│   │   │   │   ├── images.py   # 图片管理接口
│   │   │   │   └── search.py   # 搜索接口
│   │   │   └── routes.py       # 路由注册
│   │   ├── 📁 core/            # 配置和核心组件
│   │   │   ├── config.py       # 配置管理
│   │   │   └── database.py     # 数据库连接
│   │   ├── 📁 dino/            # DINOv2 核心模块
│   │   │   ├── dinov2_numpy.py # 模型实现（Embeddings、Attention、Transformer）
│   │   │   └── preprocess_image.py # 预处理函数
│   │   ├── 📁 models/          # 数据模型
│   │   │   ├── faiss_index.py  # Faiss 索引模型
│   │   │   ├── image.py        # 图片数据模型
│   │   │   └── user.py         # 用户数据模型
│   │   ├── 📁 services/        # 业务服务
│   │   │   ├── model_service.py # DINOv2 服务封装
│   │   │   ├── faiss_service.py # Faiss 索引服务
│   │   │   └── sam_service.py  # MobileSAM 服务
│   │   └── 📁 utils/           # 工具函数
│   │       └── logger.py       # 日志工具
│   ├── 📁 data/                # 数据存储
│   │   ├── 📁 images/          # 上传图片存储
│   │   ├── 📁 index/           # Faiss 索引文件
│   │   └── 📁 models/          # 模型权重文件
│   └── main.py                 # 应用入口
│
├── 📁 frontend/                # Vue3 前端界面
│   ├── 📁 src/
│   │   ├── 📁 components/      # Vue 组件
│   │   ├── 📁 views/           # 页面视图
│   │   ├── 📁 api/             # API 封装
│   │   └── main.js             # 入口文件
│   ├── index.html              # HTML 模板
│   └── package.json            # 项目配置
│
├── 📁 gallery/                 # 图库目录
│   └── 📁 images/              # 图库图片存储（10,000+ 张图片）
│
├── 📁 demo_data/               # 演示数据
│   ├── cat.jpg                 # 测试图片
│   ├── dog.jpg                 # 测试图片
│   └── cat_dog_feature.npy     # 参考特征（用于调试验证）
│
├── 📄 debug.py                 # 调试验证脚本
├── 📄 build_gallery.py         # 图库构建脚本
├── 📄 search_cli.py            # 命令行搜索工具
├── 📄 dinov2_numpy.py          # DINOv2 实现（根目录副本）
├── 📄 preprocess_image.py      # 预处理函数（根目录副本）
└── 📄 README.md                # 项目文档
```

---

## 📦 安装部署

### 1. 环境要求
*   **Python**: 3.8+
*   **Database**: **MySQL 8.0+**
*   **Libs**: NumPy, SciPy, Pillow, SQLAlchemy
*   **Search**: Faiss (CPU/GPU)
*   **Web**: FastAPI, Uvicorn
*   **Optional**: PyTorch (仅 MobileSAM 需要)

### 2. 克隆与安装

```bash
git clone <repository-url>
cd faiss-image-search-main

# 安装基础与数据库依赖
pip install numpy scipy pillow faiss-cpu fastapi uvicorn python-multipart aiofiles sqlalchemy pymysql

# 安装 SAM 相关依赖 (可选)
pip install torch torchvision opencv-python mobile-sam
```

### 3. 资源准备 (必需)

| 资源名称 | 文件名 | 说明 |
| :--- | :--- | :--- |
| **DINOv2 权重** | `vit-dinov2-base.npz` | 放置于项目根目录或 `backend/` 下。 |
| **MobileSAM 权重** | `mobile_sam.pt` | 仅在使用分割功能时需要。 |

---

这是根据你的最新要求修改后的「数据库配置」部分。你可以直接替换 README.md 中对应的段落：

---

## ⚙️ 数据库配置

本版本引入 MySQL 进行元数据管理，启动前请务必完成数据库初始化与配置。

### 1. 导入数据库结构
项目已提供完整的 SQL 初始化脚本，位于 `config/database.sql`。请选择以下任意一种方式将该文件导入 MySQL：

**方式 A：使用命令行 (推荐)**
在项目根目录下打开终端，执行以下命令：
```bash
# 请将 'root' 替换为你的 MySQL 用户名，回车后输入密码
mysql -u root -p < config/database.sql
```

**方式 B：使用图形化工具**
使用 Navicat、DBeaver 或 MySQL Workbench 连接本地数据库后，选择“运行 SQL 文件”或“导入”，加载并执行 `config/database.sql`。

> **提示**：该脚本会自动创建名为 `image_search` 的数据库及所有必要的数据表结构。

### 2. 修改配置文件
请打开项目目录下的 `config/config.yaml` 文件，找到数据库配置部分，根据你的本地 MySQL 环境修改以下参数：

```yaml
# config/config.yaml
database:
  # 数据库连接驱动
  driver: mysql+pymysql
  
  # 主机地址 (通常为 localhost)
  host: "localhost"
  
  # 端口号 (默认 3306)
  port: 3306
  
  # ⚠️ 修改为你的 MySQL 用户名
  user: "root"
  
  # ⚠️ 修改为你的 MySQL 密码
  password: "your_password"
  
  # 数据库名称 (需与 database.sql 中保持一致)
  db_name: "image_search"
  
  charset: "utf8mb4"
```
---

## 📖 使用指南

### 第一步：系统自检与索引构建

1.  **运行 Debug 脚本**：确保 NumPy 模型精度正常。
    ```bash
    python debug.py
    ```
2.  **构建初始图库**：扫描 `gallery/images` 并写入 MySQL 和 Faiss。
    ```bash
    python build_gallery.py --reset-db
    ```
    *(注：`--reset-db` 参数会清空旧的数据库记录，请谨慎使用)*

### 第二步：启动服务

**启动后端 API**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端 UI**
```bash
cd frontend
npm install && npm run dev
```

### 第三步：进阶功能体验

#### 1. 🖱️ MobileSAM 局部搜索 (指哪搜哪)
*   在搜索结果或上传界面，鼠标悬停并**点击图片中的任意物体**（如一只猫、一辆车）。
*   后端会自动调用 MobileSAM 对点击点进行**实时分割**，扣取目标区域。
*   系统将仅针对扣取部分重新提取 DINOv2 特征，并在库中检索相似物体。

#### 2. 🎨 灵魂画手 (Sketch Search)
*   点击顶部导航栏的 **“画板模式”**。
*   在画布上绘制简单线条（例如：画一个房子的轮廓）。
*   点击 **“草图检索”**。系统会将 Canvas 内容转为 Base64，利用 DINOv2 对形状和结构的敏感性，在真实图库中寻找构图最接近的图片。

#### 3. 🔧 后台图片管理 (Admin)
*   访问 `/admin` 管理面板。
*   **上传**：支持拖拽上传新图片。系统会自动计算特征 -> 存入 MySQL -> 同步 `index.add()` 到 Faiss 内存索引 -> 保存磁盘文件。
*   **删除**：点击删除图标。系统会**原子性**地同时移除：
    1.  磁盘上的物理文件
    2.  MySQL 中的元数据行
    3.  Faiss 索引中的向量（通过 ID 映射重建或软删除）

#### 4. 🌸 视觉特效设置
主页默认开启樱花飘落效果。如需调整性能或视觉风格，可修改前端 `components/SakuraEffect.vue`：

```javascript
// 樱花配置参数
const SAKURA_COUNT = 30; // 樱花数量 (调大更密集，消耗更高)
const FALL_SPEED = 1.5;  // 飘落速度
const SHOW_SAKURA = true; // 全局开关
```

---

## 📄 许可证

MIT License

---

<div align="center">
  <sub>Made with ❤️ by [Your Name]</sub>
</div>