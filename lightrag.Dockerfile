FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir "lightrag-hku[api]"

EXPOSE 9621

CMD ["lightrag-server", "--host", "0.0.0.0", "--port", "9621"]
