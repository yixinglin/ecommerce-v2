# Backend API for E-commerce
For more details, please refer to the [API documentation](http://127.0.0.1:5018/api/docs)

## Requirements:
Install Mysql, MongoDB and Redis before running the application.
```shell 
docker run --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root -d mysql:latest
docker run --name redis -p 6379:6379 --restart=always -d redis
docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest

```

## Run the backend application with command lines. 

```shell
# Create virtual environment
python -m venv .venv
# Activate virtual environment
source .venv/Scripts/activate
# Install dependencies
pip install -r requirements.txt
# Activate virtual environment
source .venv/Scripts/activate
# Run the application
ENV=dev python main.py
```

# Unit tests:
```shell
python pytest_integration.py
python pytest_units.py
```


# Deployment
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

## 
```shell
# Login to mysql container
docker exec -it mysql-yx mysql -uroot -p

```