"""Event extraction from text."""
import re
from typing import List, Optional
from dataclasses import dataclass
import json


@dataclass
class ExtractedEvent:
    """Extracted event data."""
    title: Optional[str]
    description: Optional[str]
    event_date: Optional[str]
    place: Optional[str]
    people: List[str]
    tags: List[str]
    source_quote: str


class EventExtractor:
    """Extract events from newspaper text."""
    
    # Keywords indicating events
    EVENT_KEYWORDS = [
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
        # Added event-related words
        'событие', 'события', 'мероприятие', 'мероприятия',
        'акция', 'провели', 'организовали', 'подвели итоги',
        'обсудили', 'решили', 'утвердили', 'подписали',
        'запустили', 'отметили', 'признали', 'выбрали',
    ]
    
    # Month names for date extraction
    MONTHS_RU = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
    }
    
    def __init__(self):
        self.event_pattern = re.compile(
            r'[^.!?]*(?:' + '|'.join(self.EVENT_KEYWORDS) + r')[^.!?]*[.!?]',
            re.IGNORECASE
        )
    
    def extract_events(self, text: str) -> List[ExtractedEvent]:
        """Extract events from text."""
        events = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence contains event keywords
            if self._contains_event_keywords(sentence):
                event = self._parse_event(sentence)
                if event:
                    events.append(event)
        
        return events
    
    def _contains_event_keywords(self, text: str) -> bool:
        """Check if text contains event keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.EVENT_KEYWORDS)
    
    def _parse_event(self, text: str) -> Optional[ExtractedEvent]:
        """Parse event from text."""
        # Extract date
        event_date = self._extract_date(text)
        
        # Extract place
        place = self._extract_place(text)
        
        # Extract people (simple heuristic)
        people = self._extract_people(text)
        
        # Generate title (first part of sentence)
        title = self._generate_title(text)
        
        # Generate description
        description = self._generate_description(text)
        
        # Extract tags
        tags = self._extract_tags(text)
        
        return ExtractedEvent(
            title=title,
            description=description,
            event_date=event_date,
            place=place,
            people=people,
            tags=tags,
            source_quote=text[:300]  # First 300 chars as quote
        )
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text."""
        # Pattern: 15 марта, 15 марта 2024, 15.03.2024, 15.03
        patterns = [
            r'(\d{1,2})\s+(' + '|'.join(self.MONTHS_RU.keys()) + r')\s+(\d{4})',
            r'(\d{1,2})\s+(' + '|'.join(self.MONTHS_RU.keys()) + r')',
            r'(\d{1,2})[.](\d{1,2})[.](\d{4})',
            r'(\d{1,2})[.](\d{1,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 3:
                        if groups[1].isdigit():
                            # Numeric format: 15.03.2024
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            # Text format: 15 марта 2024
                            day = int(groups[0])
                            month = self.MONTHS_RU.get(groups[1].lower(), 1)
                            year = int(groups[2])
                        return f"{year:04d}-{month:02d}-{day:02d}"
                    elif len(groups) == 2:
                        if groups[1].isdigit():
                            day, month = int(groups[0]), int(groups[1])
                            year = 2024  # Default year
                        else:
                            day = int(groups[0])
                            month = self.MONTHS_RU.get(groups[1].lower(), 1)
                            year = 2024
                        return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_place(self, text: str) -> Optional[str]:
        """Extract place from text (after 'в', 'на', 'у')."""
        # Pattern: в/на/у [Place]
        patterns = [
            r'в\s+(?:г\.?|городе|селе|посёлке|деревне)?\s*([А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)',
            r'на\s+([А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                place = match.group(1).strip()
                # Filter out common non-place words
                if place.lower() not in ['тот', 'этот', 'том', 'этом', 'всех']:
                    return place
        
        return None
    
    def _extract_people(self, text: str) -> List[str]:
        """Extract people names (simple heuristic)."""
        # Pattern: Name Surname (capitalized words)
        pattern = r'([А-Я][а-я]+\s+[А-Я][а-я]+)'
        matches = re.findall(pattern, text)
        
        # Filter short matches and common words
        people = []
        for match in matches:
            if len(match) > 6:  # At least "Иван Ив"
                people.append(match)
        
        return list(set(people))[:5]  # Max 5 people, unique
    
    def _generate_title(self, text: str) -> Optional[str]:
        """Generate short title from text."""
        # First 5-7 words or until first comma
        words = text.split()
        if len(words) > 7:
            return ' '.join(words[:7]) + '...'
        return text[:50] if len(text) > 50 else text
    
    def _generate_description(self, text: str) -> Optional[str]:
        """Generate description from text."""
        # Return full sentence or first 200 chars
        return text[:200] if len(text) > 200 else text
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from text."""
        tags = []
        text_lower = text.lower()
        
        # Category tags
        if any(w in text_lower for w in ['соревнование', 'турнир', 'спорт', 'игра']):
            tags.append('спорт')
        if any(w in text_lower for w in ['школа', 'ученик', 'учитель', 'образование']):
            tags.append('образование')
        if any(w in text_lower for w in ['больница', 'врач', 'здоровье', 'медицина']):
            tags.append('здоровье')
        if any(w in text_lower for w in ['праздник', 'концерт', 'фестиваль', 'культура']):
            tags.append('культура')
        if any(w in text_lower for w in ['строительство', 'ремонт', 'дорога', 'объект']):
            tags.append('строительство')
        if any(w in text_lower for w in ['совет', 'депутат', 'заседание', 'администрация']):
            tags.append('власть')
        
        return tags
