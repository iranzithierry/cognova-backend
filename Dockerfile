FROM python:3.11

WORKDIR /app
COPY . /app

# Create a virtual environment and activate it
RUN python3 -m venv venv

# Activating virtual environment
RUN . venv/bin/activate

# Install project dependencies inside the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Generating Prisma ORM
RUN prisma generate

# Fix Prisma import issue

# RUN sed -i.bak "s/'models\./'/" ./venv/lib/python3.*/site-packages/prisma/models.py || true
RUN sed -i.bak "s/'models\./'/" ./../usr/local/lib/python3.11/site-packages/prisma/models.py || true

# Expose port
EXPOSE 8090

# Run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "4"]