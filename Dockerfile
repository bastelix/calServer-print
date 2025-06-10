FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
# Install required build tools and CUPS headers for pycups
RUN apt-get update \
    && apt-get install -y gcc python3-dev libcups2-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "launcher.py"]
