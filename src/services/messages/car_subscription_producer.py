import aio_pika
import json
from src.core.config.config import rabbitmq_config
from ssl_context_ignore import ssl_context_ignore

exchange_name = "email_confirmation_exchange"
queue_name = "email_confirmation_queue"

connection = None
channel = None
exchange = None

async def setup():
    global connection, channel, exchange
    connection = await aio_pika.connect_robust(rabbitmq_config.AMQP_URL, ssl_context=ssl_context_ignore())
    channel = await connection.channel()
    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT)
    queue = await channel.declare_queue(name=queue_name, durable=True)
    await queue.bind(exchange, routing_key=queue_name)

async def create_confirmation_message(email: str, host: str):
    message = {"email": email, "host": host}
    await exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=queue_name
    )
    print(f"[x] Sent email confirmation for {email}")
