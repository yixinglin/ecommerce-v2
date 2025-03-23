FROM python:3.12-slim

# Specify the working directory
WORKDIR /code

# Install dependencies
RUN apt-get update && \
    apt-get install -y fonts-wqy-zenhei && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to the working directory
COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt
RUN --mount=type=cache,target=/root/.cache pip install -r requirements.txt

# Copy the code to the working directory. This step should be after the pip install step to avoid cache invalidation.
COPY . .

# Expose port 5018
EXPOSE 5018

# Start the application
CMD ["python", "/code/main.py"]