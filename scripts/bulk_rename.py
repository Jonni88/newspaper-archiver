# bulk_rename.py - Переименование файлов по дате из PDF
import os
import re
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Установи: pip install PyMuPDF")
    exit(1)

def extract_date_from_pdf(filepath):
    """Извлекает дату из метаданных или текста PDF."""
    try:
        doc = fitz.open(filepath)
        
        # Пробуем метаданные
        meta = doc.metadata
        if meta.get('creationDate'):
            # Формат: D:20240305120000
            match = re.search(r'D:(\d{4})(\d{2})(\d{2})', meta['creationDate'])
            if match:
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        if meta.get('modDate'):
            match = re.search(r'D:(\d{4})(\d{2})(\d{2})', meta['modDate'])
            if match:
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        # Пробуем первую страницу
        text = doc[0].get_text()[:1000]
        doc.close()
        
        # Ищем даты в тексте: 15.03.1985, 15 марта 1985
        patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    d, m, y = match.groups()
                    if m.isdigit():
                        return f"{y}-{int(m):02d}-{int(d):02d}"
                    else:
                        months = {'января':1, 'февраля':2, 'марта':3, 'апреля':4, 'мая':5, 'июня':6,
                                  'июля':7, 'августа':8, 'сентября':9, 'октября':10, 'ноября':11, 'декабря':12}
                        month_num = months.get(m.lower(), 1)
                        return f"{y}-{month_num:02d}-{int(d):02d}"
        
        return None
    except Exception as e:
        print(f"Ошибка {filepath}: {e}")
        return None

def main():
    folder = input("Папка с PDF: ").strip()
    folder = Path(folder)
    
    if not folder.exists():
        print("Папка не найдена!")
        return
    
    pdf_files = sorted(folder.glob("*.pdf"))
    print(f"Найдено {len(pdf_files)} PDF файлов\n")
    
    renamed = 0
    for pdf in pdf_files:
        print(f"Обработка: {pdf.name}")
        date_str = extract_date_from_pdf(pdf)
        
        if date_str:
            new_name = f"{date_str}.pdf"
            new_path = pdf.parent / new_name
            
            # Если файл существует, добавляем номер
            counter = 1
            while new_path.exists():
                new_name = f"{date_str}_{counter}.pdf"
                new_path = pdf.parent / new_name
                counter += 1
            
            print(f"  → {new_name}")
            pdf.rename(new_path)
            renamed += 1
        else:
            print(f"  ✗ Дата не найдена")
    
    print(f"\n✅ Переименовано: {renamed} из {len(pdf_files)}")

if __name__ == "__main__":
    main()
