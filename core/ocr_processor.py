"""OCR module using Tesseract (easier to bundle than PaddleOCR)."""
from typing import List, Tuple, Optional
import os


class OCRProcessor:
    """OCR processing using pytesseract."""
    
    def __init__(self, lang: str = 'rus'):
        self.lang = lang
        self._tesseract_cmd = None
        self._find_tesseract()
    
    def _find_tesseract(self):
        """Find Tesseract executable."""
        import shutil
        
        # Check if tesseract is in PATH
        tesseract_path = shutil.which('tesseract')
        
        if tesseract_path:
            self._tesseract_cmd = tesseract_path
            return
        
        # Check common Windows locations
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'.\tesseract\tesseract.exe',
            r'..\tesseract\tesseract.exe',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self._tesseract_cmd = path
                # Set for pytesseract
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = path
                except ImportError:
                    pass
                return
    
    def process_image(self, image_path: str) -> Tuple[str, float]:
        """Process single image with OCR.
        
        Returns:
            (extracted_text, confidence)
        """
        try:
            from PIL import Image
            import pytesseract
            
            # Configure tesseract path if found
            if self._tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
            
            # Open image
            image = Image.open(image_path)
            
            # Run OCR
            text = pytesseract.image_to_string(image, lang=self.lang)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5
            except:
                avg_confidence = 0.5  # Default confidence if can't calculate
            
            return text.strip(), avg_confidence
            
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


# Singleton instance
_ocr_instance = None


def get_ocr_processor(lang: str = 'rus') -> OCRProcessor:
    """Get or create OCR processor instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRProcessor(lang=lang)
    return _ocr_instance
