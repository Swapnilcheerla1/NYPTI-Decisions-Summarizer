# Dockerfile (Multi-Stage Build - Final Correct Version)

# --- Stage 1: The "Builder" Stage ---
# Instructions must start at the beginning of the line.
FROM python:3.10 AS builder

# Install system-level build tools like the gcc compiler.
# Using '&&' combines commands and reduces image layers.
RUN apt-get update && apt-get install -y build-essential

# Set up a virtual environment for clean dependency management.
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies into the virtual environment.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: The Final, "Slim" Stage ---
# Start fresh with a lightweight image for the final application.
FROM python:3.10-slim

# Set the working directory.
WORKDIR /app

# Copy the entire virtual environment with all installed libraries
# from the 'builder' stage into our final image.
COPY --from=builder /opt/venv /opt/venv

# Copy the application source code.
COPY . .

# Activate the virtual environment so the CMD uses the correct Python interpreter.
ENV PATH="/opt/venv/bin:$PATH"

# Define the default command to run when the container starts.
CMD ["python", "main.py"]