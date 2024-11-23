import asyncio
from app.models.report import TaskRequest
from fastapi import FastAPI, BackgroundTasks

from app.tasks.queue import RabbitMQClient
from app.config import setup_settings


settings = setup_settings()

rabbitmq_client = RabbitMQClient(url=settings.url, queue_name=settings.queue)

app = FastAPI()


# Глобальная переменная для задачи
receive_task = None


@app.get("/start-receiver/")
async def start_receiver(background_tasks: BackgroundTasks):
    """Эндпоинт для запуска получения сообщений из очереди RabbitMQ."""
    global receive_task

    if receive_task and not receive_task.done():
        return {"message": "Receiver is already running"}

    receive_task = asyncio.create_task(rabbitmq_client.receive_message())
    return {"message": "Receiver started"}


@app.get("/stop-receiver/")
async def stop_receiver():
    """Эндпоинт для остановки получения сообщений из очереди RabbitMQ."""
    global receive_task

    if receive_task and not receive_task.done():
        receive_task.cancel()
        return {"message": "Receiver stopped"}

    return {"message": "Receiver is not running"}


@app.post("/tasks/")
async def create_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """
    Эндпоинт для получения задачи и публикации её в очередь RabbitMQ.
    """
    message = str(task.dict())
    background_tasks.add_task(rabbitmq_client.send_message, message)

    return {"message": f"Task submitted to queue, {message}"}



@app.get("/fill/")
async def fill_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    import json
    try:
        # Создаем асинхронный клиент для MongoDB
        myclient = AsyncIOMotorClient(settings.mongo_url)
        db = myclient["report_db"]
        collection = db["calls"]

        # Открываем файл и загружаем данные
        with open("app/data.json", "r") as file:
            mylist = json.load(file)

        # Вставляем данные в коллекцию MongoDB
        await collection.insert_many(mylist)
        print("Данные успешно вставлены в базу данных.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")