"""Advanced OCR pipeline for newspaper processing.

Features:
- High-quality PDF rendering (300-350 DPI)
- Image preprocessing with OpenCV
- Automatic column detection
- Column-wise OCR processing
- Text sorting by coordinates
"""
import os
import json
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import tempfile

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None
    print("Warning: OpenCV not installed. Advanced OCR will not work.")
    print("Install: pip install opencv-python")


class ImagePreprocessor:
    """Preprocess images for better OCR results."""
    
    def __init__(self, target_dpi: int = 350):
        self.target_dpi = target_dpi
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV not available. Install: pip install opencv-python")
    
    def preprocess(self, image_path: str, output_path: str = None) -> str:
        """
        Full preprocessing pipeline.
        
        Returns:
            Path to processed image
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Step 1: Convert to grayscale
        gray = self._to_grayscale(img)
        
        # Step 2: Denoise
        denoised = self._denoise(gray)
        
        # Step 3: Enhance contrast
        enhanced = self._enhance_contrast(denoised)
        
        # Step 4: Adaptive threshold
        binary = self._adaptive_threshold(enhanced)
        
        # Save result
        if output_path is None:
            base = Path(image_path).stem
            output_path = str(Path(image_path).parent / f"{base}_preprocessed.png")
        
        cv2.imwrite(output_path, binary)
        return output_path
    
    def _to_grayscale(self, img) -> any:
        """Convert to grayscale."""
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img
    
    def _denoise(self, img) -> any:
        """Apply Gaussian blur to reduce noise."""
        return cv2.GaussianBlur(img, (5, 5), 0)
    
    def _enhance_contrast(self, img) -> any:
        """Enhance contrast using CLAHE."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(img)
    
    def _adaptive_threshold(self, img) -> any:
        """Apply adaptive thresholding."""
        return cv2.adaptiveThreshold(
            img, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 
            11, 2
        )
    
    def create_debug_image(self, original_path: str, output_path: str):
        """Create side-by-side comparison for debugging."""
        original = cv2.imread(original_path)
        preprocessed_path = self.preprocess(original_path)
        preprocessed = cv2.imread(preprocessed_path, cv2.IMREAD_GRAYSCALE)
        
        # Convert preprocessed to BGR for concatenation
        preprocessed_bgr = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2BGR)
        
        # Resize to same height if needed
        h1, w1 = original.shape[:2]
        h2, w2 = preprocessed_bgr.shape[:2]
        
        if h1 != h2:
            scale = h1 / h2
            new_w = int(w2 * scale)
            preprocessed_bgr = cv2.resize(preprocessed_bgr, (new_w, h1))
        
        # Concatenate horizontally
        debug = np.hstack([original, preprocessed_bgr])
        
        # Add labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(debug, 'ORIGINAL', (10, 30), font, 1, (0, 255, 0), 2)
        cv2.putText(debug, 'PREPROCESSED', (w1 + 10, 30), font, 1, (0, 255, 0), 2)
        
        cv2.imwrite(output_path, debug)
        return output_path


