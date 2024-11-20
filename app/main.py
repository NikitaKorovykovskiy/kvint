from fastapi import FastAPI
from app.tasks.queue import rabbitmq_connection
from app.service.mongo_servise import mongo_service
app = FastAPI()

@app.on_event("startup")
async def startup():
    await rabbitmq_connection.start()

@app.on_event("shutdown")
async def shutdown():
    await rabbitmq_connection.stop()

@app.get("/")
async def read_root():
    return mongo_service.get_data_by_phone("123")
