#!/bin/bash

cd ./Helm
chmod +x ./dqs/deployAKS.sh;

IMAGE_VERSION=$(date +"%m-%d-%Y-%H-%M")
echo "Using datetime ${IMAGE_VERSION}"
echo  "{\"unique_image_name\": \"dataqualityacr.azurecr.io/dataqualityservice:${IMAGE_VERSION}\"}" > ./DataQualityServiceImage-metadata.json

tar -czf ../deployAKS.tar.gz *;
pwd
cd ../../../src/Services/DataQuality/Source;


docker build --no-cache -t dataqualityacr.azurecr.io/dataqualityservice:"${IMAGE_VERSION}" .
az acr login --name dataqualityacr
docker push dataqualityacr.azurecr.io/dataqualityservice:"${IMAGE_VERSION}"