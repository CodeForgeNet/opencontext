FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full pcsl package (for proper module imports)
COPY pcsl/ /app/pcsl/

# Copy context.json to app root
COPY context.json /app/context.json

# Copy pyproject.toml for editable install
COPY pyproject.toml /app/

# Install pcsl package in editable mode so 'from pcsl.pcsl_server' works
RUN pip install -e /app

EXPOSE 8000

CMD ["uvicorn", "pcsl.pcsl_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
