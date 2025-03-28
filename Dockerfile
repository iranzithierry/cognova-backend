FROM python:3.11

# Create a virtual environment and activate it
RUN python3 -m venv venv

RUN ls
RUN pwd

# Activating virtual environment
RUN . venv/bin/activate

RUN ls
RUN pwd

# Install project dependencies inside the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Generating Prisma ORM
RUN prisma generate

# Fix Prisma import issue (adjust path for Linux)
RUN sed -i.bak "s/'models\./'/" ./venv/lib/python3.*/site-packages/prisma/models.py || true

# Expose port
EXPOSE 8090

# Run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "4"]