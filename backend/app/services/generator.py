import os
import redis
import aiohttp
import hashlib
from dotenv import load_dotenv
import random

load_dotenv()

EXAMPLES = """
— Доктор, я всё ещё люблю своего бывшего…
— Ну, так забудьте его!
— Забыла. Каждую ночь заново знакомимся.

— Сёма, ты слышал? Девочки на чемпионате решили всего одну задачу!
— Таки да, и что?
— Им дали шарик.
— И?
— Они его лопнули!
— Ну правильно. Мир хрупок, Сёма. Особенно, если недооценивать девушек.

— Сёма, ты решил всё на 500 баллов!
— Таки да.
— И что, тебя не взяли?
— Моя анкета была честной, Роза. А честность в Тинькофф нынче не проходит в фильтры.

— Профессор, я не понимаю монады.
— Отлично!
— В смысле?..
— Монада — это как любовь. Если ты её понял — это уже не она.

— Третья пересдача по базам данных у Батраевой.
— И как ощущения?
— Как у таблицы без PRIMARY KEY: ни за что не зацепиться.

— Что страшнее: DELETE без WHERE или третья пересдача у Батраевой?
— DELETE хотя бы логируется…

— Сёма, у тебя же уже третья пересдача у Батраевой?
— Таки да.
— И ты ещё жив?
— Нет, это мой SELECT DISTINCT двойник.

— У них предмет по универсальной алгебре?
— Да.
— И что это значит?
— Что они теперь универсально страдают.



"""


class JokeGenerator:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0
        )
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.timeout = aiohttp.ClientTimeout(total=None)  # Без ограничения времени

    async def generate(self, topic: str) -> str:
        cache_key = f"joke:{hashlib.md5(topic.encode()).hexdigest()}"

        cached_joke = self.redis.get(cache_key)
        if cached_joke:
            return cached_joke.decode("utf-8")

        joke = await self._generate_from_ollama(topic)
        self.redis.setex(cache_key, 86400, joke)
        return joke

    async def clear_cache(self):
        self.redis.flushdb()
        return "Кеш успешно очищен"

    async def _generate_from_ollama(self, topic: str) -> str:
        prompt = f"""Ты — профессиональный автор анекдотов с айтишным и студенческим юмором. 
Твой стиль должен быть точь-в-точь как в этих примерах:

{EXAMPLES}

Сгенерируй новый анекдот на тему «{topic}», строго соблюдая следующие правила:
1. Формат: короткий диалог (3-5 строк)
2. Стиль: точное соответствие примерам выше
3. Запрещены: черный юмор, политика, эротика
3. Юмор: ироничный, с студенческим подтекстом
4. Язык: разговорный русский с элементами сленга
5. Финал: неожиданная или абсурдная развязка

Пример структуры:
— Первая реплика
— Ответ
— Неожиданный поворот

Твой анекдот:"""

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                        f"{self.ollama_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": False,
                            "options": {
                                "temperature": 1.1,  # Больше креативности
                                "num_predict": 300,  # Больше места для творчества
                                "top_k": 60,  # Разнообразие вариантов
                                "repeat_penalty": 1.2  # Избегаем повторов
                            }
                        }
                ) as response:
                    data = await response.json()
                    joke = data["message"]["content"].strip()

                    # Пост-обработка для единообразия
                    joke = joke.replace('"', '—').replace('\n\n', '\n')
                    if not joke.startswith('—'):
                        joke = '— ' + joke.replace('\n', '\n— ')

                    return joke

        except Exception as e:
            print(f"Ошибка генерации: {str(e)}")
            return random.choice([
                f"Пока анекдотов про {topic} нет. Батраева всех выгнала!",
                f"Про {topic} даже Штирлиц не знает...",
                f"SELECT * FROM jokes WHERE topic='{topic}' → 0 rows returned"
            ])