import asyncio
import json
import aio_pika

from ssl_context_ignore import ssl_context_ignore
from src.core.config.config import rabbitmq_config
from src.services.messages.email import send_confirmation_email

exchange_name = "email_confirmation_exchange"
queue_name = "email_confirmation_queue"

async def setup():
    connection = await aio_pika.connect_robust(rabbitmq_config.AMQP_URL, ssl_context=ssl_context_ignore())
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
            await send_confirmation_email(
                email=data["email"],
                host=data["host"]
            )
        except Exception as e:
            print("can't send the email", e)


async def main():
    connection, channel, exchange, queue = await setup()
    await queue.consume(callback)

