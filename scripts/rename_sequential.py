# rename_sequential.py - Переименование по порядку с заданным шагом
import os
from pathlib import Path
from datetime import datetime, timedelta

def rename_sequential(folder_path, start_date_str, step_days=7):
    """
    Переименовывает файлы по порядку, добавляя даты с шагом.
    
    folder_path: папка с PDF
    start_date_str: начальная дата (YYYY-MM-DD)
    step_days: шаг в днях (7 для еженедельной газеты)
    """
    folder = Path(folder_path)
    pdf_files = sorted(folder.glob("*.pdf"))
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    
    print(f"Найдено {len(pdf_files)} файлов")
    print(f"Начальная дата: {start_date_str}")
    print(f"Шаг: {step_days} дней\n")
    
    for i, pdf in enumerate(pdf_files):
        current_date = start_date + timedelta(days=step_days * i)
        new_name = current_date.strftime("%Y-%m-%d") + ".pdf"
        new_path = folder / new_name
        
        # Если файл существует, добавляем букву
        counter = ord('a')  # 'a'
        while new_path.exists():
            new_name = current_date.strftime("%Y-%m-%d") + f"_{chr(counter)}.pdf"
            new_path = folder / new_name
            counter += 1
        
        print(f"{pdf.name} → {new_name}")
        pdf.rename(new_path)
    
    print(f"\n✅ Переименовано {len(pdf_files)} файлов")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Использование:")
        print("  python rename_sequential.py /путь/к/папке YYYY-MM-DD")
        print("")
        print("Пример (еженедельная газета с 5 января 1985):")
        print("  python rename_sequential.py ./gazety 1985-01-05")
        print("")
        print("Пример (ежедневная газета):")
        print("  python rename_sequential.py ./gazety 1985-01-01")
        exit(1)
    
    folder = sys.argv[1]
    start_date = sys.argv[2]
    
    # Для еженедельной газеты
    rename_sequential(folder, start_date, step_days=7)
