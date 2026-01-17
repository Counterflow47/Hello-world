import os
import numpy as np
import json
from tqdm import tqdm

# 引入你的模型和预处理
from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side

def safe_mkdir(path: str):
    os.makedirs(path, exist_ok=True)

def build_gallery(gallery_dir="gallery", target_size=224, patch_size=14):
    images_dir = os.path.join(gallery_dir, "images")
    safe_mkdir(gallery_dir)

    # 1. 加载模型
    print("[INFO] Loading model...")
    weights_path = "vit-dinov2-base.npz"  # 请确保你有这个文件，或者用 small 版本
    if not os.path.exists(weights_path):
        print(f"❌ 错误：权重文件 {weights_path} 不存在！")
        return
    
    weights = np.load(weights_path)
    model = Dinov2Numpy(weights)
    print("[INFO] Model loaded.")

    if not os.path.exists(images_dir):
        print(f"❌ 错误：图片目录 {images_dir} 不存在！请创建并放入图片。")
        return

    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    print(f"[INFO] Found {len(image_files)} images.")
    
    all_features = []
    meta_data = []
    
    # 2. 逐张处理 (Batch Size = 1)
    # 注意：因为 resize_short_side 会产生不同分辨率的图片，无法使用 np.stack 进行 batch 处理
    # 除非进行 padding，但这里为了简单直接逐张跑。
    for img_name in tqdm(image_files, desc="Processing Images"):
        img_path = os.path.join(images_dir, img_name)
        
        try:
            # 预处理 -> (1, 3, H, W) 其中 H, W 动态变化
            input_tensor = resize_short_side(img_path, target_size, patch_size)
            
            # 推理 -> (1, 768)
            feature = model(input_tensor).astype(np.float32)
            
            # 归一化 (L2 Norm)
            norm = np.linalg.norm(feature, axis=1, keepdims=True)
            feature = feature / (norm + 1e-6)
            
            all_features.append(feature)
            meta_data.append({
                "filename": img_name,
                "path": img_path
            })
            
        except Exception as e:
            print(f"Skipping {img_name}: {e}")

    # 3. 保存结果
    if all_features:
        # vstack 将 list of (1, 768) 变成 (N, 768)
        final_features = np.vstack(all_features)
        
        feat_path = os.path.join(gallery_dir, "features.npy")
        map_path = os.path.join(gallery_dir, "images_map.json")
        
        np.save(feat_path, final_features)
        
        # 保存元数据列表
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Done! Gallery built.")
        print(f"   Features shape: {final_features.shape}")
        print(f"   Saved to: {feat_path}")
    else:
        print("⚠️ No features extracted.")

if __name__ == "__main__":
    build_gallery()