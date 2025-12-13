# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any needed for scipy/numpy)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
# We'll generate a requirements.txt on the fly or assume one exists
# For this example, we list them explicitly
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    tensorflow \
    pyyaml \
    requests \
    beautifulsoup4 \
    scikit-learn \
    croniter \
    google-cloud-storage

# Copy the current directory contents into the container at /app
COPY . /app

# Make sure scripts are executable
RUN chmod +x *.py

# Define environment variable
ENV PYTHONUNBUFFERED=1

# The entrypoint will be decided by the Cloud Run Job command
# But we can set a default
CMD ["python", "production_app_v2.py"]
