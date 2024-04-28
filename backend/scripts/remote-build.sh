echo "Building Docker Image..."
docker build -t yixing/ecommerce-api .
echo "Cleaning up Docker Images..."
docker image prune
echo "Stopping Docker Container..."
docker stop ecommerce-api
echo "Removing Docker Container..."
docker rm ecommerce-api
echo "Starting Docker Container..."
docker compose up -d
echo "Done!"