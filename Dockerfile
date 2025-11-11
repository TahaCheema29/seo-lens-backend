FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the browsers & system dependencies
RUN playwright install --with-deps

# Copy your app code
COPY src ./src

# Default command
# CMD ["python", "-m", "src.main"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]