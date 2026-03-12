import os
import json

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit,
    QMessageBox, QSplitter, QTabWidget,
    QProgressBar, QStatusBar
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette

from workers.parser_worker import ParserWorker
from ui.mistral_dialog import MistralDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.worker = None
        self.mistral_dialog = None
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Стратегический парсер документов")
        self.setGeometry(100, 100, 1000, 600)

        # Получаем системные цвета
        palette = self.palette()
        window_bg = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.WindowText)
        base_color = palette.color(QPalette.Base)
        button_bg = palette.color(QPalette.Button)
        button_text = palette.color(QPalette.ButtonText)
        highlight_color = palette.color(QPalette.Highlight)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель с кнопками
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки
        def style_btn(btn, highlight=False):
            palette = self.palette()
            button_bg = palette.color(QPalette.Button)
            button_text = palette.color(QPalette.ButtonText)
            highlight_color = palette.color(QPalette.Highlight)

            # Если кнопка "выделена" (active)
            bg_color = highlight_color.name() if highlight else button_bg.name()

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {button_text.name()};
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {highlight_color.lighter(130).name()};
                }}
                QPushButton:disabled {{
                    background-color: #cccccc;
                    color: #666666;
                }}
            """)

        self.btn_open = QPushButton("📂 Открыть документ")
        self.btn_open.clicked.connect(self.open_document)
        style_btn(self.btn_open, highlight=True)

        self.btn_save = QPushButton("💾 Сохранить JSON")
        self.btn_save.clicked.connect(self.save_json)
        self.btn_save.setEnabled(False)
        style_btn(self.btn_save)

        self.btn_save_txt = QPushButton("📝 Сохранить текст")
        self.btn_save_txt.clicked.connect(self.save_text)
        self.btn_save_txt.setEnabled(False)
        style_btn(self.btn_save_txt)

        self.btn_export = QPushButton("📊 Экспорт отчет")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        style_btn(self.btn_export)

        self.btn_mistral = QPushButton("🤖 Спросить Mistral AI")
        self.btn_mistral.clicked.connect(self.ask_mistral)
        self.btn_mistral.setEnabled(False)
        style_btn(self.btn_mistral, highlight=True)

        top_layout.addWidget(self.btn_open)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_save_txt)
        top_layout.addWidget(self.btn_export)
        top_layout.addWidget(self.btn_mistral)
        top_layout.addStretch()

        # Информационная метка
        self.info_label = QLabel("Выберите документ для анализа")
        self.info_label.setStyleSheet(f"color: {text_color.name()}; padding: 5px;")

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        main_layout.addWidget(top_panel)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.progress_bar)

        # Разделитель для контента
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_label = QLabel("📋 Информация")
        left_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_label.setStyleSheet(f"color: {text_color.name()};")

        self.tree_view = QTextEdit()
        self.tree_view.setReadOnly(True)
        self.tree_view.setMaximumWidth(300)
        self.tree_view.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color.name()};")

        left_layout.addWidget(left_label)
        left_layout.addWidget(self.tree_view)

        # Правая панель с вкладками
        right_panel = QTabWidget()

        def style_textedit(te):
            te.setReadOnly(True)
            te.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color.name()};")

        # Вкладка с текстом
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier New", 10))
        style_textedit(self.text_edit)
        text_layout.addWidget(self.text_edit)
        right_panel.addTab(text_widget, "📄 Текст документа")

        # Вкладка с JSON
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        self.json_edit = QTextEdit()
        self.json_edit.setFont(QFont("Courier New", 10))
        style_textedit(self.json_edit)
        json_layout.addWidget(self.json_edit)
        right_panel.addTab(json_widget, "🔍 JSON данные")

        # Вкладка с метриками
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout(metrics_widget)
        self.metrics_text = QTextEdit()
        self.metrics_text.setFont(QFont("Arial", 10))
        style_textedit(self.metrics_text)
        metrics_layout.addWidget(self.metrics_text)
        right_panel.addTab(metrics_widget, "📊 Метрики")

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900])

        main_layout.addWidget(splitter)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        # Фон окна
        self.setStyleSheet(f"QMainWindow {{ background-color: {window_bg.name()}; }}")

    def apply_styles(self):
        self.setStyleSheet("""
            # QMainWindow {
            #     background-color: #f5f5f5;
            # }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            # QPushButton:hover {
            #     background-color: #357abd;
            # }
            # QPushButton:disabled {
            #     background-color: #cccccc;
            # }
            # QTextEdit, QTreeView {
            #     background-color: white;
            #     border: 1px solid #ddd;
            #     border-radius: 3px;
            # }
            # QTabWidget::pane {
            #     border: 1px solid #ddd;
            #     border-radius: 3px;
            # }
        """)

    def open_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите документ",
            "",
            "Word документы (*.docx);;Все файлы (*.*)"
        )

        if file_path:
            self.info_label.setText(f"Анализ: {os.path.basename(file_path)}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Запускаем парсер в отдельном потоке
            self.worker = ParserWorker(file_path)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.status_update.connect(self.status_bar.showMessage)
            self.worker.parsing_finished.connect(self.on_parsing_finished)
            self.worker.error_occurred.connect(self.on_error)
            self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_parsing_finished(self, data):
        self.current_data = data
        self.progress_bar.setVisible(False)

        # Активируем кнопки
        self.btn_save.setEnabled(True)
        self.btn_save_txt.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_mistral.setEnabled(True)

        # Показываем текст
        self.text_edit.setText(data["full_text"])

        # Показываем JSON
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        self.json_edit.setText(json_str)

        # Показываем информацию в левой панели
        info = []
        info.append("📊 СТАТИСТИКА")
        info.append("=" * 30)
        info.append(f"📁 Файл: {os.path.basename(data['metadata']['file_name'])}")
        info.append(f"📄 Параграфов: {data['metadata']['total_paragraphs']}")
        info.append(f"📊 Таблиц: {data['metadata']['total_tables']}")
        info.append(f"📏 Символов: {len(data['full_text'])}")

        if data["block1"]:
            info.append("\n🎯 БЛОК 1:")
            if "strategic_goal" in data["block1"]:
                info.append(f"  Цель найдена")
            if "targets" in data["block1"]:
                info.append(f"  Показателей: {len(data['block1']['targets'])}")

        if data["block2"]:
            info.append(f"\n🏢 БЛОК 2:")
            info.append(f"  Департаментов: {len(data['block2'])}")

        if data["block3"]:
            info.append(f"\n📅 БЛОК 3:")
            info.append(f"  Квартальных планов: {len(data['block3'])}")

        self.tree_view.setText("\n".join(info))

        # Показываем метрики
        metrics = []
        metrics.append("📊 МЕТРИКИ ДОКУМЕНТА\n" + "=" * 50)
        metrics.append(f"📁 Файл: {data['metadata']['file_name']}")
        metrics.append(f"🕐 Обработан: {data['metadata']['parsed_at']}")
        metrics.append(f"📄 Параграфов: {data['metadata']['total_paragraphs']}")
        metrics.append(f"📊 Таблиц: {data['metadata']['total_tables']}")
        metrics.append(f"📏 Длина текста: {len(data['full_text'])} символов")

        if "block1" in data and data["block1"]:
            metrics.append("\n🎯 БЛОК 1: Стратегическая цель")
            if "strategic_goal" in data["block1"]:
                goal = data["block1"]["strategic_goal"]
                metrics.append(f"   Цель: {goal[:100]}..." if len(goal) > 100 else f"   Цель: {goal}")

        if "block2" in data and data["block2"]:
            metrics.append(f"\n🏢 БЛОК 2: Департаментов найдено: {len(data['block2'])}")
            for dept in data["block2"].keys():
                metrics.append(f"   • {dept}")

        if "block3" in data and data["block3"]:
            metrics.append(f"\n📅 БЛОК 3: Квартальных планов: {len(data['block3'])}")

        self.metrics_text.setText("\n".join(metrics))

        self.status_bar.showMessage("Анализ завершен", 3000)

    def on_error(self, error_msg):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка:\n{error_msg}")
        self.status_bar.showMessage("Ошибка при анализе", 3000)

    def save_json(self):
        if not self.current_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить JSON",
            "стратегический_документ.json",
            "JSON файлы (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Успех", f"Данные сохранены в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

    def save_text(self):
        if not self.current_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить текст",
            "извлеченный_текст.txt",
            "Текстовые файлы (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_data["full_text"])
                QMessageBox.information(self, "Успех", f"Текст сохранен в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

    def export_report(self):
        if not self.current_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт отчета",
            "отчет.html",
            "HTML файлы (*.html)"
        )

        if file_path:
            try:
                html = self.generate_html_report()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                QMessageBox.information(self, "Успех", f"Отчет сохранен в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчет:\n{e}")

    def generate_html_report(self):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Стратегический документ - отчет</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #4a90e2; }}
                .section {{ margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .metadata {{ color: #666; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>Стратегический документ - отчет</h1>
            <div class="metadata">
                <p><b>Файл:</b> {self.current_data['metadata']['file_name']}</p>
                <p><b>Обработан:</b> {self.current_data['metadata']['parsed_at']}</p>
                <p><b>Параграфов:</b> {self.current_data['metadata']['total_paragraphs']}</p>
                <p><b>Таблиц:</b> {self.current_data['metadata']['total_tables']}</p>
            </div>

            <div class="section">
                <h2>Блок 1: Стратегическая цель</h2>
                <pre>{json.dumps(self.current_data.get('block1', {}), ensure_ascii=False, indent=2)}</pre>
            </div>

            <div class="section">
                <h2>Блок 2: Департаменты</h2>
                <pre>{json.dumps(self.current_data.get('block2', {}), ensure_ascii=False, indent=2)}</pre>
            </div>

            <div class="section">
                <h2>Блок 3: Квартальные фазы</h2>
                <pre>{json.dumps(self.current_data.get('block3', {}), ensure_ascii=False, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        return html

    def ask_mistral(self):
        """Открывает диалог с Mistral AI"""
        if not self.current_data:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте документ")
            return

        self.mistral_dialog = MistralDialog(self.current_data["full_text"], self)
        self.mistral_dialog.exec_()