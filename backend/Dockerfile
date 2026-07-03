# Use official slim Python runtime
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /workspace

# Install system dependencies required for OpenCV image rendering
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependency manifest first (leveraging Docker cache layer)
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source directory
COPY . /workspace/backend

# Expose port 8000 for FastAPI router communication
EXPOSE 8000

# Set Python Path variable
ENV PYTHONPATH=/workspace

# Start backend dev server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
