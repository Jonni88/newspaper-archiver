"""Generate "This Month" reports from archived newspapers."""
from typing import List, Dict
from datetime import datetime
from collections import defaultdict


class MonthlyReportGenerator:
    """Generate monthly reports from events."""
    
    MONTH_NAMES = {
        1: ('Январь', 'января'),
        2: ('Февраль', 'февраля'),
        3: ('Март', 'марта'),
        4: ('Апрель', 'апреля'),
        5: ('Май', 'мая'),
        6: ('Июнь', 'июня'),
        7: ('Июль', 'июля'),
        8: ('Август', 'августа'),
        9: ('Сентябрь', 'сентября'),
        10: ('Октябрь', 'октября'),
        11: ('Ноябрь', 'ноября'),
        12: ('Декабрь', 'декабря'),
    }
    
    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
    
    def generate_monthly_report(self, month: int, year: int = None) -> Dict:
        """
        Generate report for specific month.
        
        Args:
            month: Month number (1-12)
            year: Specific year or None for all years
            
        Returns:
            Dict with report data
        """
        from db import EventRepository
        
        event_repo = EventRepository(self.db)
        
        # Get all events
        if year:
            # Filter by specific year
            events = event_repo.get_by_year_month(year, month)
        else:
            # Get all events for this month across all years
            events = event_repo.get_by_month(month)
        
        # Group by year
        grouped = defaultdict(list)
        for event in events:
            event_year = event.event_date.year if event.event_date else 0
            grouped[event_year].append(event)
        
        # Sort years descending
        sorted_years = sorted(grouped.keys(), reverse=True)
        
        return {
            'month': month,
            'month_name': self.MONTH_NAMES[month][0],
            'month_name_genitive': self.MONTH_NAMES[month][1],
            'year': year,
            'total_events': len(events),
            'years': {
                y: grouped[y] for y in sorted_years
            },
        }
    
    def format_telegram_post(self, report: Dict, max_events_per_year: int = 3) -> str:
        """
        Format report as Telegram/VK post.
        
        Args:
            report: Report data from generate_monthly_report
            max_events_per_year: Max events to show per year
            
        Returns:
            Formatted text for social media
        """
        lines = [
            f"📅 Что писали газеты в {report['month_name_genitive']}",
            "",
        ]
        
        for year, events in report['years'].items():
            lines.append(f"📰 {year} год:")
            
            for i, event in enumerate(events[:max_events_per_year], 1):
                day = event.event_date.day if event.event_date else '?'
                title = event.title or 'Без названия'
                lines.append(f"  {day} — {title}")
            
            if len(events) > max_events_per_year:
                lines.append(f"  ... и ещё {len(events) - max_events_per_year} событий")
            
            lines.append("")
        
        lines.extend([
            "Источник: Архив газет Олёкминского района",
            "#историяОлёкмы #этотмесяц",
        ])
        
        return "\n".join(lines)
    
    def format_detailed_report(self, report: Dict) -> str:
        """Generate detailed text report."""
        lines = [
            f"ОТЧЁТ: Что писали газеты в {report['month_name_genitive']}",
            f"Всего событий: {report['total_events']}",
            "=" * 50,
            "",
        ]
        
        for year, events in report['years'].items():
            lines.append(f"\n{year} ГОД ({len(events)} событий)")
            lines.append("-" * 30)
            
            for event in events:
                day = event.event_date.day if event.event_date else '?'
                lines.append(f"\n{day} {report['month_name_genitive']}:")
                lines.append(f"  Заголовок: {event.title or 'Нет'}")
                lines.append(f"  Описание: {event.description or 'Нет'}")
                lines.append(f"  Место: {event.place or 'Не указано'}")
                if event.source_quote:
                    lines.append(f"  Цитата: {event.source_quote[:150]}...")
        
        return "\n".join(lines)
    
    def export_to_csv(self, report: Dict, filepath: str):
        """Export report to CSV file."""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Год', 'День', 'Месяц', 'Заголовок', 'Описание', 
                'Место', 'Источник', 'Страница'
            ])
            
            for year, events in report['years'].items():
                for event in events:
                    writer.writerow([
                        year,
                        event.event_date.day if event.event_date else '',
                        report['month_name_genitive'],
                        event.title or '',
                        event.description or '',
                        event.place or '',
                        event.source_quote or '',
                        event.page_no or '',
                    ])
