# ml_engine/Dockerfile — same pattern, note the larger image due to torch/sentence-transformers
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
# Copy the installed packages
COPY --from=builder /install /usr/local/lib/python3.11/site-packages
# Copy the executable scripts (like uvicorn) to a place on the PATH
COPY --from=builder /install/bin /usr/local/bin

COPY . .
EXPOSE 8000
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]