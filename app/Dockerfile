FROM python:3.10-slim

WORKDIR /app

# Install poetry
RUN pip install uv

# Copy dependency files
COPY requirements.in ./

# Install dependencies
RUN uv sync

# Copy application code
COPY server/ .

# Download NLTK data during build
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 