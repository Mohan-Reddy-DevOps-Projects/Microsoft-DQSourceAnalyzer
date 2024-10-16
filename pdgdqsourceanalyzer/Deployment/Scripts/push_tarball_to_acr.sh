#!/bin/bash
set -e

if [ -z "${DESTINATION_ACR_NAME}" ]; then
    echo "DESTINATION_ACR_NAME is unset, unable to continue"
    exit 1;
fi

if [ -z "${TARBALL_IMAGE_FILE_NAME}" ]; then
    echo "TARBALL_IMAGE_FILE_SAS is unset, unable to continue"
    exit 1;
fi

echo "Login cli using managed identity"
retries=0
signInExitCode=-1
until [ "${retries}" -ge 5 ]
do
   az login --identity && signInExitCode=0 && break
   retries=$((retries+1))
   sleep 15
done

if [ "${signInExitCode}" -eq 0 ]; then
    echo "Logged into az with identity"
else
    echo "Failed logging in az with identity"
    exit 1
fi

TMP_FOLDER=$(mktemp -d)
cd "${TMP_FOLDER}"

echo "Downloading docker tarball image from ${TARBALL_IMAGE_FILE_NAME}"
wget -O img.tar.gz "${TARBALL_IMAGE_FILE_NAME}"
wget -O img-meta.json "${IMAGE_METADATA_FILE_NAME}"

gunzip img.tar.gz

echo "Display all files recursively"
ls -lR

echo "Set execution permissions for crane"
chmod +x /package/unarchive/crane

echo "Getting acr credentials"
TOKEN_QUERY_RES=$(az acr login -n "${DESTINATION_ACR_NAME}" -t)
TOKEN=$(echo "${TOKEN_QUERY_RES}" | jq -r '.accessToken')
DESTINATION_ACR=$(echo "${TOKEN_QUERY_RES}" | jq -r '.loginServer')
/package/unarchive/crane auth login "${DESTINATION_ACR}" -u "00000000-0000-0000-0000-000000000000" -p "${TOKEN}"


REPOSITORY_NAME="$(jq -r '.repository_name' img-meta.json)"
IMAGE_VER_TAG="$(jq -r '.build_tag' img-meta.json)"

echo "repository_name ${REPOSITORY_NAME}"
echo "IMAGE_VER_TAG ${IMAGE_VER_TAG=}"
DEST_IMAGE_FULL_NAME="${DESTINATION_ACR}/${REPOSITORY_NAME}:${IMAGE_VER_TAG}"

echo "Pushing file ${TARBALL_IMAGE_FILE} to ${DEST_IMAGE_FULL_NAME}"
/package/unarchive/crane push img.tar "${DEST_IMAGE_FULL_NAME}"
