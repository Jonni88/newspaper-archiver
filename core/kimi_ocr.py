"""Kimi API OCR - использует Kimi для распознавания текста."""
import os
import base64
import json
from pathlib import Path
from typing import List, Tuple, Optional


class KimiOCRProcessor:
    """OCR using Kimi API."""
    
    API_URL = "https://api.moonshot.cn/v1/chat/completions"
    
    def __init__(self, api_key: str = None):
        """
        Initialize Kimi OCR.
        
        Args:
            api_key: Kimi API key. If None, tries to get from KIMI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('KIMI_API_KEY')
        if not self.api_key:
            raise ValueError("Kimi API key not provided. Set KIMI_API_KEY environment variable.")
        
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests not installed. Run: pip install requests")
    
    def image_to_text(self, image_path: str, prompt: str = None) -> str:
        """
        Extract text from image using Kimi.
        
        Args:
            image_path: Path to image file
            prompt: Custom prompt for OCR (optional)
            
        Returns:
            Extracted text
        """
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Determine image format
        ext = Path(image_path).suffix.lower()
        if ext == '.png':
            mime_type = 'image/png'
        elif ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/jpeg'  # Default
        
        default_prompt = (
            "Распознай весь текст на этом изображении. "
            "Это скан старой газеты. "
            "Сохрани форматирование, абзацы и заголовки. "
            "Верни только текст без комментариев."
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "moonshot-v1-8k-vision-preview",  # Vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt or default_prompt
                        }
                    ]
                }
            ],
            "temperature": 0.1  # Low temperature for accuracy
        }
        
        try:
            response = self.requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=120  # Images can take time
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"Kimi API error: {e}")
            return ""
    
    def process_pdf_pages(self, pdf_path: str, dpi: int = 200) -> List[Tuple[int, str]]:
        """
        Process all pages of PDF.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for rendering
            
        Returns:
            List of (page_number, text) tuples
        """
        from core.pdf_processor import PDFProcessor
        
        processor = PDFProcessor(dpi=dpi)
        
        # Render to images
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            pages = processor.render_pages(pdf_path, temp_dir)
            
            results = []
            for page_no, image_path in pages:
                print(f"Обработка страницы {page_no} через Kimi...")
                text = self.image_to_text(image_path)
                results.append((page_no, text))
                print(f"  Распознано {len(text)} символов")
            
            return results
    
    @staticmethod
    def estimate_cost(pages: int) -> dict:
        """
        Estimate cost for processing.
        
        Kimi vision pricing (approximate):
        - Input: ~$0.003 per 1K tokens (image + text)
        - Output: ~$0.003 per 1K tokens
        
        One page ~2K tokens total = ~$0.006
        """
        cost_per_page = 0.006  # USD
        return {
            'per_page': cost_per_page,
            'total': pages * cost_per_page,
            'currency': 'USD',
            'note': 'Approximate cost for vision model'
        }


# Simple CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python kimi_ocr.py <путь_к_изображению_или_PDF>")
        print("")
        print("Установи API ключ:")
        print("  set KIMI_API_KEY=your_api_key  (Windows)")
        print("  export KIMI_API_KEY=your_api_key  (Linux/Mac)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        ocr = KimiOCRProcessor()
        
        if file_path.lower().endswith('.pdf'):
            print(f"Обработка PDF: {file_path}")
            pages = ocr.process_pdf_pages(file_path)
            for page_no, text in pages:
                print(f"\n{'='*50}")
                print(f"СТРАНИЦА {page_no}")
                print('='*50)
                print(text[:1000])  # First 1000 chars
                if len(text) > 1000:
                    print(f"\n... [ещё {len(text) - 1000} символов]")
        else:
            print(f"Обработка изображения: {file_path}")
            text = ocr.image_to_text(file_path)
            print("\nРезультат:")
            print('='*50)
            print(text)
            
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
