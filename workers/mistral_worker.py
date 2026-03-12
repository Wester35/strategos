from PySide6.QtCore import QThread, Signal
from mistralai.client import Mistral


class MistralWorker(QThread):

    response_received = Signal(str)
    error_occurred = Signal(str)
    status_update = Signal(str)

    def __init__(self, api_key, document_text, question):
        super().__init__()

        self.api_key = api_key
        self.document_text = document_text
        self.question = question

    def run(self):

        try:

            self.status_update.emit("Подключение к Mistral AI...")

            client = Mistral(api_key=self.api_key)

            prompt = f"""Проанализируй этот стратегический документ компании и ответь на вопрос пользователя.

ДОКУМЕНТ:
{self.document_text[:15000]}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{self.question}

Дай развернутый, структурированный ответ на русском языке. Используй профессиональную бизнес-терминологию.
Выдели ключевые риски, сильные стороны и дай рекомендации.
"""

            self.status_update.emit("Отправка запроса в Mistral AI...")

            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )

            self.status_update.emit("Получен ответ от Mistral AI...")

            if response and response.choices:

                result = response.choices[0].message.content

                self.response_received.emit(result)

            else:
                self.error_occurred.emit(
                    "Не удалось получить ответ от Mistral AI"
                )

        except Exception as e:

            self.error_occurred.emit(
                f"Ошибка при обращении к Mistral AI: {str(e)}"
            )