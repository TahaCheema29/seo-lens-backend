FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the browsers & system dependencies
RUN playwright install --with-deps

# Copy your app code
<<<<<<< HEAD
COPY . .

# Default command
CMD ["python", "crawler.py", "keyword_rank_checker.py", "seo_analyzer.py", "keyword_research.py"]
=======
COPY src ./src

# Default command
# CMD ["python", "-m", "src.main"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> 43d941915cb4c47697e1f2b55cb910336a663044
