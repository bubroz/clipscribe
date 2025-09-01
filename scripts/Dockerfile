FROM python:3.12-slim

# Install Redis client
RUN pip install redis

# Copy the script
COPY create_token_job.py /app/create_token.py

# Run the script
CMD ["python", "/app/create_token.py"]
