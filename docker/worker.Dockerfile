# Use the same base for consistency
FROM python:3.11-slim

# Install system dependencies needed for Qiskit's C++ components
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install worker requirements (Celery, Qiskit, Redis)
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Worker source code
COPY worker/ .

# Run the Celery worker
# -A tasks: points to the tasks.py file
# --loglevel=info: essential for debugging in K8s logs
# -P solo: prevents over-allocating memory in small K8s pods
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "-P", "solo"]