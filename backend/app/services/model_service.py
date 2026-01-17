"""
模型服务
负责加载DINOv2模型并提取图像特征
"""

import numpy as np
from PIL import Image
from typing import List, Union, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import io
import os

from ..core.config import get_settings
from ..utils.logger import LoggerMixin
from ..dino.dinov2_numpy import Dinov2Numpy
from ..dino.preprocess_image import resize_short_side

settings = get_settings()


class ModelService(LoggerMixin):
    """模型服务类"""
    
    def __init__(self):
        self.model = None
        self.weights = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.feature_dim = settings.faiss.feature_dim
        
    async def initialize(self):
        """初始化模型"""
        try:
            self.logger.info("正在初始化DINOv2图像特征提取模型...")
            
            # 在线程池中加载模型权重
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._load_model
            )
            
            self.logger.info("DINOv2模型初始化完成")
            
        except Exception as e:
            self.logger.error(f"模型初始化失败: {e}")
            raise
    
    def _load_model(self):
        """加载模型（在线程池中执行）"""
        # 检查权重文件是否存在
        weights_path = settings.model.weights_path
        if not os.path.exists(weights_path):
            # 尝试从项目根目录加载
            alternative_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "dinov2_vits14_pretrain.npz"
            )
            if os.path.exists(alternative_path):
                weights_path = alternative_path
            else:
                raise FileNotFoundError(f"DINOv2权重文件未找到: {weights_path}")
        
        self.logger.info(f"正在加载DINOv2权重文件: {weights_path}")
        
        # 加载.npz权重文件
        self.weights = np.load(weights_path, allow_pickle=True)
        
        # 初始化DINOv2模型
        self.model = Dinov2Numpy(self.weights)
        
        self.logger.info(f"DINOv2模型加载成功，特征维度: {self.feature_dim}")
    
    async def extract_features(self, image_input: Union[str, Image.Image, bytes]) -> np.ndarray:
        """
        提取图像特征
        
        Args:
            image_input: 图像输入，可以是文件路径、PIL Image对象或字节数据
            
        Returns:
            特征向量数组
        """
        try:
            # 在线程池中处理图像
            features = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._extract_features_sync, image_input
            )
            return features
        except Exception as e:
            self.logger.error(f"特征提取失败: {e}")
            raise
    
    def _extract_features_sync(self, image_input: Union[str, Image.Image, bytes]) -> np.ndarray:
        """同步提取特征（在线程池中执行）"""
        # 加载图像
        if isinstance(image_input, str):
            # 文件路径
            pixel_values = resize_short_side(
                image_input,
                target_size=settings.model.target_size,
                patch_size=settings.model.patch_size
            )
        elif isinstance(image_input, bytes):
            # 字节数据
            # 先保存为临时文件，再使用resize_short_side
            temp_path = "temp_image.jpg"
            with open(temp_path, 'wb') as f:
                f.write(image_input)
            pixel_values = resize_short_side(
                temp_path,
                target_size=settings.model.target_size,
                patch_size=settings.model.patch_size
            )
            os.remove(temp_path)
        elif isinstance(image_input, Image.Image):
            # PIL Image对象
            # 先保存为临时文件，再使用resize_short_side
            temp_path = "temp_image.jpg"
            image_input.save(temp_path, format='JPEG')
            pixel_values = resize_short_side(
                temp_path,
                target_size=settings.model.target_size,
                patch_size=settings.model.patch_size
            )
            os.remove(temp_path)
        else:
            raise ValueError(f"不支持的图像输入类型: {type(image_input)}")
        
        # 提取特征
        features = self.model(pixel_values)  # (1, D)
        features = features.squeeze()  # (D,)
        
        # 确保特征维度正确
        if features.shape[0] != self.feature_dim:
            self.logger.warning(
                f"特征维度不匹配: 期望{self.feature_dim}, 实际{features.shape[0]}"
            )
        
        # L2 归一化
        features = features / np.linalg.norm(features)
        
        return features
    
    async def extract_batch_features(self, image_inputs: List[Union[str, Image.Image, bytes]]) -> np.ndarray:
        """
        批量提取图像特征
        
        Args:
            image_inputs: 图像输入列表
            
        Returns:
            特征矩阵，形状为 (N, feature_dim)
        """
        try:
            features_list = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._extract_batch_features_sync, image_inputs
            )
            return np.array(features_list)
        except Exception as e:
            self.logger.error(f"批量特征提取失败: {e}")
            raise
    
    def _extract_batch_features_sync(self, image_inputs: List[Union[str, Image.Image, bytes]]) -> List[np.ndarray]:
        """同步批量提取特征（在线程池中执行）"""
        features_list = []
        batch_size = settings.model.batch_size
        
        for i in range(0, len(image_inputs), batch_size):
            batch = image_inputs[i:i + batch_size]
            
            for image_input in batch:
                try:
                    # 提取单个图像特征
                    feature = self._extract_features_sync(image_input)
                    features_list.append(feature)
                except Exception as e:
                    self.logger.warning(f"处理图像失败: {e}")
                    continue
        
        return features_list
    
    def get_feature_dim(self) -> int:
        """获取特征维度"""
        return self.feature_dim
    
    def is_initialized(self) -> bool:
        """检查模型是否已初始化"""
        return self.model is not None
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理模型服务资源...")
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            self.logger.info("模型服务资源清理完成")
        except Exception as e:
            self.logger.error(f"模型服务清理失败: {e}")
