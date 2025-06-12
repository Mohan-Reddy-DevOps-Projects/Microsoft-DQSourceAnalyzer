#!/bin/bash

echo "Getting latest Geneva image tag..."
echo "$IMAGE_NAME:$IMAGE_TAG"
oras manifest fetch $IMAGE_NAME:$IMAGE_TAG --descriptor > /root/admShellOutput.json






