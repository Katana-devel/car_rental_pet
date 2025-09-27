import asyncio
import json
from uuid import UUID

import aio_pika
from src.core.config.config import rabbitmq_config
from src.core.logger.logger import logger
from src.services.messages.email import send_password_reset

exchange_name = "password_reset_exchange"
queue_name = "password_reset_queue"

async def setup():
    connection = await aio_pika.connect_robust(rabbitmq_config.AMQP_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT)
    queue = await channel.declare_queue(name=queue_name, durable=True)
    await queue.bind(exchange, routing_key=queue_name)

    return connection, channel, exchange, queue


async def callback(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            await send_password_reset(
                user_id=UUID(data["user_id"]),
                email=data["email"],
                host=data["host"]
            )
        except Exception as e:
            logger.error("can't send the password reset email: %s", e)


async def main():
    connection, channel, exchange, queue = await setup()
    await queue.consume(callback)

