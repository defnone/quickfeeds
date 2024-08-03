# Use a multi-stage build to reduce the final image size
# Stage 1: Build and install dependencies
FROM python:3.12.3-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential gcc libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Create the final image
FROM python:3.12.3-slim
COPY --from=builder /usr/local /usr/local
WORKDIR /app

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000
ENV LOG_LEVEL=INFO
ENV LOG_FILE=logs/app.log

# Copy the entrypoint script and give it execution permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy only the necessary application files
COPY . .

# Copy version file
COPY version.txt /app/version.txt

# Create directories and symbolic links for logs and instances
RUN mkdir -p /data/instance /data/logs \
    && ln -s /data/instance /app/instance \
    && ln -s /data/logs /app/logs

# Expose the port the app runs on
EXPOSE 8000

# Run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
