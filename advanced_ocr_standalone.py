# advanced_ocr_standalone.py
# Запускайте этот скрипт отдельно с установленным OpenCV
# 
# Установка зависимостей:
#   pip install opencv-python numpy pytesseract pillow PyMuPDF
#
# Запуск:
#   python advanced_ocr_standalone.py input.pdf output_folder

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.advanced_ocr import AdvancedOCRProcessor

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python advanced_ocr_standalone.py input.pdf [output_folder]")
        print("")
        print("Пример:")
        print("  python advanced_ocr_standalone.py gazeta.pdf ./ocr_result")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "ocr_output"
    
    if not os.path.exists(input_path):
        print(f"❌ Файл не найден: {input_path}")
        sys.exit(1)
    
    print(f"🔍 Обработка: {input_path}")
    print(f"📁 Результат: {output_dir}")
    print("-" * 50)
    
    try:
        processor = AdvancedOCRProcessor(dpi=350, language='rus')
        
        if input_path.lower().endswith('.pdf'):
            results = processor.process_pdf(input_path, output_dir)
            
            # Summary
            total_chars = sum(len(r['text']) for r in results)
            avg_conf = sum(r['confidence'] for r in results) / len(results)
            
            print(f"\n{'='*50}")
            print(f"✅ ГОТОВО!")
            print(f"Обработано страниц: {len(results)}")
            print(f"Всего символов: {total_chars}")
            print(f"Средняя уверенность: {avg_conf:.2f}")
            print(f"Результаты сохранены в: {os.path.abspath(output_dir)}")
            print(f"\nФайлы:")
            print(f"  - page_001/page.txt (распознанный текст)")
            print(f"  - page_001/page.json (метаданные)")
            print(f"  - page_001/page_debug.png (отладочное изображение)")
            print(f"  - page_001/columns/ (отдельные колонки)")
            
        else:
            result = processor.process_page(input_path, output_dir)
            print(f"\n✅ Распознано {len(result['text'])} символов")
            print(f"Уверенность: {result['confidence']:.2f}")
            print(f"Колонок: {len(result['columns'])}")
            
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("\nУстановите зависимости:")
        print("  pip install opencv-python numpy pytesseract pillow PyMuPDF")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
