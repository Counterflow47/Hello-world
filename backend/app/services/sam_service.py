import os
import torch
import numpy as np
import cv2
from mobile_sam import sam_model_registry, SamPredictor
from app.core.config import get_settings

settings = get_settings()

class SamService:
    def __init__(self):
        self.predictor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # 尝试多个可能的模型路径
        self.possible_paths = [
            "mobile_sam.pt",
            "./mobile_sam.pt",
            "./backend/mobile_sam.pt",
            "./app/services/mobile_sam.pt",
            "./data/models/mobile_sam.pt",
            "./models/mobile_sam.pt",
        ]

    async def initialize(self):
        """初始化 MobileSAM 模型"""
        print(f"🔄 正在加载 MobileSAM 模型 ({self.device})...")
        try:
            # 加载模型 (vit_t 是 MobileSAM 的类型)
            model_type = "vit_t"
            
            # 尝试所有可能的路径
            model_path = None
            for path in self.possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                raise FileNotFoundError(f"未找到 MobileSAM 模型文件。请将 mobile_sam.pt 放在以下任一目录：\n{chr(10).join(self.possible_paths)}")
            
            print(f"📦 找到模型文件: {model_path}")
            sam = sam_model_registry[model_type](checkpoint=model_path)
            sam.to(device=self.device)
            sam.eval()
            
            self.predictor = SamPredictor(sam)
            print("✅ MobileSAM 模型加载成功")
        except Exception as e:
            print(f"❌ MobileSAM 模型加载失败: {e}")
            # 这里可以选择是否抛出异常，或者允许服务在没有SAM的情况下启动
            # raise e

    async def cleanup(self):
        """清理显存"""
        if self.predictor:
            del self.predictor
            if self.device == "cuda":
                torch.cuda.empty_cache()
            print("✅ MobileSAM 资源已释放")

    def predict_mask_and_crop(self, image_rgb: np.ndarray, x: int, y: int):
        """核心业务逻辑：点击 -> 预测 -> 抠图"""
        if not self.predictor:
            raise RuntimeError("SAM 模型未初始化")

        # 1. 设置图像
        self.predictor.set_image(image_rgb)

        # 2. 预测
        input_point = np.array([[x, y]])
        input_label = np.array([1]) # 1=前景

        masks, scores, _ = self.predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True,
        )

        # 3. 选最好的 mask
        best_idx = np.argmax(scores)
        best_mask = masks[best_idx]

        # 4. 抠图
        cropped_img = np.zeros_like(image_rgb)
        cropped_img[best_mask] = image_rgb[best_mask]

        # 5. 裁剪黑边 (只保留物体部分)
        y_indices, x_indices = np.where(best_mask)
        if len(y_indices) > 0:
            x_min, x_max = x_indices.min(), x_indices.max()
            y_min, y_max = y_indices.min(), y_indices.max()
            # 增加一点 padding
            pad = 10
            h, w, _ = image_rgb.shape
            y_min = max(0, y_min - pad)
            y_max = min(h, y_max + pad)
            x_min = max(0, x_min - pad)
            x_max = min(w, x_max + pad)
            
            # 只裁剪物体区域，其他区域全部去掉
            final_crop = cropped_img[y_min:y_max, x_min:x_max]
            return final_crop, float(scores[best_idx])
        
        return cropped_img, 0.0
