from mistralai.client import Mistral


class MistralService:

    def __init__(self, api_key: str):
        self.client = Mistral(api_key=api_key)

    def ask(self, document_text: str, question: str):

        prompt = f"""
        Проанализируй стратегический документ.

        ДОКУМЕНТ:
        {document_text[:15000]}

        ВОПРОС:
        {question}

        Дай структурированный ответ.
        """

        response = self.client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content