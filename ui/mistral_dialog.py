import os

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QProgressBar,
    QTextBrowser,
    QDialogButtonBox,
    QMessageBox
)

from workers.mistral_worker import MistralWorker


class MistralDialog(QDialog):
    """Диалог для взаимодействия с Mistral AI"""

    def __init__(self, document_text, parent=None):
        super().__init__(parent)
        self.document_text = document_text
        self.api_key = None
        self.worker = None
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Mistral AI - Анализ документа")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        # Палитра для системных цветов
        palette = self.palette()
        window_bg = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.WindowText)
        base_color = palette.color(QPalette.Base)
        button_bg = palette.color(QPalette.Button)
        button_text = palette.color(QPalette.ButtonText)

        # Поле для ввода API ключа
        key_layout = QHBoxLayout()
        key_label = QLabel("API ключ Mistral:")
        key_label.setStyleSheet(f"color: {text_color.name()};")

        self.key_input = QTextEdit()
        self.key_input.setMaximumHeight(60)
        self.key_input.setPlaceholderText("Введите ваш Mistral API ключ...")
        self.key_input.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color.name()};")

        # Кнопка сохранения ключа
        self.save_key_btn = QPushButton("💾 Сохранить ключ")
        self.save_key_btn.clicked.connect(self.save_api_key)
        self.save_key_btn.setStyleSheet(f"""
            background-color: {button_bg.name()};
            color: {button_text.name()};
        """)

        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        key_layout.addWidget(self.save_key_btn)

        # Поле для вопроса
        question_label = QLabel("Ваш вопрос к ИИ:")
        question_label.setStyleSheet(f"color: {text_color.name()};")

        self.question_input = QTextEdit()
        self.question_input.setMaximumHeight(80)
        self.question_input.setPlaceholderText(
            "Например: Какие основные риски в этом плане? Или: Дай оценку стратегии..."
        )
        self.question_input.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color.name()};")

        # Кнопка отправки
        self.ask_btn = QPushButton("🤖 Спросить Mistral AI")
        self.ask_btn.clicked.connect(self.ask_mistral)
        self.ask_btn.setEnabled(False)
        self.ask_btn.setStyleSheet(f"""
            background-color: {button_bg.name()};
            color: {button_text.name()};
            font-weight: bold;
            padding: 10px;
            font-size: 14px;
        """)

        # Статус
        self.status_label = QLabel("Введите API ключ для начала работы")
        self.status_label.setStyleSheet(f"color: {text_color.name()};")

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Область для ответа
        response_label = QLabel("Ответ Mistral AI:")
        response_label.setStyleSheet(f"color: {text_color.name()};")

        self.response_text = QTextBrowser()
        self.response_text.setOpenExternalLinks(True)
        self.response_text.setStyleSheet(f"""
            background-color: {base_color.name()};
            color: {text_color.name()};
            border: 1px solid {button_bg.name()};
            border-radius: 5px;
            padding: 10px;
            font-family: Arial;
        """)

        # Кнопки диалога
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)

        # Добавляем все в layout
        layout.addLayout(key_layout)
        layout.addWidget(question_label)
        layout.addWidget(self.question_input)
        layout.addWidget(self.ask_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(response_label)
        layout.addWidget(self.response_text)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Пытаемся загрузить сохраненный ключ
        self.load_api_key()

    def save_api_key(self):
        """Сохраняет API ключ"""
        key = self.key_input.toPlainText().strip()
        if key:
            self.api_key = key
            # Сохраняем в файл для следующего раза
            try:
                with open("mistral_key.txt", "w") as f:
                    f.write(key)
                self.ask_btn.setEnabled(True)
                self.status_label.setText("✅ API ключ сохранен. Можете задавать вопросы!")
                self.status_label.setStyleSheet("color: green;")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить ключ: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Введите API ключ")

    def load_api_key(self):
        """Загружает сохраненный API ключ"""
        try:
            if os.path.exists("mistral_key.txt"):
                with open("mistral_key.txt", "r") as f:
                    self.api_key = f.read().strip()
                    self.key_input.setText(self.api_key)
                    self.ask_btn.setEnabled(True)
                    self.status_label.setText("✅ API ключ загружен")
                    self.status_label.setStyleSheet("color: green;")
        except:
            pass

    def ask_mistral(self):
        """Отправляет запрос в Mistral AI"""
        if not self.api_key:
            QMessageBox.warning(self, "Ошибка", "Сначала сохраните API ключ")
            return

        question = self.question_input.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "Ошибка", "Введите вопрос")
            return

        # Блокируем кнопки
        self.ask_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс
        self.response_text.clear()
        self.status_label.setText("🔄 Отправка запроса в Mistral AI...")

        # Запускаем поток
        self.worker = MistralWorker(self.api_key, self.document_text, question)
        self.worker.response_received.connect(self.on_response)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.start()

    def on_response(self, response):
        """Обработка ответа от Mistral"""
        self.progress_bar.setVisible(False)
        self.ask_btn.setEnabled(True)
        self.status_label.setText("✅ Ответ получен!")
        self.status_label.setStyleSheet("color: green;")

        # Форматируем ответ
        formatted_response = f"""
        <div style='font-family: Arial; line-height: 1.6;'>
            <h3 style='color: #4a90e2;'>🤖 Ответ Mistral AI:</h3>
            <div style='background-color: white; padding: 15px; border-radius: 5px;'>
                {response.replace(chr(10), '<br>')}
            </div>
        </div>
        """
        self.response_text.setHtml(formatted_response)

    def on_error(self, error_msg):
        """Обработка ошибки"""
        self.progress_bar.setVisible(False)
        self.ask_btn.setEnabled(True)
        self.status_label.setText("❌ Ошибка")
        self.status_label.setStyleSheet("color: red;")
        QMessageBox.critical(self, "Ошибка Mistral AI", error_msg)