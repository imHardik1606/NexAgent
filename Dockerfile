# Use the official Python 3.11-slim image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements file first for layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Create the logs directory
RUN mkdir -p logs

# Run the application
CMD ["python", "main.py"]
