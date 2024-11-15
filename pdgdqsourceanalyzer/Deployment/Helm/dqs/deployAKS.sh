#!/bin/bash

# Exit when commands complete with non-0 exit codes and display the failing command and its code
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command completed with exit code $?."' EXIT

# Define some global variables
serviceDeploymentName=purview-dqsa
appLabelName=purview-dqsa
loadBalancerName=purview-dqsa-loadbalancer
genevaDaemonsetName=geneva-services

# Test whether an AKS application deployment has completed
testDeploymentReady() {
  local deploymentName=$1
  local replicas=$(kubectl get deployment $deploymentName -o jsonpath='{.spec.replicas}')
  local readyReplicas=$(kubectl get deployment $deploymentName -o jsonpath='{.status.readyReplicas}')
  local updatedReplicas=$(kubectl get deployment $deploymentName -o jsonpath='{.status.updatedReplicas}')
  local unavailableReplicas=$(kubectl get deployment $deploymentName -o jsonpath='{.status.unavailableReplicas}')
  echo "Expected $replicas $deploymentName instance(s), found ready:${readyReplicas:-0}, updated:${updatedReplicas:-0}, unavailable:${unavailableReplicas:-0}"
  if [[ "$replicas" != "${readyReplicas:-0}" ]] || [[ "$replicas" != "${updatedReplicas:-0}" ]] || [[ "0" != "${unavailableReplicas:-0}" ]]; then
    echo "Deployment $deploymentName is not yet ready"
    return 1
  fi
  echo "Deployment $deploymentName is ready"
  return 0
}

# Test whether an AKS daemonset deploymnent has completed
testDaemonsetReady() {
  local daemonSetName=$1
  local replicas=$(kubectl get daemonset $daemonSetName -o jsonpath='{.status.desiredNumberScheduled}')
  local readyReplicas=$(kubectl get daemonset $daemonSetName -o jsonpath='{.status.numberReady}')
  local updatedReplicas=$(kubectl get daemonset $daemonSetName -o jsonpath='{.status.updatedNumberScheduled}')
  local unavailableReplicas=$(kubectl get daemonset $daemonSetName -o jsonpath='{.status.numberUnavailable}')
  echo "Expected $replicas $daemonSetName instance(s), found ready:${readyReplicas:-0}, updated:${updatedReplicas:-0}, unavailable:${unavailableReplicas:-0}"
  if [[ "$replicas" != "${readyReplicas:-0}" ]] || [[ "$replicas" != "${updatedReplicas:-0}" ]] || [[ "0" != "${unavailableReplicas:-0}" ]]; then
    echo "Daemonset $daemonSetName is not yet ready"
    return 1
  fi
  echo "Daemonset $daemonSetName is ready"
  return 0
}

# Test whether the helm chart was deployed successfully:
# 1. Deployments and daemonsets are ready
# 2. The load balancer service external IP is binded with the public IP.

testAllServicesReady() {
  local exitCode=0
  
  if ! testDeploymentReady $serviceDeploymentName; then
    echo "Waiting for all $serviceDeploymentName instances to deploy..."
    exitCode=1
  fi
  
  if ! testDaemonsetReady $genevaDaemonsetName; then
    echo "Waiting for all $genevaDaemonsetName instances to deploy..."
    exitCode=1
  fi

  # Test if the public IP is bound with the load balancer service 
  local externalIP=$(kubectl get service $loadBalancerName -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  echo "The load balancer external IP is '$externalIP'. The expected IP is '$1'"
  if [[ "$externalIP" != "$1" ]]; then
    echo "Waiting for load balancer IP to bind..."
    exitCode=1
  fi
  
  
  return $exitCode
}

# Run an arbitrary command on a node.
# Based on Bash script from https://github.com/kvaps/kubectl-enter
# Usage: execNodeCmd <nodeName> <command>
execNodeCmd() {
  if [ -z "$1" ]; then
    echo "node name is not specified."
    return 1
  fi
  
  node=$1
  image="mcr.microsoft.com/mirror/docker/library/debian:bullseye-slim"
  pod="aks-temp-$RANDOM"
  namespace="default"
  shift
  command="$@"
  nsenterCmd="\"nsenter\", \"--target\", \"1\", \"--mount\", \"--uts\", \"--ipc\", \"--net\", \"--pid\", \"--\""
  for elem in $command
  do
    nsenterCmd+=", \"$elem\""
  done
  if [ -t 0 ]; then
    tty=true
  else
    tty=false
  fi
  # Check the node
  kubectl get node $node > /dev/null || return 1
  
  overrides="$(cat <<EOT
  {
    "spec": {
      "nodeName": "$node",
      "hostPID": true,
      "containers": [
        {
          "securityContext": {
          "privileged": true
          },
          "image": "$image",
          "name": "nsenter",
          "stdin": true,
          "stdinOnce": true,
          "tty": $tty,
          "command": [ $nsenterCmd ]
        }
      ]
    }
  }
EOT
)"
  # Support Kubectl <1.18
  clientVersion=$(kubectl version --client -o yaml | awk -F'[ :"]+' '$2 == "minor" {print $3+0}')
  echo "Kubectl version is : $clientVersion"
  if [ "$clientVersion" -lt 18 ]; then
    generator="--generator=run-pod/v1"
  fi
  echo "spawning \"$pod\" on \"$node\""
  kubectl run --namespace $namespace --image "$image" --restart=Never --overrides="$overrides" --pod-running-timeout=30m   $([ "$tty" = true ] && echo -t) -i "$pod" $generator
}

