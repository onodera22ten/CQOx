FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY ciq/ ./ciq/
COPY data/ ./data/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Make start script executable
RUN chmod +x /app/scripts/start_services.sh

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/logs /app/reports

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application (both gateway and engine)
CMD ["/app/scripts/start_services.sh"]
