"""Settings management for the application."""
import json
import os
from pathlib import Path
from typing import List


class Settings:
    """Application settings manager."""
    
    DEFAULT_KEYWORDS = [
        'состоялся', 'состоялась', 'состоялись',
        'прошёл', 'прошла', 'прошло', 'прошли',
        'открылся', 'открылась', 'открытие',
        'закрылся', 'закрылась', 'закрытие',
        'поздравили', 'поздравление',
        'соревнования', 'турнир', 'конкурс', 'олимпиада',
        'введён', 'введена', 'введено',
        'построен', 'построена', 'построено',
        'заседание', 'собрание', 'совет',
        'праздник', 'фестиваль', 'ярмарка',
        'визит', 'прибыл', 'прибыла',
        'награждение', 'премия', 'награда',
        'событие', 'события', 'мероприятие', 'мероприятия',
        'акция', 'провели', 'организовали', 'подвели итоги',
        'обсудили', 'решили', 'утвердили', 'подписали',
        'запустили', 'отметили', 'признали', 'выбрали',
    ]
    
    def __init__(self, config_path: str = None):
        """Initialize settings."""
        if config_path is None:
            # Use app directory or user home
            app_dir = Path.home() / '.newspaper-archiver'
            app_dir.mkdir(exist_ok=True)
            self.config_path = app_dir / 'settings.json'
        else:
            self.config_path = Path(config_path)
        
        self._data = self._load()
    
    def _load(self) -> dict:
        """Load settings from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return defaults
        return {
            'event_keywords': self.DEFAULT_KEYWORDS.copy(),
            'ocr_dpi': 300,
            'ocr_language': 'rus',
            'ocr_engine': 'tesseract',  # 'tesseract', 'ai', or 'advanced'
            'ocr_dpi': 350,  # DPI for advanced OCR
            'detect_columns': True,  # Auto-detect newspaper columns
            'ai_provider': 'deepseek',  # 'deepseek', 'openai', 'google', 'kimi'
            'ai_api_key': '',  # API key for AI OCR
        }
    
    def save(self):
        """Save settings to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_keywords(self) -> List[str]:
        """Get event keywords."""
        return self._data.get('event_keywords', self.DEFAULT_KEYWORDS.copy())
    
    def set_keywords(self, keywords: List[str]):
        """Set event keywords."""
        # Filter empty strings and strip whitespace
        cleaned = [k.strip() for k in keywords if k.strip()]
        self._data['event_keywords'] = cleaned
    
    def reset_keywords(self):
        """Reset keywords to defaults."""
        self._data['event_keywords'] = self.DEFAULT_KEYWORDS.copy()
    
    def add_keyword(self, keyword: str):
        """Add a single keyword."""
        keyword = keyword.strip().lower()
        if keyword and keyword not in self._data['event_keywords']:
            self._data['event_keywords'].append(keyword)
    
    def remove_keyword(self, keyword: str):
        """Remove a keyword."""
        keyword = keyword.strip().lower()
        if keyword in self._data['event_keywords']:
            self._data['event_keywords'].remove(keyword)
    
    def get_ocr_dpi(self) -> int:
        """Get OCR DPI setting."""
        return self._data.get('ocr_dpi', 300)
    
    def set_ocr_dpi(self, dpi: int):
        """Set OCR DPI setting."""
        self._data['ocr_dpi'] = max(150, min(600, int(dpi)))
    
    def get_ocr_language(self) -> str:
        """Get OCR language."""
        return self._data.get('ocr_language', 'rus')
    
    def set_ocr_language(self, lang: str):
        """Set OCR language."""
        self._data['ocr_language'] = lang
    
    def get_ocr_engine(self) -> str:
        """Get OCR engine (tesseract or ai)."""
        return self._data.get('ocr_engine', 'tesseract')
    
    def set_ocr_engine(self, engine: str):
        """Set OCR engine."""
        self._data['ocr_engine'] = engine
    
    def get_detect_columns(self) -> bool:
        """Get column detection setting."""
        return self._data.get('detect_columns', True)
    
    def set_detect_columns(self, detect: bool):
        """Set column detection."""
        self._data['detect_columns'] = detect
    
    def get_ai_provider(self) -> str:
        """Get AI provider."""
        return self._data.get('ai_provider', 'deepseek')
    
    def set_ai_provider(self, provider: str):
        """Set AI provider."""
        self._data['ai_provider'] = provider
    
    def get_ai_api_key(self) -> str:
        """Get AI API key."""
        return self._data.get('ai_api_key', '')
    
    def set_ai_api_key(self, api_key: str):
        """Set AI API key."""
        self._data['ai_api_key'] = api_key
