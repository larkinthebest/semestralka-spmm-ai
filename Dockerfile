# Use an official Python runtime as a parent image
FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by some Python packages (e.g., OpenCV, Tesseract)
# Tesseract-OCR and its language data are needed for pytesseract
# OpenCV dependencies might be needed for opencv-python
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    build-essential \
    cmake \
    git \
    libstdc++6 \
    libgomp1 \
    libcurl4-openssl-dev \
    libssl-dev \
    libblas3 \
    liblapack3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create models directory (models will be downloaded manually or mounted)
RUN mkdir -p /app/models

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8002

# Define environment variable for GPT4All models directory
ENV GPT4ALL_MODELS_PATH=/app/models

# Run the application
CMD ["python", "run.py"]
