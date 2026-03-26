FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps

COPY . .

CMD ["uvicorn", "srv.main:app", "--host", "0.0.0.0", "--port", "8000"]