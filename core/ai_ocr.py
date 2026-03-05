"""AI OCR module using DeepSeek API or other vision models."""
import os
import base64
import requests
from typing import List, Tuple, Optional


class AIOCRProcessor:
    """OCR processing using AI vision APIs."""
    
    SUPPORTED_PROVIDERS = {
        'deepseek': 'DeepSeek API',
        'openai': 'OpenAI GPT-4 Vision',
        'google': 'Google Vision API',
    }
    
    def __init__(self, provider: str = 'deepseek', api_key: str = None):
        """
        Initialize AI OCR processor.
        
        Args:
            provider: 'deepseek', 'openai', or 'google'
            api_key: API key for the service
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f'{provider.upper()}_API_KEY')
        
    def image_to_text(self, image_path: str) -> str:
        """
        Extract text from image using AI API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        if not self.api_key:
            raise ValueError(f"API key not set for {self.provider}")
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        if self.provider == 'deepseek':
            return self._deepseek_ocr(image_data)
        elif self.provider == 'openai':
            return self._openai_ocr(image_data)
        elif self.provider == 'google':
            return self._google_ocr(image_path)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _deepseek_ocr(self, image_base64: str) -> str:
        """Use DeepSeek API for OCR."""
        url = "https://api.deepseek.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Распознай весь текст на этом изображении. Это скан газеты. Верни только текст без комментариев."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return ""
    
    def _openai_ocr(self, image_base64: str) -> str:
        """Use OpenAI GPT-4 Vision for OCR."""
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this newspaper scan. Return only the text content without any comments or explanations. Preserve the layout as much as possible."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return ""
    
    def _google_ocr(self, image_path: str) -> str:
        """Use Google Vision API for OCR."""
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            
            with open(image_path, 'rb') as f:
                content = f.read()
            
            image = vision.Image(content=content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(response.error.message)
            
            return response.full_text_annotation.text
            
        except ImportError:
            print("Google Cloud Vision not installed. Run: pip install google-cloud-vision")
            return ""
        except Exception as e:
            print(f"Google Vision error: {e}")
            return ""
    
    @staticmethod
    def estimate_cost(pages: int, provider: str = 'deepseek') -> dict:
        """
        Estimate cost for processing pages.
        
        Returns dict with cost info.
        """
        # Approximate costs per page (assuming 1 page = 1 image)
        costs = {
            'deepseek': {
                'per_page': 0.001,  # ~$0.001 per page (very approximate)
                'total': pages * 0.001,
                'currency': 'USD'
            },
            'openai': {
                'per_page': 0.01,  # GPT-4 Vision is more expensive
                'total': pages * 0.01,
                'currency': 'USD'
            },
            'google': {
                'per_page': 0.0015,  # Google Vision pricing
                'total': pages * 0.0015,
                'currency': 'USD'
            }
        }
        
        return costs.get(provider, costs['deepseek'])


# Hybrid OCR that tries Tesseract first, then AI for bad pages
class HybridOCRProcessor:
    """Hybrid OCR: Tesseract for speed, AI for quality."""
    
    def __init__(self, ai_provider: str = None, ai_api_key: str = None, 
                 confidence_threshold: float = 0.6):
        """
        Initialize hybrid OCR.
        
        Args:
            ai_provider: AI provider name or None for Tesseract only
            ai_api_key: API key for AI service
            confidence_threshold: If Tesseract confidence below this, use AI
        """
        self.ai_processor = None
        if ai_provider and ai_api_key:
            self.ai_processor = AIOCRProcessor(ai_provider, ai_api_key)
        
        self.confidence_threshold = confidence_threshold
        
        # Import Tesseract OCR
        from core.ocr_processor import OCRProcessor
        self.tesseract = OCRProcessor(lang='rus')
    
    def process_image(self, image_path: str) -> Tuple[str, float, str]:
        """
        Process image with hybrid approach.
        
        Returns:
            (text, confidence, method_used)
        """
        # First try Tesseract
        text, confidence = self.tesseract.process_image(image_path)
        
        # If confidence is good, use Tesseract result
        if confidence >= self.confidence_threshold:
            return text, confidence, 'tesseract'
        
        # If AI available and confidence is low, try AI
        if self.ai_processor:
            print(f"  Tesseract confidence {confidence:.2f}, trying AI...")
            ai_text = self.ai_processor.image_to_text(image_path)
            if ai_text and len(ai_text) > len(text) * 0.5:
                return ai_text, 0.9, 'ai'  # Assume high confidence for AI
        
        # Fallback to Tesseract
        return text, confidence, 'tesseract'
