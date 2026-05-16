FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi uvicorn \
    requests \
    neo4j \
    python-dotenv

COPY . .

EXPOSE 7688

CMD ["uvicorn", "http_server:app", "--host", "0.0.0.0", "--port", "7688"]
