import asyncio
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from app.tasks.queue import RabbitMQConnection
from app.service.mongo_servise import mongo_service
app = FastAPI()

RABBIT_QUEUE = "report_queue"
RABBIT_HOST = "rabbitmq"
rabbitmq = RabbitMQConnection(queue_name=RABBIT_QUEUE, host=RABBIT_HOST)



class TaskRequest(BaseModel):
    correlation_id: str
    phones: list[int]


@app.on_event("startup")
async def startup_event():
    """Подключение к RabbitMQ при запуске приложения."""
    await rabbitmq.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие подключения к RabbitMQ при завершении работы приложения."""
    await rabbitmq.close()

@app.get("/")
async def read_root():
    await rabbitmq.connect()
    # return mongo_service.get_data_by_phone("123")

@app.post("/tasks")
async def submit_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """
    Эндпоинт для получения задачи от клиента.
    """
    # Отправка задачи в RabbitMQ
    message = task.json()
    await rabbitmq.publish(message)

    # В фоне запускаем обработку задачи
    background_tasks.add_task(process_task, task.correlation_id)

    return {"status": "Task submitted", "correlation_id": task.correlation_id}

async def process_task(correlation_id: str):
    """
    Обработка задачи (имитация асинхронной обработки).
    """
    # Заглушка: в реальном сценарии здесь будет вызов к MongoDB и обработка данных
    await asyncio.sleep(2)
    print(f"Task with correlation_id {correlation_id} processed.")