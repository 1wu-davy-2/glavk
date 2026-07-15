FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

COPY app ./app
COPY sql ./sql
COPY docker-entrypoint.sh /usr/local/bin/glavk-entrypoint.sh
RUN chmod 755 /usr/local/bin/glavk-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/glavk-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
