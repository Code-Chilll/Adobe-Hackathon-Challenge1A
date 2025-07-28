FROM --platform=linux/amd64 python:3.10-alpine as build

WORKDIR /app

# Install build dependencies for PyMuPDF
RUN apk add --no-cache --virtual .build-deps build-base musl-dev gcc zlib-dev jpeg-dev openjpeg-dev tiff-dev lcms2-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final image
FROM --platform=linux/amd64 python:3.10-alpine
WORKDIR /app

# Copy installed packages from build stage
COPY --from=build /install /usr/local
COPY process_pdfs.py .

# Create input and output directories for local testing (will be overridden by Docker volumes)
RUN mkdir -p input output

# Remove build dependencies to keep image small
RUN apk del .build-deps || true
RUN apk add --no-cache libstdc++

ENTRYPOINT ["python", "process_pdfs.py"]