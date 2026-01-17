import os
import json
import numpy as np
import sys

from dinov2_numpy import Dinov2Numpy
# ⚠️ 修正：改为使用 resize_short_side，与图库构建保持一致
from preprocess_image import resize_short_side 

# ================= 配置 =================
GALLERY_DIR = "gallery"
FEATURE_FILE = "features.npy"
MAP_FILE = "images_map.json"
MODEL_WEIGHTS = "vit-dinov2-base.npz"
# =======================================

def load_metadata(map_path):
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"找不到索引文件: {map_path}")
    
    with open(map_path, "r", encoding="utf-8") as f:
        # build_gallery 现在保存的是标准 JSON List，直接 load
        return json.load(f)

def search_image(query_path, k=10):
    # 1. 检查文件
    feat_path = os.path.join(GALLERY_DIR, FEATURE_FILE)
    map_path = os.path.join(GALLERY_DIR, MAP_FILE)

    if not os.path.exists(feat_path) or not os.path.exists(map_path):
        print("❌ 错误：图库未构建，请先运行 build_gallery.py")
        return

    # 2. 加载图库
    print(f"[INFO] Loading gallery...")
    gallery_feats = np.load(feat_path).astype(np.float32) # (N, 768)
    meta = load_metadata(map_path)

    # 3. 加载模型
    print(f"[INFO] Loading model...")
    if not os.path.exists(MODEL_WEIGHTS):
        print(f"❌ 权重文件 {MODEL_WEIGHTS} 缺失")
        return
    weights = np.load(MODEL_WEIGHTS)
    model = Dinov2Numpy(weights)

    # 4. 处理查询图片
    print(f"[INFO] Processing query: {query_path}")
    try:
        # ✅ 关键：使用同样的预处理策略 (Resize Short Side)
        query_input = resize_short_side(query_path, target_size=224, patch_size=14)
    except Exception as e:
        print(f"❌ 图片处理失败: {e}")
        return

    # 5. 提取特征
    # 输出 (1, 768)
    query_feat = model(query_input).astype(np.float32)
    
    # 6. 归一化 (Cosine Similarity 前置步骤)
    query_norm = np.linalg.norm(query_feat, axis=1, keepdims=True)
    query_feat = query_feat / (query_norm + 1e-6)

    # 7. 计算相似度 (矩阵乘法)
    # query: (1, 768), gallery: (N, 768) -> (1, N)
    scores = np.dot(query_feat, gallery_feats.T).flatten()

    # 8. 排序 (从大到小)
    top_indices = np.argsort(scores)[::-1][:k]

    # 9. 打印结果
    print("\n" + "="*50)
    print(f"🔍 Search Results for: {os.path.basename(query_path)}")
    print("="*50)
    
    for rank, idx in enumerate(top_indices, start=1):
        score = scores[idx]
        item = meta[idx]
        print(f"Rank {rank:02d} | Similarity: {score:.4f} | {item['filename']}")
        # print(f"        Path: {item['path']}") # 可选打印完整路径
        print("-" * 50)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_cli.py <path_to_query_image>")
    else:
        search_image(sys.argv[1])