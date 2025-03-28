FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a virtual environment and activate it
RUN python -m venv venv

# Install project dependencies inside the virtual environment
RUN venv/bin/pip install --no-cache-dir -r requirements.txt

# Fix Prisma import issue (adjust path for Linux)
RUN sed -i.bak "s/'models\./'/" ./venv/lib/python3.*/site-packages/prisma/models.py || true

# Expose port
EXPOSE 8090

# Run the Uvicorn server
CMD ["venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "4"]