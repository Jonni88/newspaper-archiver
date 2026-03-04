"""OCR module using PaddleOCR."""
from typing import List, Tuple, Optional
import os


class OCRProcessor:
    """OCR processing using PaddleOCR."""
    
    def __init__(self, lang: str = 'ru'):
        self.lang = lang
        self._ocr = None
    
    def _get_ocr(self):
        """Lazy initialization of PaddleOCR."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    show_log=False
                )
            except ImportError:
                print("PaddleOCR not installed. OCR functionality will not work.")
                raise
        return self._ocr
    
    def process_image(self, image_path: str) -> Tuple[str, float]:
        """Process single image with OCR.
        
        Returns:
            (extracted_text, average_confidence)
        """
        try:
            ocr = self._get_ocr()
            result = ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return "", 0.0
            
            texts = []
            confidences = []
            
            for line in result[0]:
                if line:
                    text = line[1][0]
                    confidence = line[1][1]
                    texts.append(text)
                    confidences.append(confidence)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
            
        except Exception as e:
            print(f"OCR error for {image_path}: {e}")
            return "", 0.0
    
    def process_images(self, image_paths: List[Tuple[int, str]]) -> List[Tuple[int, str, float]]:
        """Process multiple images.
        
        Args:
            image_paths: List of (page_number, image_path) tuples
            
        Returns:
            List of (page_number, text, confidence) tuples
        """
        results = []
        
        for page_no, image_path in image_paths:
            text, confidence = self.process_image(image_path)
            results.append((page_no, text, confidence))
        
        return results


# Simple factory for OCR processors
_ocr_instance = None


def get_ocr_processor(lang: str = 'ru') -> OCRProcessor:
    """Get or create OCR processor instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRProcessor(lang=lang)
    return _ocr_instance
