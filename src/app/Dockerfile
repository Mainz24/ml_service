FROM python:3.12-slim

WORKDIR /src

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /src

RUN pip install --upgrade pip && pip install -r /src/requirements.txt

EXPOSE 8080

#COPY ./ /app

CMD ["python", "/src/app/api.py"]