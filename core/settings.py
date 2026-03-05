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
