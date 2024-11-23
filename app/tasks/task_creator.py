from motor.motor_asyncio import AsyncIOMotorClient
import time


class CallRepository:
    def __init__(self, db_url: str, db_name: str, collection_name: str):
        self.client = AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    async def get_calls_by_phone(self, phone: str) -> list[dict]:
        """
        Получение всех записей звонков для указанного номера телефона.
        """
        calls = await self.collection.find({"phone": phone}).to_list(length=None)
        return calls
    
class TaskProcessor:
    def __init__(self, call_repository: CallRepository):
        self.call_repository = call_repository

    async def generate_report(self, phone: str) -> dict:
        """
        Асинхронная генерация отчета по номеру телефона.
        """
        start_time = time.monotonic()

        # Получаем данные из репозитория
        calls = await self.call_repository.get_calls_by_phone(phone)
        if not calls:
            return {"phone": phone, "error": "No data found for the given phone"}

        count_rows = len(calls)
        durations = {"10_sec": 0, "10_30_sec": 0, "30_sec": 0}
        prices = []
        total_durations = 0
        sum_price_above_15 = 0

        # Обрабатываем данные звонков
        for call in calls:
            start_date = call["start_date"]
            end_date = call["end_date"]
            duration = max(0, (end_date - start_date) // 1000)

            if duration <= 10:
                durations["10_sec"] += 1
            elif 10 < duration <= 30:
                durations["10_30_sec"] += 1
            else:
                durations["30_sec"] += 1

            price = duration * 10
            prices.append(price)
            total_durations += duration
            if duration > 15:
                sum_price_above_15 += price

        total_duration = time.monotonic() - start_time
        return {
            "phone": phone,
            "count_rows": count_rows,
            "durations_breakdown": durations,
            "max_price_attempt": max(prices),
            "min_price_attempt": min(prices),
            "avg_duration": total_durations / count_rows,
            "sum_price_above_15_sec": sum_price_above_15,
            "total_duration": total_duration,
        }
