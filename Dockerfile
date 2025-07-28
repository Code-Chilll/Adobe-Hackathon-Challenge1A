FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY process_pdfs.py .

# Create input and output directories for local testing (will be overridden by Docker volumes)
RUN mkdir -p input output

ENTRYPOINT ["python", "process_pdfs.py"] 