class ColumnDetector:
    """Detect and extract columns from newspaper pages."""
    
    def __init__(self, min_column_width: int = 200):
        self.min_column_width = min_column_width
    
    def detect_columns(self, image_path: str) -> List[Tuple[int, int, int, int]]:
        """
        Detect columns in newspaper image.
        
        Returns:
            List of (x, y, width, height) for each column
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        height, width = img.shape
        
        # Calculate vertical projection (sum of pixels in each column)
        # Inverted: text is black (0), background is white (255)
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        vertical_proj = np.sum(binary, axis=0)
        
        # Normalize
        vertical_proj = vertical_proj / np.max(vertical_proj)
        
        # Find column boundaries (gaps between columns)
        # Gaps have low projection values
        threshold = 0.1  # 10% of max
        is_gap = vertical_proj < threshold
        
        # Find gap regions
        gaps = []
        in_gap = False
        gap_start = 0
        
        for i, gap in enumerate(is_gap):
            if gap and not in_gap:
                gap_start = i
                in_gap = True
            elif not gap and in_gap:
                gaps.append((gap_start, i))
                in_gap = False
        
        if in_gap:
            gaps.append((gap_start, len(is_gap)))
        
        # Determine column boundaries from gaps
        columns = []
        
        if len(gaps) >= 3:
            # Multiple gaps detected - use them
            # Columns are between gaps
            prev_end = 0
            for gap_start, gap_end in gaps:
                col_width = gap_start - prev_end
                if col_width > self.min_column_width:
                    columns.append((prev_end, 0, col_width, height))
                prev_end = gap_end
            
            # Last column
            if width - prev_end > self.min_column_width:
                columns.append((prev_end, 0, width - prev_end, height))
        
        elif len(gaps) == 0 or len(columns) < 2:
            # No clear gaps detected - use fixed column count
            # Common newspaper layouts: 3, 4, or 5 columns
            column_counts = [4, 3, 5]
            
            for count in column_counts:
                col_width = width // count
                cols = []
                for i in range(count):
                    x = i * col_width
                    cols.append((x, 0, col_width, height))
                
                # Check if columns seem reasonable
                if self._validate_columns(img, cols):
                    columns = cols
                    break
            else:
                # Fallback: 3 equal columns
                col_width = width // 3
                columns = [(i * col_width, 0, col_width, height) for i in range(3)]
        
        return columns
    
    def _validate_columns(self, img, columns: List[Tuple]) -> bool:
        """Check if detected columns contain reasonable amount of text."""
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        for x, y, w, h in columns:
            col_region = binary[y:y+h, x:x+w]
            text_density = np.sum(col_region > 0) / (w * h)
            
            # If any column has very low text density, reject this layout
            if text_density < 0.05:  # Less than 5% text
                return False
        
        return True
    
    def extract_columns(self, image_path: str, output_dir: str) -> List[str]:
        """
        Extract columns as separate images.
        
        Returns:
            List of paths to column images
        """
        img = cv2.imread(image_path)
        columns = self.detect_columns(image_path)
        
        output_paths = []
        for i, (x, y, w, h) in enumerate(columns):
            col_img = img[y:y+h, x:x+w]
            output_path = os.path.join(output_dir, f"col_{i+1}.png")
            cv2.imwrite(output_path, col_img)
            output_paths.append(output_path)
        
        return output_paths
    
    def draw_columns(self, image_path: str, output_path: str):
        """Draw detected column boundaries on image (for debugging)."""
        img = cv2.imread(image_path)
        columns = self.detect_columns(image_path)
        
        for i, (x, y, w, h) in enumerate(columns):
            # Draw rectangle
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
            # Add label
            cv2.putText(img, f'Col {i+1}', (x+10, y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imwrite(output_path, img)
        return output_path


class AdvancedOCRProcessor:
    """Advanced OCR pipeline for newspapers."""
    
    def __init__(self, dpi: int = 350, language: str = 'rus'):
        self.dpi = dpi
        self.language = language
        self.preprocessor = ImagePreprocessor(target_dpi=dpi)
        self.column_detector = ColumnDetector()
        
        # Try to import Tesseract
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except ImportError:
            self.tesseract_available = False
            print("Warning: pytesseract not available")
    
    def process_page(self, image_path: str, output_dir: str) -> Dict:
        """
        Process single page through full pipeline.
        
        Returns:
            Dict with:
            - text: Full extracted text
            - confidence: OCR confidence
            - columns: List of column texts
            - debug_images: Paths to debug images
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        base_name = Path(image_path).stem
        
        results = {
            'text': '',
            'confidence': 0.0,
            'columns': [],
            'debug_images': {}
        }
        
        # Step 1: Preprocess
        print(f"  Preprocessing {base_name}...")
        preprocessed_path = self.preprocessor.preprocess(
            image_path, 
            os.path.join(output_dir, f"{base_name}_preprocessed.png")
        )
        results['debug_images']['preprocessed'] = preprocessed_path
        
        # Create debug comparison
        debug_path = os.path.join(output_dir, f"{base_name}_debug.png")
        self.preprocessor.create_debug_image(image_path, debug_path)
        results['debug_images']['comparison'] = debug_path
        
        # Step 2: Detect columns
        print(f"  Detecting columns...")
        columns_debug = os.path.join(output_dir, f"{base_name}_columns.png")
        self.column_detector.draw_columns(preprocessed_path, columns_debug)
        results['debug_images']['columns'] = columns_debug
        
        # Step 3: Extract columns
        col_dir = os.path.join(output_dir, 'columns')
        Path(col_dir).mkdir(exist_ok=True)
        column_paths = self.column_detector.extract_columns(preprocessed_path, col_dir)
        
        # Step 4: OCR each column
        print(f"  Running OCR on {len(column_paths)} columns...")
        all_texts = []
        confidences = []
        
        for i, col_path in enumerate(column_paths):
            text, conf = self._ocr_image(col_path)
            all_texts.append(text)
            confidences.append(conf)
            results['columns'].append({
                'column': i + 1,
                'text': text,
                'confidence': conf
            })
        
        # Step 5: Sort columns left-to-right and combine
        columns_info = self.column_detector.detect_columns(preprocessed_path)
        sorted_columns = sorted(zip(columns_info, all_texts), key=lambda x: x[0][0])
        
        full_text = '\n\n'.join([text for _, text in sorted_columns])
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        results['text'] = full_text
        results['confidence'] = avg_confidence
        
        return results
    
    def _ocr_image(self, image_path: str) -> Tuple[str, float]:
        """Run OCR on single image."""
        if not self.tesseract_available:
            return "", 0.0
        
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            
            # OCR with psm 6 (assume uniform block of text)
            custom_config = f'--oem 3 --psm 6 -l {self.language}'
            text = self.pytesseract.image_to_string(img, config=custom_config)
            
            # Get confidence
            data = self.pytesseract.image_to_data(
                img, lang=self.language, 
                config=custom_config,
                output_type=self.pytesseract.Output.DICT
            )
            confs = [int(c) for c in data['conf'] if int(c) > 0]
            confidence = sum(confs) / len(confs) / 100 if confs else 0.5
            
            return text.strip(), confidence
            
        except Exception as e:
            print(f"    OCR error: {e}")
            return "", 0.0
    
    def process_pdf(self, pdf_path: str, output_dir: str) -> List[Dict]:
        """
        Process all pages of PDF.
        
        Returns:
            List of results per page
        """
        from core.pdf_processor import PDFProcessor
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Render PDF pages
        print(f"Rendering {pdf_path} at {self.dpi} DPI...")
        renderer = PDFProcessor(dpi=self.dpi)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pages = renderer.render_pages(pdf_path, temp_dir)
            
            results = []
            for page_no, image_path in pages:
                print(f"\nProcessing page {page_no}...")
                page_dir = os.path.join(output_dir, f"page_{page_no:03d}")
                
                result = self.process_page(image_path, page_dir)
                result['page_no'] = page_no
                results.append(result)
                
                # Save text
                text_path = os.path.join(page_dir, "page.txt")
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(result['text'])
                
                # Save metadata
                meta_path = os.path.join(page_dir, "page.json")
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'page_no': page_no,
                        'confidence': result['confidence'],
                        'columns': len(result['columns'])
                    }, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ Page {page_no}: {len(result['text'])} chars, confidence: {result['confidence']:.2f}")
            
            return results


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python advanced_ocr.py <PDF или изображение> [выходная_папка]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "ocr_output"
    
    processor = AdvancedOCRProcessor(dpi=350, language='rus')
    
    if input_path.lower().endswith('.pdf'):
        results = processor.process_pdf(input_path, output_dir)
        
        # Summary
        total_chars = sum(len(r['text']) for r in results)
        avg_conf = sum(r['confidence'] for r in results) / len(results)
        
        print(f"\n{'='*50}")
        print(f"ОБРАБОТАНО: {len(results)} страниц")
        print(f"Всего символов: {total_chars}")
        print(f"Средняя уверенность: {avg_conf:.2f}")
        print(f"Результат: {output_dir}")
    else:
        result = processor.process_page(input_path, output_dir)
        print(f"\nРаспознано {len(result['text'])} символов")
        print(f"Уверенность: {result['confidence']:.2f}")
        print(f"\nПервые 500 символов:")
        print(result['text'][:500])
