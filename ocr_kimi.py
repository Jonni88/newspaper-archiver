#!/usr/bin/env python3
"""
OCR для архивных газет через Kimi API
Установка: pip install PyMuPDF Pillow requests

Запуск:
  python ocr_kimi.py файл.pdf --api-key ТВОЙ_КЛЮЧ
"""

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import requests
except ImportError:
    print("❌ Установи зависимости:")
    print("   pip install PyMuPDF Pillow requests")
    sys.exit(1)


def pdf_to_images(pdf_path, dpi=300):
    """Convert PDF pages to images."""
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render at high DPI
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append((page_num + 1, img))
    
    doc.close()
    return images


def image_to_base64(img):
    """Convert PIL Image to base64."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def ocr_with_kimi(image, api_key, prompt=None):
    """OCR using Kimi API."""
    
    default_prompt = (
        "Распознай весь текст на этой странице газеты. "
        "Сохрани структуру: заголовки, абзацы, колонки. "
        "Это советская газета 1960-х годов. "
        "Верни только текст без комментариев."
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "moonshot-v1-8k-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_to_base64(image)}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt or default_prompt
                    }
                ]
            }
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"   ❌ Ошибка API: {e}")
        return ""


def process_pdf(pdf_path, api_key, output_dir, dpi=300):
    """Process entire PDF."""
    
    print(f"📄 Файл: {pdf_path}")
    print(f"🔑 API ключ: {'*' * 10}{api_key[-6:]}")
    print(f"📁 Выходная папка: {output_dir}")
    print("-" * 50)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Convert PDF to images
    print("🖼️  Конвертация PDF в изображения...")
    images = pdf_to_images(pdf_path, dpi)
    print(f"   Найдено страниц: {len(images)}")
    
    # Process each page
    results = []
    for page_num, img in images:
        print(f"\n📃 Обработка страницы {page_num}/{len(images)}...")
        
        text = ocr_with_kimi(img, api_key)
        results.append({
            'page': page_num,
            'text': text,
            'chars': len(text)
        })
        
        print(f"   ✅ Распознано {len(text)} символов")
        
        # Save individual page
        page_file = Path(output_dir) / f"page_{page_num:03d}.txt"
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(text)
    
    # Save full result
    full_text = '\n\n'.join([f"=== СТРАНИЦА {r['page']} ===\n{r['text']}" for r in results])
    full_file = Path(output_dir) / "full_text.txt"
    with open(full_file, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    # Save JSON metadata
    json_file = Path(output_dir) / "result.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'file': Path(pdf_path).name,
            'pages': len(results),
            'total_chars': sum(r['chars'] for r in results),
            'pages_data': results
        }, f, ensure_ascii=False, indent=2)
    
    # Summary
    print(f"\n{'='*50}")
    print("✅ ГОТОВО!")
    print(f"Обработано страниц: {len(results)}")
    print(f"Всего символов: {sum(r['chars'] for r in results)}")
    print(f"\nРезультаты сохранены в: {output_dir}")
    print(f"  - full_text.txt (полный текст)")
    print(f"  - page_001.txt, page_002.txt... (по страницам)")
    print(f"  - result.json (метаданные)")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='OCR для газет через Kimi API')
    parser.add_argument('pdf', help='PDF файл для обработки')
    parser.add_argument('--api-key', '-k', help='Kimi API ключ')
    parser.add_argument('--output', '-o', default='ocr_result', help='Выходная папка')
    parser.add_argument('--dpi', type=int, default=300, help='DPI (по умолчанию 300)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('KIMI_API_KEY')
    if not api_key:
        print("❌ Нужен API ключ Kimi!")
        print("   Получи тут: https://platform.moonshot.cn")
        print("   Затем запусти с --api-key или установи переменную KIMI_API_KEY")
        sys.exit(1)
    
    # Check file exists
    if not Path(args.pdf).exists():
        print(f"❌ Файл не найден: {args.pdf}")
        sys.exit(1)
    
    # Process
    process_pdf(args.pdf, api_key, args.output, args.dpi)


if __name__ == '__main__':
    main()
