import pika as pk
import time
import random
import threading
from pika.exchange_type import ExchangeType

connection_params = pk.ConnectionParameters(
    host="localhost",
    credentials=pk.PlainCredentials("admin", "admin"),
)

running = True


def generate_payment_id():
    return random.randint(100000, 999999)


def producer_loop():
    connection = pk.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.exchange_declare(exchange="payments", exchange_type=ExchangeType.direct)

    while running:
        amount = random.randint(100, 100000)
        payment_id = generate_payment_id()
        print(f"Making payment with id {payment_id}")
        time.sleep(2)
        print(f"Payment with id {payment_id} pending")

        message_body = str(
            {
                "payment_id": payment_id,
                "amount": amount,
            }
        )
        channel.basic_publish(
            exchange="payments", routing_key="pending", body=message_body.encode()
        )
        time.sleep(3)

    connection.close()


def consumer_loop():
    connection = pk.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.exchange_declare(exchange="payments", exchange_type=ExchangeType.direct)

    queue = channel.queue_declare(queue="payments_failed")
    channel.queue_bind(
        exchange="payments", queue=queue.method.queue, routing_key="failed"
    )

    def callback(ch, method, properties, body):
        print(f"Received failed payment: {body}")

    channel.basic_consume(
        queue=queue.method.queue, on_message_callback=callback, auto_ack=True
    )

    print(f"Started consuming failed payments from {queue.method.queue}")

    channel.start_consuming()

    connection.close()


if __name__ == "__main__":
    producer_thread = threading.Thread(target=producer_loop)
    consumer_thread = threading.Thread(target=consumer_loop)

    producer_thread.start()
    consumer_thread.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping threads...")
        running = False
        producer_thread.join()
        consumer_thread.join()
        print("Threads stopped. Exiting.")