# Prune cached images on the AKS cluster
pruneCachedImages() {
  version=$(kubectl version -o yaml | awk -F'[ :"]+' '$2 == "minor" {print $3+0}' | awk 'NR==2{print $1+0}')
  nodeNames=$(kubectl get node -o="jsonpath={.items[*].metadata.name}")
  echo "AKS minor server version is $version"
  for node in $nodeNames 
  do
    echo "Clearing unused cached docker images on node $node"
    if [ "$version" -lt 19 ]; then
      echo "AKS 1.18 and below: docker"
      execNodeCmd $node docker image prune --all --force
    else
      echo "AKS 1.19 and above: containerd"
      execNodeCmd $node crictl rmi --prune
    fi
  done
}

trimQuotes() {
  local temp
  temp="${1%\"}"
  temp="${temp#\"}"
  echo $temp;
}

echo "Login to Azure with the user-assigned MSI"
az login --identity
retries=0
signInExitCode=-1
until [ "${retries}" -ge 5 ]
do
   az login --identity && signInExitCode=0 && break
   retries=$((retries+1))
   sleep 15
done

echo "Printing all the environment variables"
set

echo "Set current subscription to $subId"
az account set --subscription $subId

az aks get-credentials --resource-group ${aksGroupName} --name ${aksClusterName}

echo "Get AKS node details"
kubectl get node -o wide

helm version

echo "Install support for pod managed identity"
# Feature https://github.com/Azure/aad-pod-identity
# Use explicit version rather than latest from master to avoid accidental deployment of untested versions
kubectl apply -f enable-pod-identity-with-kubenet.yaml
kubectl apply -f https://raw.githubusercontent.com/Azure/aad-pod-identity/v1.8.8/deploy/infra/mic-exception.yaml

deployment_name=$(kubectl get deployments -l app=purview-dqsa -o jsonpath='{.items[0].metadata.name}')

# Check if the deployment name was found
if [[ -n "$deployment_name" ]]; then
  echo "Setting environment variable DQS_ENV_REGION for deployment $deployment_name"
  kubectl set env deployment/$deployment_name DQS_ENV_REGION="$tlsCertName"

# echo "Install kured for automatic reboots"
kubectl apply -f ./dqs/kured/kured-1.9.2-dockerhub.yaml

echo "Extract SSL keys and certificates in PEM format from key vault $keyVaultName, secret $genevaCertName"
localCertPfx=cert.pfx
localKeyPem=key.pem
localCertPem=cert.pem


# Remove local certificates before exit.
removeLocalCerts() {
    rm -f $localCertPfx $localKeyPem $localCertPem
}

az keyvault secret download --vault-name $keyVaultName -f $localCertPfx --name $genevaCertName --encoding base64
ls -l $localCertPfx
openssl pkcs12 -in $localCertPfx -out $localKeyPem -nodes -nocerts -passin pass:
ls -l $localKeyPem
openssl pkcs12 -in $localCertPfx -out $localCertPem -nodes -nokeys -clcerts -passin pass:
ls -l $localCertPem

# https://azure.github.io/secrets-store-csi-driver-provider-azure/getting-started/installation/
echo "Install Azure Keyvault Provider For Secrets Store CSI Driver for mounting and periodically refreshing the Geneva certificate"
helm repo add csi-secrets-store-provider-azure https://azure.github.io/secrets-store-csi-driver-provider-azure/charts --force-update

# See if the csi release exists on the cluster
csiReleaseExists=$(helm list --filter csi -q)
echo "AKV CSI release: $csiReleaseExists"

# CSI parameters to enable periodic certificate refresh
akvCsiValues="constructPEMChain=true,\
secrets-store-csi-driver.enableSecretRotation=true,\
secrets-store-csi-driver.rotationPollInterval=60m"

if [ -z "$csiReleaseExists" ]; then
  echo "Installing csi..."
  helm install csi csi-secrets-store-provider-azure/csi-secrets-store-provider-azure --set "${akvCsiValues}" --wait --version 0.0.18
