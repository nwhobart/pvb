# First stage: Build
FROM python:3.12-alpine AS builder

# Install build dependencies, Python packages, and remove build dependencies
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev make openssl-dev \
    && pip install --no-cache-dir --user redis requests semver prettytable \
    && apk del .build-deps

# Second stage: Final image
FROM python:3.12-alpine

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Set environment variables
ENV REDIS_HOSTNAME="localhost"
ENV REDIS_PORT="6379"

# Copy your application
COPY main.py .

CMD ["python", "-u", "main.py"]