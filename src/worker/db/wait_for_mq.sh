#!/bin/sh
# wait_for_mq.sh

host=rabbitmq

sleep 5

until nc -z rabbitmq 5672; do
  echo "RabbitMQ недоступен - ожидание..."
  sleep 1
done

echo "RabbitMQ запущен, выполнение команды приложения"
exec "$@"