else
  echo "Upgrading csi..."
  helm upgrade csi csi-secrets-store-provider-azure/csi-secrets-store-provider-azure --set "${akvCsiValues}" --wait --version 0.0.18
fi


echo "Fetch properties to be set as arguments for the helm command"

publicIp=$(az network public-ip show -n $publicIpName -g $publicIpGroup --query "{ipAddress: ipAddress}" -o tsv)
podMSIClientId=$(az identity show -n $podIdentityName --subscription $podIdentitySubscriptionId -g $podIdentityGroup --query "{clientId: clientId}" -o tsv)
podMSIResourceId=$(az identity show -n $podIdentityName --subscription $podIdentitySubscriptionId -g $podIdentityGroup --query "{resourceId: id}" -o tsv)
tenantId=$(az identity show -n $podIdentityName --subscription $podIdentitySubscriptionId -g $podIdentityGroup --query "{tenantId: tenantId}" -o tsv)
allowedServiceTags=${allowedServiceTags//,/\\,}

# Parse the image metadata file produced by the dockerbuildcommand to identify the full image path.
# Pick appropriate ACR depending on whether the release is a PROD (AME) deployment or not.
# Use the full unique image name rather than the image tagged with the build number because
# the build numbers are not be unique across all build definitions for different branches of a repo.

echo "Parse the image path for release name: $helmReleaseName"
if [[ "${deploymentType,,}" == *"prod"* ]]; then
  imagePath=$(jq '.ame_unique_image_name' PdgDqsourceAnalyzerImage-metadata.json)
else
  imagePath=$(jq '.unique_image_name' PdgDqsourceAnalyzerImage-metadata.json)
fi

imagePath=$(trimQuotes $imagePath)

echo "Deployment of release $helmReleaseName will use image $imagePath with serviceTags: $allowedServiceTags"

helmParams="dqs.publicIp=$publicIp,\
dqs.publicIpGroup=$publicIpGroup,\
podIdentityResourceId=$podMSIResourceId,\
podIdentityClientId=$podMSIClientId,\
tlsDNS=$tlsDNS,\
dqs.imagePath=$imagePath,\
dqs.allowedServiceTags=$allowedServiceTags"

echo "Helm --set parameters: $helmParams"

helmFileParams="gcscert.pem=$localCertPem,gcskey.pem=$localKeyPem"
echo "Helm --set-file parameters: $helmFileParams"


# See if the current release exists on the cluster 
releaseExists=$(helm list --filter $helmReleaseName -q)
echo "Release: $releaseExists"

if [ -z "$releaseExists" ]; then
  echo "Installing release $helmReleaseName"
  helm install $helmReleaseName dqs -f dqs/generated/$helmValueFile --set "$helmParams" --set-file "$helmFileParams"
else
  echo "Upgrading release $helmReleaseName"
  helm upgrade $helmReleaseName dqs -f dqs/generated/$helmValueFile --set "$helmParams" --set-file "$helmFileParams"
fi

# Check the deployment status every few seconds, exit when deployment completes successfully, or time out.
deploymentSucceeded=1
for iteration in {1..30}
    do
        echo "--------------------------------------------------------------------------------"
        sleep 30
        echo "$(date): Checking status ($iteration)..."
        helm status $helmReleaseName
        if testAllServicesReady $publicIp; then
            deploymentSucceeded=0
            break
        fi
    done
if [ $deploymentSucceeded -eq 0 ]; then
    # Deployment succeeded
    echo "Helm install/upgrade succeeded."
    helm history $helmReleaseName
else
    # Wait loop timed out - display diagnostics and exit with failure
    echo "Deployment failed!!! Additional diagnostics..."
    echo "List pods..."
    kubectl get pod

    echo "Describe deployment..."
    kubectl describe deployment $serviceDeploymentName

    echo "List services..."
    kubectl get service

   
    echo "Describe load balancer services..."
    kubectl describe service $loadBalancerName

    echo "Dump service pod logs..."
    kubectl logs -l app=$appLabelName || echo "Logs cannot be fetched"

    # Rollback
    if [ -z "$releaseExists" ]; then
        echo "Deployment failed, deleting the release..."
        helm delete $helmReleaseName
    else
        echo "Deployment failed, rolling back to previous revision..."
        previousRevision=$(($(helm list --filter $helmReleaseName --output yaml | grep "revision" | awk -F ": " '{print $2}' | awk -F '"' '{print $2}') - 1))
        echo "Previous release revision = $previousRevision"
        helm rollback $helmReleaseName $previousRevision
    fi
fi

pruneCachedImages

removeLocalCerts

exit $deploymentSucceeded
