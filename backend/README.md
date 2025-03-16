# Backend API for E-commerce
For more details, please refer to the [API documentation](http://127.0.0.1:5018/api/docs)

## Deploy the backend application with Docker
To run the code with Docker, follow the steps below:
``` shell
# Build Dockerfile
docker build -t yixing/ecommerce-api .

# Build Dockerfile in two stages
# First stage
docker build --target builder -t yixing/ecommerce-api-builder .
# Second stage
docker build -t yixing/ecommerce-api .
```
Install MongoDB and Redis before running the application.
```shell 
docker run --name redis -p 6379:6379 --restart=always -d redis

docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest

```

```shell 
# Run code
export $(grep -v '^#' conf/dev.env | xargs) && printenv  && python main.py
```

## Run the backend application 

```shell
# Install dependencies
pip install -r requirements.txt
# Activate virtual environment
source .venv/Scripts/activate
# Run the application
export ENV=dev && python main.py
```

# Unit tests:
```shell
python pytest_integration.py
python pytest_units.py
```


# Deployment:
```shell
# Build Dockerfile
docker compose up --build -d
```
## Push to Production:
```shell
# Test the application locally
cd /workspace/backend
docker compose up --build 
# If everything is ok, save the image in the local machine
docker save -o ecommerce-api.tar yixing/ecommerce-api:latest
# Copy the image to the production server
scp -P 22 ecommerce-api.tar root@192.168.8.100:/tmp/
# Login to production server, and load the image
docker load -i /tmp/ecommerce-api.tar
# Run the container at the workspace directory
cd /workspace/backend
# Run the container
docker compose down && docker compose up -d
```