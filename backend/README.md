``` shell
# Build Dockerfile
docker build -t yixing/ecommerce-api .

# Build Dockerfile in two stages
# First stage
docker build --target builder -t yixing/ecommerce-api-builder .
# Second stage
docker build -t yixing/ecommerce-api .
```


```shell 
# Run code
export $(grep -v '^#' conf/dev.env | xargs) && printenv  && python main.py
```