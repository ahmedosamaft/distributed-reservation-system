import time
import random
import pika as pk
from pika.exchange_type import ExchangeType

connection_params = pk.ConnectionParameters(
    host="localhost",
    credentials=pk.PlainCredentials(username="admin", password="admin"),
)

connection = pk.BlockingConnection(connection_params)

channel = connection.channel()

channel.exchange_declare(exchange="payments", exchange_type=ExchangeType.direct)

pending_queue = channel.queue_declare(queue="pending_payments")
flashed_queue = channel.queue_declare(queue="flashed_payments")

channel.queue_bind(
    exchange="payments",
    queue=pending_queue.method.queue,
    routing_key="pending",
)

channel.queue_bind(
    exchange="payments",
    queue=flashed_queue.method.queue,
    routing_key="pending",
)

channel.basic_qos(prefetch_count=1)


def on_pending_payment_callback(ch, method, props, body):
    payment_data = body.decode("utf-8")
    rand = random.randint(0, 1)
    if rand == 0:
        print(f"Payment {payment_data} failed")
        ch.basic_publish(
            exchange="payments",
            routing_key="failed",
            body=body,
        )
        return
    print(f"Payment {payment_data} succeeded")


channel.basic_consume(
    queue=pending_queue.method.queue,
    on_message_callback=on_pending_payment_callback,
    auto_ack=True,
)

channel.basic_consume(
    queue=flashed_queue.method.queue,
    on_message_callback=on_pending_payment_callback,
    auto_ack=True,
)

print("Started consuming")

channel.start_consuming()

channel.close()
connection.close()
