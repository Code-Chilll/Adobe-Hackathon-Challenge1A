# Use a slim, official Python base image compatible with linux/amd64 [cite: 57]
FROM --platform=linux/amd64 python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script and directories into the container
COPY process_pdfs.py .
COPY input/ ./input/
COPY output/ ./output/

# This command will be run when the container starts 
CMD ["python", "process_pdfs.py"]