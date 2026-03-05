"""Worker thread for background processing."""
from PySide6.QtCore import QRunnable, Signal, QObject, Slot
from pathlib import Path
import tempfile
import os

from db import Database, IssueRepository, PageRepository, EventRepository, JobRepository
from db import Issue, Page, Event, Job
from core.pdf_processor import PDFProcessor, guess_date_from_filename, guess_issue_no
from core.ocr_processor import get_ocr_processor
from core.event_extractor import EventExtractor
from core.settings import Settings


class WorkerSignals(QObject):
    """Signals for worker thread."""
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message
    log = Signal(str)  # log message


class PDFProcessingWorker(QRunnable):
    """Worker for processing PDF files."""
    
    def __init__(self, job_id: int, pdf_path: str, db_path: str = "newspaper_archiver.db"):
        super().__init__()
        self.job_id = job_id
        self.pdf_path = pdf_path
        self.db_path = db_path
        self.signals = WorkerSignals()
        self._is_running = True
    
    def run(self):
        """Main processing loop."""
        db = Database(self.db_path)
        job_repo = JobRepository(db)
        issue_repo = IssueRepository(db)
        page_repo = PageRepository(db)
        event_repo = EventRepository(db)
        
        try:
            # Update job status
            job_repo.update_status(self.job_id, "processing", 0, "Начало обработки")
            self.signals.log.emit(f"Обработка: {self.pdf_path}")
            
            # Initialize processors
            pdf_processor = PDFProcessor(dpi=200)
            
            # Get metadata
            self.signals.log.emit("Анализ PDF...")
            metadata = pdf_processor.get_metadata(self.pdf_path)
            total_pages = metadata['page_count']
            
            # Guess date and issue number from filename
            filename = Path(self.pdf_path).name
            guessed_date = guess_date_from_filename(filename)
            issue_no = guess_issue_no(filename)
            
            self.signals.log.emit(f"Страниц: {total_pages}, Дата: {guessed_date or 'не определена'}")
            
            # Create issue record
            issue = Issue(
                id=None,
                file_path=self.pdf_path,
                guessed_date=guessed_date,
                issue_no=issue_no
            )
            issue_id = issue_repo.create(issue)
            self.signals.log.emit(f"Создана запись выпуска #{issue_id}")
            
            # Check if PDF is text or scan
            self.signals.log.emit("Определение типа PDF...")
            is_text = pdf_processor.is_text_pdf(self.pdf_path)
            
            if is_text:
                self.signals.log.emit("PDF текстовый, извлечение текста...")
                self._process_text_pdf(
                    pdf_processor, issue_id, total_pages,
                    page_repo, event_repo, job_repo
                )
            else:
                self.signals.log.emit("PDF скан, запуск OCR...")
                self._process_scan_pdf(
                    pdf_processor, issue_id, total_pages,
                    page_repo, event_repo, job_repo
                )
            
            # Mark job as done
            job_repo.update_status(self.job_id, "done", 100, "Обработка завершена")
            self.signals.finished.emit(True, f"Обработано страниц: {total_pages}")
            
        except Exception as e:
            error_msg = str(e)
            self.signals.log.emit(f"ОШИБКА: {error_msg}")
            job_repo.update_status(self.job_id, "error", 0, error_msg)
            self.signals.finished.emit(False, error_msg)
    
    def _process_text_pdf(self, pdf_processor, issue_id, total_pages, page_repo, event_repo, job_repo):
        """Process text-based PDF."""
        # Load settings and get custom keywords
        settings = Settings()
        keywords = settings.get_keywords()
        extractor = EventExtractor(keywords=keywords)
        
        # Extract text from all pages
        pages_text = pdf_processor.extract_text(self.pdf_path)
        
        for i, (page_no, text) in enumerate(pages_text):
            if not self._is_running:
                break
            
            progress = int((i / total_pages) * 100)
            job_repo.update_status(self.job_id, "processing", progress, f"Страница {page_no}")
            self.signals.progress.emit(i + 1, total_pages, f"Страница {page_no}")
            
            # Save page
            page = Page(
                id=None,
                issue_id=issue_id,
                page_no=page_no,
                text=text,
                ocr_confidence=None,
                image_path=None
            )
            page_id = page_repo.create(page)
            
            # Extract events
            events = extractor.extract_events(text)
            for event_data in events:
                event = Event(
                    id=None,
                    issue_id=issue_id,
                    page_no=page_no,
                    event_date=event_data.event_date,
                    title=event_data.title,
                    description=event_data.description,
                    place=event_data.place,
                    people_json=str(event_data.people),
                    tags_json=str(event_data.tags),
                    source_quote=event_data.source_quote
                )
                event_repo.create(event)
            
            self.signals.log.emit(f"  Страница {page_no}: {len(events)} событий")
    
    def _process_scan_pdf(self, pdf_processor, issue_id, total_pages, page_repo, event_repo, job_repo):
        """Process scan PDF with OCR."""
        ocr = get_ocr_processor()
        # Load settings and get custom keywords
        settings = Settings()
        keywords = settings.get_keywords()
        extractor = EventExtractor(keywords=keywords)
        
        # Create temp directory for images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Render pages to images
            self.signals.log.emit("Рендеринг страниц в изображения...")
            pages_images = pdf_processor.render_pages(self.pdf_path, temp_dir)
            
            for i, (page_no, image_path) in enumerate(pages_images):
                if not self._is_running:
                    break
                
                progress = int((i / total_pages) * 100)
                job_repo.update_status(self.job_id, "processing", progress, f"OCR страница {page_no}")
                self.signals.progress.emit(i + 1, total_pages, f"OCR страница {page_no}")
                
                # OCR
                text, confidence = ocr.process_image(image_path)
                
                # Save page
                page = Page(
                    id=None,
                    issue_id=issue_id,
                    page_no=page_no,
                    text=text,
                    ocr_confidence=confidence,
                    image_path=image_path
                )
                page_repo.create(page)
                
                # Extract events
                events = extractor.extract_events(text)
                for event_data in events:
                    event = Event(
                        id=None,
                        issue_id=issue_id,
                        page_no=page_no,
                        event_date=event_data.event_date,
                        title=event_data.title,
                        description=event_data.description,
                        place=event_data.place,
                        people_json=str(event_data.people),
                        tags_json=str(event_data.tags),
                        source_quote=event_data.source_quote
                    )
                    event_repo.create(event)
                
                self.signals.log.emit(f"  Страница {page_no}: OCR confidence {confidence:.1%}, {len(events)} событий")
    
    def stop(self):
        """Stop the worker."""
        self._is_running = False
