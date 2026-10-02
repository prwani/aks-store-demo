# Deploying the AKS Store Demo app to Azure using Azure Developer CLI

Using the [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview), you can deploy this solution to Azure. By default it ships prebuilt container images and RabbitMQ/DocumentDB; you can also opt into Azure Service Bus and Azure Cosmos DB, and even build app images from source.

## Prerequisites

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=648726487)

Opening the [AKS Store Demo repo](https://github.com/Azure-Samples/aks-store-demo) in [GitHub Codespaces](https://github.com/features/codespaces) is preferred; however, if you want to run the app locally, you will need the following tools:

- [Azure CLI](https://learn.microsoft.com/cli/azure/what-is-azure-cli)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview) version 1.15.0 or later
- [Visual Studio Code](https://code.visualstudio.com/)
- A running Docker Desktop or Podman container runtime (required by the AKS `azd` target)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [kubelogin](https://azure.github.io/kubelogin/install.html)
- [Helm](https://helm.sh/docs/intro/install/)
- [Kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/) only when using the build-from-source variant
- [Git](https://git-scm.com/)
- [Terraform](https://www.terraform.io/)
- Bash shell

## Get started

To get started, authenticate to Azure using the Azure Developer CLI and Azure CLI.

```bash
# authenticate to Azure Developer CLI
azd auth login

# enable Helm support
azd config set alpha.aks.helm on

# authenticate to Azure CLI
az login
```

The default `azure.yaml` deployment uses an external Helm chart and does not
require Kustomize. Enable `alpha.aks.kustomize` only when deploying with
`azure-build-from-source.yaml`.

> [!WARNING]
> Before you run the `azd up` command, make sure that you have the "Owner" role on the subscription you are deploying to. This is because the infrastructure-as-code templates will create Azure role based access control (RBAC) assignments. Otherwise, the deployment will fail.
>
> You may also need to register the following Azure resource providers in your subscription if they are not already registered:
>
> - `Microsoft.AlertsManagement` (if using observability tools)
> - `Microsoft.CognitiveServices` (for Azure OpenAI)
> - `Microsoft.ContainerService` (for AKS)
> - `Microsoft.DocumentDB` (if using Cosmos DB)
> - `Microsoft.KeyVault` (for Key Vault)
> - `Microsoft.OperationalInsights` (if using observability tools)
> - `Microsoft.ServiceBus` (if using Service Bus)
>
> You can register these providers using the Azure CLI:
>
> ```bash
> az provider register --namespace Microsoft.AlertsManagement
> az provider register --namespace Microsoft.CognitiveServices
> az provider register --namespace Microsoft.ContainerService
> az provider register --namespace Microsoft.DocumentDB
> az provider register --namespace Microsoft.KeyVault
> az provider register --namespace Microsoft.OperationalInsights
> az provider register --namespace Microsoft.ServiceBus
> ```

When selecting an Azure region, choose one that supports all services used here: Azure OpenAI, AKS, Key Vault, Service Bus, Cosmos DB, Log Analytics, Azure Monitor (managed Prometheus).

### Availability zone support

For increased resiliency you may want to deploy into a region that supports Availability Zones. Availability zone mappings are assigned per subscription, so the set of zones available can vary between subscriptions and regions. You can use the following command to list regions that support all three availability zones (1, 2, and 3):

```bash
az account list-locations \
  --query "sort_by([? (availabilityZoneMappings != null && contains(availabilityZoneMappings[].logicalZone, '1') && contains(availabilityZoneMappings[].logicalZone, '2') && contains(availabilityZoneMappings[].logicalZone, '3')) || (metadata.availabilityZoneMappings != null && contains(metadata.availabilityZoneMappings[].logicalZone, '1') && contains(metadata.availabilityZoneMappings[].logicalZone, '2') && contains(metadata.availabilityZoneMappings[].logicalZone, '3')) ], &name)[].{Region:name}" \
  --output table
```

See the [Azure documentation on availability zones](https://learn.microsoft.com/azure/reliability/availability-zones-overview) for details and service-specific guidance.

If you are deploying Azure OpenAI, ensure your subscription has enough
[quota](https://learn.microsoft.com/azure/ai-services/openai/how-to/quota?tabs=cli)
for the selected model and deployment type. The current default text model is
`gpt-5.4-mini`. You can inspect regional usage with:

```bash
REGION=swedencentral

az cognitiveservices usage list \
  --location $REGION \
  --query "[].{name: name.value, currentValue:currentValue, limit: limit}" \
  -o table
```

### Deployment settings

The infrastructure-as-code templates in this repo use variables to define the deployment settings. You can set these variables using the Azure Developer CLI and the templates will evaluate them to provision the resources.

The following environment variables control what gets deployed:

| Variable                          | Description                                                                                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AZURE_LOCATION`                  | The Azure region for the deployment.                                                                                                                               |
| `AZURE_AKS_LOCATION`              | Optional AKS-only region override. Defaults to `AZURE_LOCATION`; useful when AKS capacity is constrained in the deployment region.                                  |
| `AKS_NODE_POOL_VM_SIZE`           | AKS node VM size. Default: `Standard_D2s_v6`.                                                                                                                      |
| `DEPLOY_AZURE_CONTAINER_REGISTRY` | Set `true` to provision Azure Container Registry (ACR). When enabled, images are either imported from GHCR or built to ACR and the deployment uses that registry.  |
| `BUILD_CONTAINERS`                | With ACR enabled (above), set `true` to build images from `src/*` using `az acr build`. If `false`/unset, images are imported from GHCR into ACR.                  |
| `DEPLOY_AZURE_OPENAI`             | Set `true` to deploy Azure OpenAI and enable `ai-service` with workload identity.                                                                                  |
| `AZURE_OPENAI_LOCATION`           | Region for Azure OpenAI. See [model availability](https://learn.microsoft.com/azure/ai-services/openai/concepts/models#provisioned-deployment-model-availability). |
| `DEPLOY_IMAGE_GENERATION_MODEL`   | Set `true` to deploy an Azure OpenAI image generation model (for example `gpt-image-2`) along with Azure OpenAI.                                                   |
| `DEPLOY_AZURE_SERVICE_BUS`        | Set `true` to deploy Azure Service Bus (RabbitMQ disabled in app).                                                                                                 |
| `DEPLOY_AZURE_COSMOSDB`           | Set `true` to deploy Azure Cosmos DB (DocumentDB disabled in app).                                                                                                 |
| `AZURE_COSMOSDB_ACCOUNT_KIND`     | Cosmos DB API kind: `MongoDB` or `GlobalDocumentDB` (SQL API). Default: `GlobalDocumentDB`.                                                                        |
| `DEPLOY_OBSERVABILITY_TOOLS`      | Set `true` to deploy Log Analytics, managed Prometheus, and enable Container Insights.                                                                             |
| `SOURCE_REGISTRY`                 | Source container registry for images. Default: `ghcr.io/azure-samples`.                                                                                            |
| `AUTH_USERNAME`                   | **Required.** Username used to sign in to the `store-front` and `store-admin` portals.                                                                              |
| `AUTH_PASSWORD`                   | **Required.** Password used to sign in to the `store-front` and `store-admin` portals.                                                                              |

These environment variables listed above can be set with commands like this:

```bash
# set the main deployment location
azd env set AZURE_LOCATION swedencentral

# optionally place only the AKS cluster in a different region
azd env set AZURE_AKS_LOCATION northeurope

# set the SKU of the virtual machine scale set nodes in the AKS cluster
azd env set AKS_NODE_POOL_VM_SIZE Standard_D2s_v6

# deploys azure container registry and imports containers from github container registry
azd env set DEPLOY_AZURE_CONTAINER_REGISTRY true

# deploys Azure OpenAI
azd env set DEPLOY_AZURE_OPENAI true

# Azure OpenAI region
azd env set AZURE_OPENAI_LOCATION swedencentral

# deploys azure service bus
azd env set DEPLOY_AZURE_SERVICE_BUS true

# deploys azure cosmos db with the sql api
azd env set DEPLOY_AZURE_COSMOSDB true

# set Cosmos DB account kind (GlobalDocumentDB for SQL API, MongoDB for MongoDB API)
azd env set AZURE_COSMOSDB_ACCOUNT_KIND GlobalDocumentDB

# deploys aks observability tools
azd env set DEPLOY_OBSERVABILITY_TOOLS true

# set custom source registry (optional)
azd env set SOURCE_REGISTRY ghcr.io/azure-samples

# set the credentials used to sign in to the store-front and store-admin portals (required)
azd env set AUTH_USERNAME <username>
azd env set AUTH_PASSWORD <password>
```

> [!NOTE]
> If none of these are set, only the AKS cluster is deployed. Workload identity is enabled by default and applied automatically to services that integrate with Azure (OpenAI, Service Bus, Cosmos DB).

## Deploy the app

Provision and deploy the app with a single command.

```bash
azd up
```

When you run the `azd up` command for the first time, you will be asked for a bit of information:

- **Environment name:** This is the name of the environment that will be created so that Azure Developer CLI can keep track of the resources that are created.
- **Azure subscription:** You will be asked to select the Azure subscription that you want to use. If you only have one subscription, it will be selected by default.
- **Azure location:** You will be asked to select the Azure location where the resources will be created. You can select the location that is closest to you but you must ensure that the location supports all the resources that will be created. If you are unsure of which region to use, select "East US 2".

After you provide the information, `azd up` registers providers/features and installs required Azure CLI extensions. It then runs Terraform to provision Azure resources and deploys the app to AKS using a Helm chart. Workload identity is configured automatically for services that talk to Azure resources.

Provisioning time varies; AKS and model deployments can take considerably
longer than a few minutes.

`AZURE_AKS_LOCATION` overrides the cluster region only. The resource group and
other Azure services remain in `AZURE_LOCATION`.

When `DEPLOY_AZURE_OPENAI=true`, the deployment also creates the configured
Azure OpenAI resource and model deployments, which can be managed through
Azure AI Foundry; the default text model is
`gpt-5.4-mini`, and image generation is added when
`DEPLOY_IMAGE_GENERATION_MODEL=true`. The default Helm deployment keeps the
`store-front` and `store-admin` Services internal (`ClusterIP`). It does not
deploy the separate MCP servers, ingress-nginx, or Azure Front Door public
endpoints; those are configured afterward by the scripts in
[`mcp-servers/README.md`](../mcp-servers/README.md).

> [!NOTE]
> Infra defaults to [Terraform](../infra/terraform). To use [Bicep](../infra/bicep) instead, open `azure.yaml` and change:
>
> - `infra.provider: bicep`
> - `infra.path: infra/bicep`
>
> The application deployment remains Helm-based.

### Build from source (optional)

For a full source-to-ACR build and Kustomize-based deploy:

1. Swap the azd config to the build-from-source variant

```bash
mv azure.yaml azure.yaml.bak
mv azure-build-from-source.yaml azure.yaml
```

1. Ensure ACR is enabled (images will be built and pushed there)

```bash
azd env set DEPLOY_AZURE_CONTAINER_REGISTRY true
```

This flow builds Docker images for each service and deploys using Kustomize overlays.

## Validate the deployment

Once the deployment completes, get the resource group:

```bash
azd env get-value AZURE_RESOURCE_GROUP
```

In the AKS resource, check Workloads, Services, and Ingresses in the `pets`
namespace. The `store-front` and `store-admin` app Services are `ClusterIP`;
the public ingress controller is installed separately by the public-access
deployment.

The public portal URLs are created by the public-access deployment described
in [`mcp-servers/README.md`](../mcp-servers/README.md). If you deployed Azure
Service Bus, use Service Bus Explorer to inspect order messages. If you
deployed Azure Cosmos DB, use its data explorer to inspect order records.

## Clean up

When you are done testing the deployment, you can clean up the resources using the `azd down` command.

```bash
azd down --force --purge
```
