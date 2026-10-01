#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Provisions public HTTPS access for the store-front portal and the MCP
  servers (store-front-mcp / store-admin-mcp): installs ingress-nginx,
  creates the mcp-auth secret, applies the mcp-servers k8s manifests, and
  provisions an Azure Front Door profile in front of the ingress controller.

.DESCRIPTION
  This is a one-shot az/kubectl/helm CLI script (no Terraform) so it can be
  re-run against a freshly provisioned cluster without touching
  infra/terraform and risking merge conflicts with upstream
  Azure-Samples/aks-store-demo. Safe to re-run; every step is idempotent.

.PARAMETER ResourceGroup
  Resource group containing the AKS cluster.

.PARAMETER ClusterName
  AKS cluster name.

.PARAMETER Subscription
  Azure subscription ID or name. Defaults to the current az CLI context.

.PARAMETER Namespace
  Kubernetes namespace the app is deployed to. Defaults to "pets".

.PARAMETER McpAuthUsername / McpAuthPassword
  Basic auth credentials for the MCP servers (and the store-front/store-admin
  portals, if the mcp-auth and store-auth secrets should share credentials).
  Required.

.PARAMETER FrontDoorProfileName
  Azure Front Door (Standard) profile name. Defaults to "fd-aks-store-mcp".

.EXAMPLE
  ./deploy-public-access.ps1 -ResourceGroup rg-aks-store-demo-devstork70 `
    -ClusterName aks-aks-store-demo-devstork70 `
    -McpAuthUsername admin -McpAuthPassword admin
#>
param(
  [Parameter(Mandatory = $true)][string]$ResourceGroup,
  [Parameter(Mandatory = $true)][string]$ClusterName,
  [string]$Subscription = "",
  [string]$Namespace = "pets",
  [Parameter(Mandatory = $true)][string]$McpAuthUsername,
  [Parameter(Mandatory = $true)][string]$McpAuthPassword,
  [string]$FrontDoorProfileName = "fd-aks-store-mcp"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Subscription) {
  az account set --subscription $Subscription
}

Write-Host "==> Getting AKS credentials for $ClusterName" -ForegroundColor Cyan
az aks get-credentials --resource-group $ResourceGroup --name $ClusterName --overwrite-existing

###############################################################################
# 1. Install ingress-nginx (idempotent: helm upgrade --install)
###############################################################################
Write-Host "==> Installing/upgrading ingress-nginx controller" -ForegroundColor Cyan
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx --force-update | Out-Null
helm repo update ingress-nginx | Out-Null
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx `
  --namespace ingress-nginx --create-namespace `
  --set controller.service.type=LoadBalancer

Write-Host "==> Waiting for ingress-nginx controller's public IP" -ForegroundColor Cyan
$ingressIp = $null
for ($i = 0; $i -lt 60; $i++) {
  $ingressIp = kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
  if ($ingressIp) { break }
  Start-Sleep -Seconds 5
}
if (-not $ingressIp) {
  throw "Timed out waiting for ingress-nginx-controller LoadBalancer IP"
}
Write-Host "    ingress-nginx public IP: $ingressIp"

###############################################################################
# 2. Create/update the mcp-auth secret
###############################################################################
Write-Host "==> Creating/updating mcp-auth secret in namespace $Namespace" -ForegroundColor Cyan
kubectl create secret generic mcp-auth --namespace $Namespace `
  --from-literal=username=$McpAuthUsername `
  --from-literal=password=$McpAuthPassword `
  --dry-run=client -o yaml | kubectl apply -f -

###############################################################################
# 3. Apply the MCP server deployments + ingress (host substituted with the
#    live ingress-nginx IP so it works regardless of which cluster/LB this is)
###############################################################################
Write-Host "==> Applying mcp-servers k8s manifests" -ForegroundColor Cyan
kubectl apply -f "$scriptDir/k8s/store-front-mcp.yaml"
kubectl apply -f "$scriptDir/k8s/store-admin-mcp.yaml"

$ingressYaml = Get-Content "$scriptDir/k8s/ingress.yaml" -Raw
$ingressYaml = $ingressYaml -replace '__INGRESS_IP__', $ingressIp
$ingressYaml | kubectl apply -f -

###############################################################################
# 4. Provision Azure Front Door (Standard) in front of ingress-nginx
###############################################################################
Write-Host "==> Provisioning Azure Front Door profile $FrontDoorProfileName" -ForegroundColor Cyan
$profileExists = az afd profile show --resource-group $ResourceGroup --profile-name $FrontDoorProfileName 2>$null
if (-not $profileExists) {
  az afd profile create --resource-group $ResourceGroup --profile-name $FrontDoorProfileName --sku Standard_AzureFrontDoor | Out-Null
}

$endpoints = @(
  @{ Name = "store-front";      Host = "store-front.$ingressIp.nip.io" },
  @{ Name = "store-front-mcp";  Host = "store-front-mcp.$ingressIp.nip.io" },
  @{ Name = "store-admin-mcp";  Host = "store-admin-mcp.$ingressIp.nip.io" }
)

foreach ($ep in $endpoints) {
  $name = $ep.Name
  $originHostHeader = $ep.Host
  $ogName = "$name-og"
  $originName = "$name-origin"
  $routeName = "$name-route"

  Write-Host "    -- $name (origin host: $originHostHeader)"

  az afd endpoint create --resource-group $ResourceGroup --profile-name $FrontDoorProfileName `
    --endpoint-name $name --enabled-state Enabled --only-show-errors | Out-Null

  az afd origin-group create --resource-group $ResourceGroup --profile-name $FrontDoorProfileName `
    --origin-group-name $ogName `
    --probe-request-type GET --probe-protocol Http --probe-path / `
    --probe-interval-in-seconds 30 `
    --sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50 `
    --only-show-errors | Out-Null

  az afd origin create --resource-group $ResourceGroup --profile-name $FrontDoorProfileName `
    --origin-group-name $ogName --origin-name $originName `
    --host-name $ingressIp --origin-host-header $originHostHeader `
    --http-port 80 --https-port 443 --priority 1 --weight 1000 `
    --enabled-state Enabled --only-show-errors | Out-Null

  az afd route create --resource-group $ResourceGroup --profile-name $FrontDoorProfileName `
    --endpoint-name $name --route-name $routeName `
    --origin-group $ogName --supported-protocols Http Https `
    --link-to-default-domain Enabled --forwarding-protocol HttpOnly `
    --https-redirect Disabled --only-show-errors | Out-Null
}

Write-Host "==> Done. Public endpoints:" -ForegroundColor Green
foreach ($ep in $endpoints) {
  $hostName = az afd endpoint show --resource-group $ResourceGroup --profile-name $FrontDoorProfileName `
    --endpoint-name $ep.Name --query hostName -o tsv
  Write-Host "    https://$hostName"
}
