# Use a slim version of Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only the API requirements
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API source code
COPY api/ .

# Expose the FastAPI port
EXPOSE 8080

# Run the API with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]