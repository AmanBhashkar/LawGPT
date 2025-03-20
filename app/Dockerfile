FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libgomp1 \
    python3-pip

WORKDIR /app

# Install dependencies
COPY requirements.txt ./

# Then install other dependencies
RUN pip install uv 
RUN uv pip install -r requirements.txt --system


# Install application
COPY . .

# Install NLTK data


# Use PATH-based CMD instead of absolute path
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]