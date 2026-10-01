#!/usr/bin/env bash
# Provisions public HTTPS access for the store-front portal and the MCP
# servers (store-front-mcp / store-admin-mcp): installs ingress-nginx,
# creates the mcp-auth secret, applies the mcp-servers k8s manifests, and
# provisions an Azure Front Door profile in front of the ingress controller.
#
# This is a one-shot az/kubectl/helm CLI script (no Terraform) so it can be
# re-run against a freshly provisioned cluster without touching
# infra/terraform and risking merge conflicts with upstream
# Azure-Samples/aks-store-demo. Safe to re-run; every step is idempotent.
#
# Usage:
#   ./deploy-public-access.sh -g <resource-group> -c <cluster-name> \
#       -u <mcp-auth-username> -p <mcp-auth-password> \
#       [-s <subscription>] [-n <namespace, default: pets>] \
#       [-f <front-door-profile-name, default: fd-aks-store-mcp>]

set -euo pipefail

NAMESPACE="pets"
FRONTDOOR_PROFILE="fd-aks-store-mcp"
SUBSCRIPTION=""

while getopts "g:c:s:n:u:p:f:" opt; do
  case $opt in
    g) RESOURCE_GROUP="$OPTARG" ;;
    c) CLUSTER_NAME="$OPTARG" ;;
    s) SUBSCRIPTION="$OPTARG" ;;
    n) NAMESPACE="$OPTARG" ;;
    u) MCP_AUTH_USERNAME="$OPTARG" ;;
    p) MCP_AUTH_PASSWORD="$OPTARG" ;;
    f) FRONTDOOR_PROFILE="$OPTARG" ;;
    *) echo "Unknown option"; exit 1 ;;
  esac
done

: "${RESOURCE_GROUP:?-g <resource-group> is required}"
: "${CLUSTER_NAME:?-c <cluster-name> is required}"
: "${MCP_AUTH_USERNAME:?-u <mcp-auth-username> is required}"
: "${MCP_AUTH_PASSWORD:?-p <mcp-auth-password> is required}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "$SUBSCRIPTION" ]]; then
  az account set --subscription "$SUBSCRIPTION"
fi

echo "==> Getting AKS credentials for $CLUSTER_NAME"
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$CLUSTER_NAME" --overwrite-existing

###############################################################################
# 1. Install ingress-nginx (idempotent: helm upgrade --install)
###############################################################################
echo "==> Installing/upgrading ingress-nginx controller"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx --force-update >/dev/null
helm repo update ingress-nginx >/dev/null
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer

echo "==> Waiting for ingress-nginx controller's public IP"
INGRESS_IP=""
for i in $(seq 1 60); do
  INGRESS_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
  if [[ -n "$INGRESS_IP" ]]; then break; fi
  sleep 5
done
if [[ -z "$INGRESS_IP" ]]; then
  echo "Timed out waiting for ingress-nginx-controller LoadBalancer IP" >&2
  exit 1
fi
echo "    ingress-nginx public IP: $INGRESS_IP"

###############################################################################
# 2. Create/update the mcp-auth secret
###############################################################################
echo "==> Creating/updating mcp-auth secret in namespace $NAMESPACE"
kubectl create secret generic mcp-auth --namespace "$NAMESPACE" \
  --from-literal=username="$MCP_AUTH_USERNAME" \
  --from-literal=password="$MCP_AUTH_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

###############################################################################
# 3. Apply the MCP server deployments + ingress (host substituted with the
#    live ingress-nginx IP so it works regardless of which cluster/LB this is)
###############################################################################
echo "==> Applying mcp-servers k8s manifests"
kubectl apply -f "$SCRIPT_DIR/k8s/store-front-mcp.yaml"
kubectl apply -f "$SCRIPT_DIR/k8s/store-admin-mcp.yaml"
sed "s/__INGRESS_IP__/$INGRESS_IP/g" "$SCRIPT_DIR/k8s/ingress.yaml" | kubectl apply -f -

###############################################################################
# 4. Provision Azure Front Door (Standard) in front of ingress-nginx
###############################################################################
echo "==> Provisioning Azure Front Door profile $FRONTDOOR_PROFILE"
if ! az afd profile show --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" >/dev/null 2>&1; then
  az afd profile create --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" --sku Standard_AzureFrontDoor >/dev/null
fi

ENDPOINT_NAMES=("store-front" "store-front-mcp" "store-admin-mcp")

for name in "${ENDPOINT_NAMES[@]}"; do
  ORIGIN_HOST_HEADER="${name}.${INGRESS_IP}.nip.io"
  OG_NAME="${name}-og"
  ORIGIN_NAME="${name}-origin"
  ROUTE_NAME="${name}-route"

  echo "    -- $name (origin host: $ORIGIN_HOST_HEADER)"

  az afd endpoint create --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" \
    --endpoint-name "$name" --enabled-state Enabled --only-show-errors >/dev/null

  az afd origin-group create --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" \
    --origin-group-name "$OG_NAME" \
    --probe-request-type GET --probe-protocol Http --probe-path / \
    --probe-interval-in-seconds 30 \
    --sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50 \
    --only-show-errors >/dev/null

  az afd origin create --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" \
    --origin-group-name "$OG_NAME" --origin-name "$ORIGIN_NAME" \
    --host-name "$INGRESS_IP" --origin-host-header "$ORIGIN_HOST_HEADER" \
    --http-port 80 --https-port 443 --priority 1 --weight 1000 \
    --enabled-state Enabled --only-show-errors >/dev/null

  az afd route create --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" \
    --endpoint-name "$name" --route-name "$ROUTE_NAME" \
    --origin-group "$OG_NAME" --supported-protocols Http Https \
    --link-to-default-domain Enabled --forwarding-protocol HttpOnly \
    --https-redirect Disabled --only-show-errors >/dev/null
done

echo "==> Done. Public endpoints:"
for name in "${ENDPOINT_NAMES[@]}"; do
  HOSTNAME=$(az afd endpoint show --resource-group "$RESOURCE_GROUP" --profile-name "$FRONTDOOR_PROFILE" \
    --endpoint-name "$name" --query hostName -o tsv)
  echo "    https://$HOSTNAME"
done
