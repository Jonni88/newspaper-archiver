# rename_from_table.py - Переименование по таблице
import os
import csv
from pathlib import Path

def rename_from_csv(folder_path, csv_path):
    """
    CSV формат:
    old_name,new_name
    19.pdf,1985-03-15.pdf
    20.pdf,1985-03-22.pdf
    """
    folder = Path(folder_path)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_name = row['old_name']
            new_name = row['new_name']
            
            old_path = folder / old_name
            new_path = folder / new_name
            
            if old_path.exists():
                old_path.rename(new_path)
                print(f"✅ {old_name} → {new_name}")
            else:
                print(f"✗ {old_name} не найден")

def create_template(folder_path):
    """Создает шаблон CSV для заполнения."""
    folder = Path(folder_path)
    pdf_files = sorted(folder.glob("*.pdf"))
    
    csv_path = folder / "rename_template.csv"
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['old_name', 'new_name', 'date_hint'])
        
        for pdf in pdf_files:
            # Пробуем извлечь год из метаданных
            hint = ""
            try:
                import fitz
                doc = fitz.open(pdf)
                meta = doc.metadata
                if meta.get('creationDate'):
                    hint = meta['creationDate'][:10]
                doc.close()
            except:
                pass
            
            writer.writerow([pdf.name, '', hint])
    
    print(f"📄 Шаблон создан: {csv_path}")
    print("Заполни колонку new_name и запусти скрипт снова")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  Создать шаблон: python rename_from_table.py /путь/к/папке")
        print("  Переименовать:  python rename_from_table.py /путь/к/папке /путь/к/table.csv")
        exit(1)
    
    folder = sys.argv[1]
    
    if len(sys.argv) == 2:
        create_template(folder)
    else:
        csv_file = sys.argv[2]
        rename_from_csv(folder, csv_file)
