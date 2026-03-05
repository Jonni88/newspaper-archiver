# diagnostic.py - Диагностика почему не находятся события
import sys
import os
from pathlib import Path

# Добавляем путь к модулю
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_tesseract():
    """Проверка установки Tesseract."""
    import shutil
    
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        print(f"✅ Tesseract найден: {tesseract_path}")
        
        # Проверяем версию
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        print(f"   Версия: {result.stdout.split(chr(10))[0]}")
        return True
    else:
        print("❌ Tesseract НЕ найден в PATH!")
        print("   Установи Tesseract OCR:")
        print("   1. Скачай: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   2. При установке выбери 'Add to PATH'")
        return False

def test_pdf_extraction(pdf_path):
    """Тест извлечения текста из одного PDF."""
    try:
        from core.pdf_processor import PDFProcessor
        from core.ocr_processor import get_ocr_processor
        from core.event_extractor import EventExtractor
        from core.settings import Settings
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("   Запусти из папки scripts: python diagnostic.py")
        return
    
    print(f"\n📄 Тестирование: {pdf_path}")
    print("-" * 50)
    
    # 1. Проверяем тип PDF
    processor = PDFProcessor(dpi=200)
    is_text = processor.is_text_pdf(pdf_path)
    
    if is_text:
        print("📋 Тип PDF: текстовый")
    else:
        print("📷 Тип PDF: скан (нужен OCR)")
    
    # 2. Пробуем извлечь текст
    print("\n📝 Извлечение текста...")
    
    if is_text:
        pages = processor.extract_text(pdf_path)
        text = pages[0][1] if pages else ""
    else:
        # OCR
        pages = processor.render_pages(pdf_path, max_pages=1)
        if not pages:
            print("❌ Не удалось отрендерить страницу!")
            return
        
        ocr = get_ocr_processor()
        text = ocr.image_to_text(pages[0][1])
        
        # Cleanup
        os.remove(pages[0][1])
    
    print(f"   Извлечено символов: {len(text)}")
    
    if len(text) < 100:
        print("⚠️  Мало текста! Возможные причины:")
        print("   - Низкое качество скана")
        print("   - Tesseract неправильно распознаёт")
        print("   - PDF защищён от копирования")
    
    # 3. Показываем образец текста
    print("\n--- Первые 300 символов текста ---")
    print(text[:300])
    print("---")
    
    # 4. Проверяем ключевые слова
    print("\n🔑 Проверка ключевых слов:")
    settings = Settings()
    keywords = settings.get_keywords()
    print(f"   Загружено слов: {len(keywords)}")
    
    text_lower = text.lower()
    found_keywords = []
    for kw in keywords[:20]:  # Первые 20
        if kw in text_lower:
            found_keywords.append(kw)
    
    if found_keywords:
        print(f"   ✅ Найдены в тексте: {', '.join(found_keywords[:5])}")
    else:
        print("   ❌ Ни одно ключевое слово не найдено!")
        print("   Проверь вкладку 'Настройки' и добавь слова из текста выше")
    
    # 5. Пробуем найти события
    print("\n🎯 Поиск событий...")
    extractor = EventExtractor(keywords=keywords)
    events = extractor.extract_events(text)
    
    print(f"   Найдено событий: {len(events)}")
    
    if events:
        for i, event in enumerate(events[:3], 1):
            print(f"\n   {i}. {event.title}")
            print(f"      Дата: {event.event_date or 'не найдена'}")
    else:
        print("\n   💡 Советы:")
        print("   1. Открой 'Настройки' и посмотри список ключевых слов")
        print("   2. Добавь слова которые видишь в тексте выше")
        print("   3. Например: 'прошло', 'состоялось', 'открылось'")

def main():
    print("🔍 ДИАГНОСТИКА Newspaper Archiver\n")
    print("=" * 50)
    
    # 1. Проверка Tesseract
    print("\n1. Проверка Tesseract OCR:")
    print("-" * 30)
    tesseract_ok = check_tesseract()
    
    if not tesseract_ok:
        input("\nНажми Enter для выхода...")
        return
    
    # 2. Тест PDF
    print("\n2. Тестирование PDF:")
    print("-" * 30)
    
    # Ищем PDF в папке с программой
    pdf_files = list(Path('.').glob('*.pdf'))
    if not pdf_files:
        pdf_files = list(Path('../').glob('*.pdf'))
    
    if not pdf_files:
        path = input("\nВведи путь к PDF файлу для теста: ").strip()
        if Path(path).exists():
            test_pdf_extraction(path)
    else:
        print(f"Найдено {len(pdf_files)} PDF файлов")
        test_pdf_extraction(str(pdf_files[0]))
    
    print("\n" + "=" * 50)
    input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    main()
