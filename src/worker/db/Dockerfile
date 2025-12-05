FROM python:3.12-slim

WORKDIR /src

# Устанавливаем netcat (nc) для скрипта ожидания воркеров
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем скрипт ожидания
COPY ./wait_for_mq.sh /usr/bin/wait_for_mq.sh

RUN chmod +x /usr/bin/wait_for_mq.sh

COPY requirements.txt /src

RUN pip install --upgrade pip && pip install -r /src/requirements.txt

#EXPOSE 8080
#COPY ./ /app
#CMD ["python", "/app/src/api.py"]