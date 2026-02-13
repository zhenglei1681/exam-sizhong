"""
OCR 引擎模块

封装 PaddleOCR 进行图片文字识别
"""
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None


class OCREngine:
    """OCR 引擎封装类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 OCR 引擎

        Args:
            config: OCR 配置字典
        """
        if PaddleOCR is None:
            raise ImportError("请先安装 PaddleOCR: pip install paddleocr")

        self.config = config or {}
        self.use_gpu = self.config.get("use_gpu", False)
        self.lang = self.config.get("lang", "ch")
        self._ocr: Optional[PaddleOCR] = None

    def _init_ocr(self):
        """延迟初始化 PaddleOCR"""
        if self._ocr is None:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False
            )

    def recognize(
        self,
        image,
        return_details: bool = False
    ) -> List[Dict[str, Any]]:
        """
        识别图片中的文字

        Args:
            image: 图片对象，可以是 PIL.Image.Image 或 numpy 数组
            return_details: 是否返回详细信息（包括坐标、置信度等）

        Returns:
            识别结果列表，每项包含文本内容
        """
        self._init_ocr()

        # 转换图片格式
        if isinstance(image, Image.Image):
            image = np.array(image)

        # 执行 OCR
        result = self._ocr.ocr(image, cls=True)

        if result is None or not result:
            return []

        # 格式化结果
        formatted_results = []
        for line_group in result:
            if line_group is None:
                continue
            for line in line_group:
                bbox, (text, confidence) = line

                if return_details:
                    formatted_results.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": float(confidence)
                    })
                else:
                    formatted_results.append({
                        "text": text
                    })

        return formatted_results

    def recognize_to_text(
        self,
        image,
        separator: str = "\n"
    ) -> str:
        """
        识别图片中的文字并返回拼接的文本

        Args:
            image: 图片对象
            separator: 文本分隔符

        Returns:
            拼接后的文本
        """
        results = self.recognize(image)
        texts = [item["text"] for item in results]
        return separator.join(texts)

    def get_text_with_confidence(
        self,
        image,
        min_confidence: float = 0.5
    ) -> List[str]:
        """
        �识别图片中的文字，并过滤低置信度结果

        Args:
            image: 图片对象
            min_confidence: 最小置信度阈值

        Returns:
            高置信度文本列表
        """
        results = self.recognize(image, return_details=True)
        return [
            item["text"]
            for item in results
            if item.get("confidence", 0) >= min_confidence
        ]
