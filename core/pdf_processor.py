"""PDF processing module."""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Optional
import tempfile
import os


class PDFProcessor:
    """Process PDF files - extract text or convert to images for OCR."""
    
    def __init__(self, dpi: int = 200):
        self.dpi = dpi
    
    def is_text_pdf(self, pdf_path: str, sample_pages: int = 3) -> bool:
        """Check if PDF contains extractable text or is a scan."""
        try:
            doc = fitz.open(pdf_path)
            pages_to_check = min(sample_pages, len(doc))
            
            total_text_length = 0
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                total_text_length += len(text.strip())
            
            doc.close()
            
            # If average text length per page > 100 chars, consider it text PDF
            avg_text = total_text_length / pages_to_check
            return avg_text > 100
            
        except Exception as e:
            print(f"Error checking PDF type: {e}")
            return False
    
    def extract_text(self, pdf_path: str) -> List[Tuple[int, str]]:
        """Extract text from PDF by pages.
        
        Returns:
            List of (page_number, text) tuples
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                results.append((page_num + 1, text.strip()))
            
            doc.close()
            
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        
        return results
    
    def render_pages(self, pdf_path: str, output_dir: str) -> List[Tuple[int, str]]:
        """Render PDF pages to images.
        
        Returns:
            List of (page_number, image_path) tuples
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            zoom = self.dpi / 72  # 72 is the base DPI
            mat = fitz.Matrix(zoom, zoom)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render page to image
                pix = page.get_pixmap(matrix=mat)
                
                # Save image
                image_path = output_path / f"page_{page_num + 1:03d}.png"
                pix.save(str(image_path))
                
                results.append((page_num + 1, str(image_path)))
            
            doc.close()
            
        except Exception as e:
            print(f"Error rendering PDF pages: {e}")
        
        return results
    
    def get_metadata(self, pdf_path: str) -> dict:
        """Extract PDF metadata."""
        try:
            doc = fitz.open(pdf_path)
            metadata = {
                'page_count': len(doc),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
            }
            doc.close()
            return metadata
        except Exception as e:
            print(f"Error getting PDF metadata: {e}")
            return {'page_count': 0}


def guess_date_from_filename(filename: str) -> Optional[str]:
    """Try to extract date from filename.
    
    Examples:
        "gazeta_2024_03_15.pdf" -> "2024-03-15"
        "issue_15_03_2024.pdf" -> "2024-03-15"
    """
    import re
    from datetime import datetime
    
    # Try different date patterns
    patterns = [
        r'(\d{4})[._-](\d{1,2})[._-](\d{1,2})',  # 2024_03_15 or 2024-03-15
        r'(\d{1,2})[._-](\d{1,2})[._-](\d{4})',  # 15_03_2024
        r'(\d{2})(\d{2})(\d{4})',  # 15032024
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            try:
                if len(groups[2]) == 4:  # year is last
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # year is first
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                
                # Validate date
                date = datetime(year, month, day)
                return date.strftime('%Y-%m-%d')
            except (ValueError, IndexError):
                continue
    
    return None


def guess_issue_no(filename: str) -> Optional[str]:
    """Try to extract issue number from filename."""
    import re
    
    patterns = [
        r'(?:выпуск|issue|№|n)[._-]?(\d+)',
        r'\b(\d{2,3})\b',  # Just a number (2-3 digits)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None
