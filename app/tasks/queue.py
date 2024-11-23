import asyncio
import aio_pika
import asyncio

from app.tasks.task_creator import CallRepository, TaskProcessor
from app.config import setup_settings
import aio_pika
import ast
import json
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


settings = setup_settings()

call_repository = CallRepository(db_url=settings.mongo_url, db_name="report_db", collection_name="calls")
task_processor = TaskProcessor(call_repository)


# Обработчик сообщений
async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        tasks = []
        message_body = message.body.decode()
        data_dict = ast.literal_eval(message_body)
        print(data_dict)
        phones = data_dict.get("phones", [])
        correlation_id = data_dict.get("correlation_id", "")
        for phone in phones:
            task = asyncio.create_task(task_processor.generate_report(phone))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        print(type(results))
        save_reports(results, correlation_id=correlation_id)

def save_reports(results, correlation_id):
    # Метаинформация для отчета
    report_metadata = {
        "correlation_id": correlation_id,  # Можно генерировать уникальный ID
        "status": "Complete",
        "task_received": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "from": "report_service",
        "to": "client",
        "data": results,
        "total_duration": sum(
            result.get("durations_breakdown", {}).get("total_duration", 0)  # Используем пустой словарь и 0 по умолчанию
            for result in results
        )
    }

    # Открытие файла в режиме добавления
    with open("reports.json", "a") as file:
        # Если файл пустой, добавляем начальную скобку для массива JSON
        if file.tell() == 0:
            pass
        else:
            file.write(",\n")

        # Запись метаинформации и данных
        json.dump(report_metadata, file, indent=4)

        logger.info("Отчеты сохранены в reports.json")


class RabbitMQClient:
    def __init__(self, url: str, queue_name: str):
        self.url = url
        self.queue_name = queue_name

    async def receive_message(self):
        """
        Подключаемся к RabbitMQ, слушаем очередь и передаем сообщения на обработку.
        """
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.queue_name, durable=True)
            await queue.consume(process_message)
            logger.info("Ожидание сообщений...")
            await asyncio.Future()  # Ждем бесконечно

    async def send_message(self, message: str):
        """
        Отправляем сообщение в очередь RabbitMQ.
        """
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.queue_name, durable=True)

            message = aio_pika.Message(body=message.encode("utf-8"))
            await channel.default_exchange.publish(message, routing_key=queue.name)
            logger.info(f"Сообщение отправлено в очередь: {message.body.decode()}")