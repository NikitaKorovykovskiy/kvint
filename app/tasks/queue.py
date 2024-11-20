import asyncio
import pika
from pika.adapters.asyncio_connection import AsyncioConnection


class RabbitMQConnection:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = "report_queue"

    async def start(self):
        """Подключение к RabbitMQ и создание очереди."""
        loop = asyncio.get_event_loop()

        connection_future = asyncio.Future()

        def on_connection_open(connection):
            self.connection = connection
            connection_future.set_result(connection)
            # Теперь, когда соединение установлено, открываем канал
            self.connection.channel(on_open_callback=self.on_channel_open)

        def on_connection_error(connection_unused, error):
            connection_future.set_exception(error)

        # Создаем соединение
        self.connection = AsyncioConnection(
            pika.ConnectionParameters(host="rabbitmq"),  # используйте правильный хост
            on_open_callback=on_connection_open,
            on_open_error_callback=on_connection_error
        )

        await connection_future

    def on_channel_open(self, channel):
        """Коллбэк для открытия канала."""
        self.channel = channel

        # После открытия канала, создаем очередь
        queue_future = asyncio.Future()

        def on_queue_declared(_):
            queue_future.set_result(None)

        self.channel.queue_declare(queue=self.queue_name, callback=on_queue_declared)
        loop = asyncio.get_event_loop()
        loop.create_task(queue_future)

    async def stop(self):
        """Закрытие подключения."""
        if self.connection:
            self.connection.close()

    async def publish(self, message: str):
        """Публикация сообщения."""
        if not self.channel:
            raise Exception("Channel is not available")
        self.channel.basic_publish(
            exchange="", routing_key=self.queue_name, body=message
        )


rabbitmq_connection = RabbitMQConnection()
