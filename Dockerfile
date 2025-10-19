# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8002 for the FastAPI application
EXPOSE 8002

# Command to run the application
# This assumes `run.py` is the entry point for your FastAPI app
CMD ["python", "run.py"]
