import numpy as np
from PIL import Image

def center_crop(img_path, crop_size=224):
    # 用于兜底或固定尺寸场景
    image = Image.open(img_path).convert("RGB")
    w, h = image.size
    left = (w - crop_size) // 2
    top = (h - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    image = image.crop((left, top, right, bottom))
    image = np.array(image).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image = (image - mean) / std
    image = image.transpose(2, 0, 1)
    return image[None]

# ************* Finished: resize short side *************
def resize_short_side(img_path, target_size=224, patch_size=14):
    """
    1. 调整图像尺寸，使得短边长度为 target_size
    2. 确保最终的高度和宽度都是 patch_size (14) 的整数倍
    """
    # Step 1: load image
    try:
        image = Image.open(img_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Cannot open image {img_path}: {e}")
        
    w, h = image.size

    # Step 2: compute new size
    # 找到短边，计算缩放比例
    if w < h:
        scale = target_size / w
        new_w = target_size
        new_h = int(round(h * scale))
    else:
        scale = target_size / h
        new_h = target_size
        new_w = int(round(w * scale))

    # Step 3: Snap to multiples of patch_size
    # 确保长宽都是 14 的倍数
    new_w = int(round(new_w / patch_size)) * patch_size
    new_h = int(round(new_h / patch_size)) * patch_size
    
    # 防止极少数情况尺寸归零
    new_w = max(new_w, patch_size)
    new_h = max(new_h, patch_size)

    # 使用 Bicubic 插值以获得更好质量
    image = image.resize((new_w, new_h), resample=Image.BICUBIC)

    # Step 4: to_numpy & normalize
    image = np.array(image).astype(np.float32) / 255.0  # (H, W, C)

    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image = (image - mean) / std  # (H, W, C)
    
    image = image.transpose(2, 0, 1)  # (C, H, W)
    
    # 返回 (1, C, H, W) 用于直接推理
    return image[None]