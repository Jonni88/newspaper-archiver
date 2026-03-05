"""Main window UI."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QFileDialog, QTableWidget, QTableWidgetItem,
    QTabWidget, QSplitter, QMessageBox, QHeaderView,
    QLineEdit, QSpinBox, QComboBox, QGroupBox,
    QPlainTextEdit, QApplication
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction
from pathlib import Path
from datetime import datetime

from db import Database, JobRepository, IssueRepository, EventRepository
from db import Job
from core import PDFProcessingWorker, Settings
from core.monthly_report import MonthlyReportGenerator


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Архив газет Олёкминска")
        self.setMinimumSize(1200, 800)
        
        # Initialize database
        self.db = Database()
        self.job_repo = JobRepository(self.db)
        self.issue_repo = IssueRepository(self.db)
        self.event_repo = EventRepository(self.db)
        
        # Initialize settings
        self.settings = Settings()
        
        # Thread pool for workers
        self.thread_pool = QThreadPool()
        
        # Current jobs
        self.current_jobs = {}
        
        self._create_ui()
        self._create_menu()
        self._refresh_jobs()
    
    def _create_ui(self):
        """Create main UI."""
        # Central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tab 1: Import
        self.import_tab = self._create_import_tab()
        self.tabs.addTab(self.import_tab, "📥 Импорт")
        
        # Tab 2: Events
        self.events_tab = self._create_events_tab()
        self.tabs.addTab(self.events_tab, "📋 События")
        
        # Tab 3: This Day
        self.this_day_tab = self._create_this_day_tab()
        self.tabs.addTab(self.this_day_tab, "📅 Этот день")
        
        # Tab 4: This Month
        self.this_month_tab = self._create_this_month_tab()
        self.tabs.addTab(self.this_month_tab, "📰 Этот месяц")
        
        # Tab 5: Settings
        self.settings_tab = self._create_settings_tab()
        self.tabs.addTab(self.settings_tab, "⚙️ Настройки")
    
    def _create_import_tab(self):
        """Create import tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_select_pdf = QPushButton("📄 Выбрать PDF")
        self.btn_select_pdf.clicked.connect(self._select_pdf)
        button_layout.addWidget(self.btn_select_pdf)
        
        self.btn_select_folder = QPushButton("📁 Выбрать папку")
        self.btn_select_folder.clicked.connect(self._select_folder)
        button_layout.addWidget(self.btn_select_folder)
        
        button_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self._refresh_jobs)
        button_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(button_layout)
        
        # Jobs table
        self.jobs_table = QTableWidget()
        self.jobs_table.setColumnCount(5)
        self.jobs_table.setHorizontalHeaderLabels([
            "ID", "Файл", "Статус", "Прогресс", "Сообщение"
        ])
        self.jobs_table.horizontalHeader().setStretchLastSection(True)
        self.jobs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.jobs_table)
        
        # Log
        log_group = QGroupBox("Лог")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
        
        return widget
    
    def _create_events_tab(self):
        """Create events tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Год:"))
        self.event_year_filter = QSpinBox()
        self.event_year_filter.setRange(1900, 2100)
        self.event_year_filter.setValue(2024)
        filter_layout.addWidget(self.event_year_filter)
        
        filter_layout.addWidget(QLabel("Месяц:"))
        self.event_month_filter = QComboBox()
        self.event_month_filter.addItems([
            "Все", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ])
        filter_layout.addWidget(self.event_month_filter)
        
        filter_layout.addWidget(QLabel("Поиск:"))
        self.event_search = QLineEdit()
        self.event_search.setPlaceholderText("Текст для поиска...")
        filter_layout.addWidget(self.event_search)
        
        self.btn_filter_events = QPushButton("🔍 Применить")
        self.btn_filter_events.clicked.connect(self._refresh_events)
        filter_layout.addWidget(self.btn_filter_events)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(7)
        self.events_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Заголовок", "Место", "Источник", "Страница", "Цитата"
        ])
        self.events_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.events_table)
        
        return widget
    
    def _create_this_day_tab(self):
        """Create "This Day" tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Date selection
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("День:"))
        self.this_day_spin = QSpinBox()
        self.this_day_spin.setRange(1, 31)
        self.this_day_spin.setValue(1)
        date_layout.addWidget(self.this_day_spin)
        
        date_layout.addWidget(QLabel("Месяц:"))
        self.this_month_combo = QComboBox()
        self.this_month_combo.addItems([
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ])
        date_layout.addWidget(self.this_month_combo)
        
        date_layout.addWidget(QLabel("Количество:"))
        self.this_count_spin = QSpinBox()
        self.this_count_spin.setRange(1, 20)
        self.this_count_spin.setValue(5)
        date_layout.addWidget(self.this_count_spin)
        
        self.btn_generate_this_day = QPushButton("✨ Сформировать")
        self.btn_generate_this_day.clicked.connect(self._generate_this_day)
        date_layout.addWidget(self.btn_generate_this_day)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Generated text
        self.this_day_text = QPlainTextEdit()
        self.this_day_text.setPlaceholderText("Здесь появится сформированный текст...")
        layout.addWidget(self.this_day_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_copy_this_day = QPushButton("📋 Копировать")
        self.btn_copy_this_day.clicked.connect(self._copy_this_day)
        btn_layout.addWidget(self.btn_copy_this_day)
        
        self.btn_save_this_day = QPushButton("💾 Сохранить в файл")
        self.btn_save_this_day.clicked.connect(self._save_this_day)
        btn_layout.addWidget(self.btn_save_this_day)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_this_month_tab(self):
        """Create 'This Month' tab for monthly reports."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Month selection
        select_layout = QHBoxLayout()
        
        select_layout.addWidget(QLabel("Месяц:"))
        self.report_month_combo = QComboBox()
        self.report_month_combo.addItems([
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ])
        self.report_month_combo.setCurrentIndex(datetime.now().month - 1)
        select_layout.addWidget(self.report_month_combo)
        
        select_layout.addWidget(QLabel("Год (опционально):"))
        self.report_year_spin = QSpinBox()
        self.report_year_spin.setRange(1900, 2100)
        self.report_year_spin.setValue(0)  # 0 = all years
        self.report_year_spin.setSpecialValueText("Все годы")
        select_layout.addWidget(self.report_year_spin)
        
        self.btn_generate_report = QPushButton("📊 Сформировать отчёт")
        self.btn_generate_report.clicked.connect(self._generate_monthly_report)
        select_layout.addWidget(self.btn_generate_report)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # Report output
        self.report_text = QPlainTextEdit()
        self.report_text.setPlaceholderText("Здесь появится отчёт...")
        layout.addWidget(self.report_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_copy_report = QPushButton("📋 Копировать")
        self.btn_copy_report.clicked.connect(self._copy_monthly_report)
        btn_layout.addWidget(self.btn_copy_report)
        
        self.btn_save_report = QPushButton("💾 Сохранить в файл")
        self.btn_save_report.clicked.connect(self._save_monthly_report)
        btn_layout.addWidget(self.btn_save_report)
        
        self.btn_export_csv = QPushButton("📄 Экспорт CSV")
        self.btn_export_csv.clicked.connect(self._export_monthly_csv)
        btn_layout.addWidget(self.btn_export_csv)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_settings_tab(self):
        """Create settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Keywords section
        keywords_group = QGroupBox("Ключевые слова для поиска событий")
        keywords_layout = QVBoxLayout(keywords_group)
        
        # Info label
        info_label = QLabel(
            "Программа ищет предложения, содержащие эти слова. "
            "Каждое слово с новой строки."
        )
        info_label.setWordWrap(True)
        keywords_layout.addWidget(info_label)
        
        # Keywords text edit
        self.keywords_edit = QPlainTextEdit()
        self.keywords_edit.setPlaceholderText(
            "состоялся\nпрошёл\nоткрылся\nсобытие\n..."
        )
        # Load current keywords
        self.keywords_edit.setPlainText("\n".join(self.settings.get_keywords()))
        keywords_layout.addWidget(self.keywords_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_save_keywords = QPushButton("💾 Сохранить")
        self.btn_save_keywords.clicked.connect(self._save_keywords)
        btn_layout.addWidget(self.btn_save_keywords)
        
        self.btn_reset_keywords = QPushButton("🔄 Сбросить по умолчанию")
        self.btn_reset_keywords.clicked.connect(self._reset_keywords)
        btn_layout.addWidget(self.btn_reset_keywords)
        
        btn_layout.addStretch()
        keywords_layout.addLayout(btn_layout)
        
        layout.addWidget(keywords_group)
        
        # OCR Settings section
        ocr_group = QGroupBox("Настройки OCR (распознавание текста)")
        ocr_layout = QVBoxLayout(ocr_group)
        
        # DPI slider
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("Качество (DPI):"))
        
        self.dpi_slider = QSpinBox()
        self.dpi_slider.setRange(150, 600)
        self.dpi_slider.setSingleStep(50)
        self.dpi_slider.setValue(self.settings.get_ocr_dpi())
        self.dpi_slider.valueChanged.connect(self._on_dpi_changed)
        dpi_layout.addWidget(self.dpi_slider)
        
        self.dpi_label = QLabel(f"{self.settings.get_ocr_dpi()} DPI")
        dpi_layout.addWidget(self.dpi_label)
        dpi_layout.addStretch()
        
        ocr_layout.addLayout(dpi_layout)
        
        # Info about DPI
        dpi_info = QLabel(
            "150-200 DPI — быстро, но низкое качество\n"
            "300 DPI — оптимально (рекомендуется)\n"
            "400-600 DPI — медленно, но высокое качество"
        )
        dpi_info.setStyleSheet("color: gray; font-size: 11px;")
        ocr_layout.addWidget(dpi_info)
        
        # OCR Engine selection
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Движок OCR:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Tesseract (локально)", "AI (через API)"])
        current_engine = self.settings.get_ocr_engine()
        self.engine_combo.setCurrentIndex(0 if current_engine == 'tesseract' else 1)
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self.engine_combo)
        engine_layout.addStretch()
        ocr_layout.addLayout(engine_layout)
        
        # AI Settings (initially hidden if tesseract selected)
        self.ai_group = QGroupBox("Настройки AI OCR")
        ai_layout = QVBoxLayout(self.ai_group)
        
        # Provider selection
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Провайдер:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["DeepSeek", "OpenAI GPT-4", "Google Vision", "Kimi (Moonshot)"])
        providers = ['deepseek', 'openai', 'google', 'kimi']
        current_provider = self.settings.get_ai_provider()
        if current_provider in providers:
            self.provider_combo.setCurrentIndex(providers.index(current_provider))
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        ai_layout.addLayout(provider_layout)
        
        # API Key
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API ключ:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setText(self.settings.get_ai_api_key())
        self.api_key_edit.setPlaceholderText("Введите API ключ...")
        api_layout.addWidget(self.api_key_edit)
        
        self.btn_save_api = QPushButton("💾 Сохранить ключ")
        self.btn_save_api.clicked.connect(self._save_api_key)
        api_layout.addWidget(self.btn_save_api)
        api_layout.addStretch()
        ai_layout.addLayout(api_layout)
        
        # Cost info
        cost_info = QLabel(
            "⚠️ AI OCR требует интернет и API ключ.\n"
            "DeepSeek: ~$0.001 за страницу\n"
            "OpenAI: ~$0.01 за страницу\n"
            "Google Vision: ~$0.0015 за страницу\n"
            "Kimi: ~$0.006 за страницу"
        )
        cost_info.setStyleSheet("color: gray; font-size: 11px;")
        ai_layout.addWidget(cost_info)
        
        ocr_layout.addWidget(self.ai_group)
        
        # Show/hide AI group based on current engine
        self.ai_group.setVisible(current_engine == 'ai')
        
        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["rus — Русский", "eng — English", "rus+eng — Русский+English"])
        current_lang = self.settings.get_ocr_language()
        if current_lang == "rus":
            self.lang_combo.setCurrentIndex(0)
        elif current_lang == "eng":
            self.lang_combo.setCurrentIndex(1)
        else:
            self.lang_combo.setCurrentIndex(2)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        ocr_layout.addLayout(lang_layout)
        
        layout.addWidget(ocr_group)
        
        # Stats section
        stats_group = QGroupBox("Информация")
        stats_layout = QVBoxLayout(stats_group)
        
        self.settings_info_label = QLabel()
        self._update_settings_info()
        stats_layout.addWidget(self.settings_info_label)
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return widget
    
    def _update_settings_info(self):
        """Update settings info label."""
        keywords_count = len(self.settings.get_keywords())
        self.settings_info_label.setText(
            f"Загружено ключевых слов: {keywords_count}\n"
            f"Файл настроек: {self.settings.config_path}"
        )
    
    def _save_keywords(self):
        """Save keywords from text edit."""
        text = self.keywords_edit.toPlainText()
        keywords = [line.strip() for line in text.split('\n') if line.strip()]
        self.settings.set_keywords(keywords)
        
        if self.settings.save():
            QMessageBox.information(self, "Сохранено", "Ключевые слова сохранены!")
            self._update_settings_info()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настройки.")
    
    def _reset_keywords(self):
        """Reset keywords to defaults."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Сбросить ключевые слова к значениям по умолчанию?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.reset_keywords()
            self.settings.save()
            self.keywords_edit.setPlainText("\n".join(self.settings.get_keywords()))
            self._update_settings_info()
            QMessageBox.information(self, "Сброшено", "Ключевые слова сброшены по умолчанию.")
    
    def _on_dpi_changed(self, value):
        """Handle DPI slider change."""
        self.settings.set_ocr_dpi(value)
        self.dpi_label.setText(f"{value} DPI")
        self.settings.save()
    
    def _on_engine_changed(self, index):
        """Handle OCR engine change."""
        engine = 'ai' if index == 1 else 'tesseract'
        self.settings.set_ocr_engine(engine)
        self.settings.save()
        self.ai_group.setVisible(engine == 'ai')
    
    def _on_provider_changed(self, index):
        """Handle AI provider change."""
        providers = ['deepseek', 'openai', 'google']
        self.settings.set_ai_provider(providers[index])
        self.settings.save()
    
    def _save_api_key(self):
        """Save API key."""
        api_key = self.api_key_edit.text().strip()
        self.settings.set_ai_api_key(api_key)
        if self.settings.save():
            QMessageBox.information(self, "Сохранено", "API ключ сохранён!")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить API ключ.")
    
    def _on_lang_changed(self, index):
        """Handle language selection change."""
        languages = ["rus", "eng", "rus+eng"]
        self.settings.set_ocr_language(languages[index])
        self.settings.save()
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Файл")
        
        import_action = QAction("Импорт PDF...", self)
        import_action.triggered.connect(self._select_pdf)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Экспорт событий...", self)
        export_action.triggered.connect(self._export_events)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def _select_pdf(self):
        """Open file dialog to select PDF."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать PDF", "", "PDF файлы (*.pdf)"
        )
        if file_path:
            self._start_processing(file_path)
    
    def _select_folder(self):
        """Open folder dialog to select folder with PDFs."""
        folder_path = QFileDialog.getExistingDirectory(self, "Выбрать папку с PDF")
        if folder_path:
            # Find all PDFs in folder
            pdf_files = list(Path(folder_path).glob("*.pdf"))
            for pdf_file in pdf_files:
                self._start_processing(str(pdf_file))
    
    def _start_processing(self, file_path: str):
        """Start processing a PDF file."""
        # Create job record
        job = Job(id=None, input_path=file_path, status="queued")
        job_id = self.job_repo.create(job)
        
        self.log(f"Добавлена задача #{job_id}: {Path(file_path).name}")
        
        # Create and start worker
        worker = PDFProcessingWorker(job_id, file_path)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.log.connect(self.log)
        
        self.current_jobs[job_id] = worker
        self.thread_pool.start(worker)
        
        self._refresh_jobs()
    
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self._refresh_jobs()
    
    def _on_finished(self, success: bool, message: str):
        """Handle job completion."""
        self._refresh_jobs()
        if success:
            self.log(f"✅ Завершено: {message}")
        else:
            self.log(f"❌ Ошибка: {message}")
    
    def _refresh_jobs(self):
        """Refresh jobs table."""
        jobs = self.job_repo.get_all(limit=50)
        
        self.jobs_table.setRowCount(len(jobs))
        for i, job in enumerate(jobs):
            self.jobs_table.setItem(i, 0, QTableWidgetItem(str(job.id)))
            self.jobs_table.setItem(i, 1, QTableWidgetItem(Path(job.input_path).name))
            self.jobs_table.setItem(i, 2, QTableWidgetItem(job.status))
            self.jobs_table.setItem(i, 3, QTableWidgetItem(f"{job.progress}%"))
            self.jobs_table.setItem(i, 4, QTableWidgetItem(job.message))
    
    def _refresh_events(self):
        """Refresh events table."""
        # Get filter values
        year = self.event_year_filter.value()
        month = self.event_month_filter.currentIndex()  # 0 = all
        search = self.event_search.text().strip()
        
        if search:
            events = self.event_repo.search(search)
        else:
            events = self.event_repo.get_all(limit=100)
        
        self.events_table.setRowCount(len(events))
        for i, event in enumerate(events):
            self.events_table.setItem(i, 0, QTableWidgetItem(str(event.id)))
            self.events_table.setItem(i, 1, QTableWidgetItem(event.event_date or ""))
            self.events_table.setItem(i, 2, QTableWidgetItem(event.title or ""))
            self.events_table.setItem(i, 3, QTableWidgetItem(event.place or ""))
            self.events_table.setItem(i, 4, QTableWidgetItem(str(event.issue_id)))
            self.events_table.setItem(i, 5, QTableWidgetItem(str(event.page_no)))
            self.events_table.setItem(i, 6, QTableWidgetItem(event.source_quote[:100] + "..."))
    
    def _generate_this_day(self):
        """Generate 'This Day' text."""
        day = self.this_day_spin.value()
        month = self.this_month_combo.currentIndex() + 1
        count = self.this_count_spin.value()
        
        events = self.event_repo.get_by_date(day, month)
        
        if not events:
            self.this_day_text.setPlainText(f"На {day} {self.this_month_combo.currentText()} событий не найдено.")
            return
        
        # Take first N events
        selected = events[:count]
        
        # Short version
        short_lines = [f"📅 Этот день в истории Олёкминска ({day} {self.this_month_combo.currentText()}):"]
        for event in selected:
            year = event.event_date[:4] if event.event_date else "????"
            short_lines.append(f"• {year}: {event.title or 'Событие'}")
        
        short_text = "\n".join(short_lines)
        
        # Long version
        long_lines = [f"📅 {day} {self.this_month_combo.currentText()} в истории Олёкминска\n"]
        for event in selected:
            year = event.event_date[:4] if event.event_date else "????"
            long_lines.append(f"{year} год:")
            if event.description:
                long_lines.append(event.description)
            elif event.source_quote:
                long_lines.append(event.source_quote[:200])
            long_lines.append("")
        
        long_text = "\n".join(long_lines)
        
        # Combine
        full_text = f"{short_text}\n\n{'='*50}\\n\n{long_text}"
        self.this_day_text.setPlainText(full_text)
    
    def _copy_this_day(self):
        """Copy 'This Day' text to clipboard."""
        text = self.this_day_text.toPlainText()
        QApplication.clipboard().setText(text)
        self.log("Текст скопирован в буфер обмена")
    
    def _save_this_day(self):
        """Save 'This Day' text to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить", "this_day.txt", "Текстовые файлы (*.txt)"
        )
        if file_path:
            text = self.this_day_text.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.log(f"Сохранено: {file_path}")
    
    def _generate_monthly_report(self):
        """Generate monthly report."""
        month = self.report_month_combo.currentIndex() + 1
        year = self.report_year_spin.value()
        
        generator = MonthlyReportGenerator(self.db)
        
        if year == 0:
            year = None  # All years
        
        try:
            report = generator.generate_monthly_report(month, year)
            
            if report['total_events'] == 0:
                self.report_text.setPlainText(
                    f"Событий за {report['month_name_genitive']} не найдено."
                )
                return
            
            # Format as Telegram post
            text = generator.format_telegram_post(report, max_events_per_year=5)
            
            # Store report for export
            self._current_monthly_report = report
            
            self.report_text.setPlainText(text)
            self.log(f"Отчёт сформирован: {report['total_events']} событий")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сформировать отчёт: {e}")
    
    def _copy_monthly_report(self):
        """Copy monthly report to clipboard."""
        text = self.report_text.toPlainText()
        QApplication.clipboard().setText(text)
        self.log("Отчёт скопирован в буфер обмена")
    
    def _save_monthly_report(self):
        """Save monthly report to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", f"report_{datetime.now().strftime('%Y%m')}.txt",
            "Текстовые файлы (*.txt)"
        )
        if file_path:
            text = self.report_text.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.log(f"Отчёт сохранён: {file_path}")
    
    def _export_monthly_csv(self):
        """Export monthly report to CSV."""
        if not hasattr(self, '_current_monthly_report'):
            QMessageBox.warning(self, "Внимание", "Сначала сформируйте отчёт")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт CSV", f"events_{datetime.now().strftime('%Y%m')}.csv",
            "CSV файлы (*.csv)"
        )
        if file_path:
            try:
                generator = MonthlyReportGenerator(self.db)
                generator.export_to_csv(self._current_monthly_report, file_path)
                self.log(f"CSV экспортирован: {file_path}")
                QMessageBox.information(self, "Готово", "CSV файл сохранён!")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось экспортировать: {e}")
    
    def _export_events(self):
        """Export events to CSV/JSON."""
        # TODO: Implement export
        QMessageBox.information(self, "Экспорт", "Функция экспорта в разработке")
    
    def log(self, message: str):
        """Add log message."""
        self.log_text.appendPlainText(message)
