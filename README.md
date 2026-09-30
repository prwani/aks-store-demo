---
page_type: sample
languages:
- azdeveloper
- go
- javascript
- rust
- nodejs
- python
- bicep
- terraform
- dockerfile
products:
- azure
- azure-kubernetes-service
- azure-openai
- azure-cosmos-db
- azure-container-registry
- azure-service-bus
- azure-monitor
- azure-log-analytics
- azure-managed-grafana
- azure-key-vault
urlFragment: aks-store-demo
name: AKS Store Demo
description: This sample demo app consists of a group of containerized microservices that can be easily deployed into an Azure Kubernetes Service (AKS) cluster. 
---
<!-- YAML front-matter schema: https://review.learn.microsoft.com/en-us/help/contribute/samples/process/onboarding?branch=main#supported-metadata-fields-for-readmemd -->

# AKS Store Demo

This sample demo app consists of a group of containerized microservices that can be easily deployed into an Azure Kubernetes Service (AKS) cluster. This is meant to show a realistic scenario using a polyglot architecture, event-driven design, and common open source back-end services (eg - RabbitMQ, MongoDB). The application also leverages OpenAI's GPT-3 models to generate product descriptions. This can be done using either [Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/overview) or [OpenAI](https://openai.com/).

This application is inspired by another demo app called [Red Dog](https://github.com/Azure/reddog-code).

> [!NOTE]
> This is not meant to be an example of perfect code to be used in production, but more about showing a realistic application running in AKS. 

<!-- 
To walk through a quick deployment of this application, see the [AKS Quickstart](https://learn.microsoft.com/azure/aks/learn/quick-kubernetes-deploy-cli).

To walk through a complete experience where this code is packaged into container images, uploaded to Azure Container Registry, and then run in and AKS cluster, see the [AKS Tutorials](https://learn.microsoft.com/azure/aks/tutorial-kubernetes-prepare-app).

 -->

## Architecture

The application has the following services: 

| Service | Description |
| --- | --- |
| `makeline-service` | This service handles processing orders from the queue and completing them (Golang) |
| `order-service` | This service is used for placing orders (Javascript) |
| `product-service` | This service is used to perform CRUD operations on products (Rust) |
| `store-front` | Web app for customers to place orders (Vue.js) |
| `store-admin` | Web app used by store employees to view orders in queue and manage products (Vue.js) | 
| `virtual-customer` | Simulates order creation on a scheduled basis (Rust) |
| `virtual-worker` | Simulates order completion on a scheduled basis (Rust) |
| `ai-service` | Optional service for adding generative text and graphics creation (Python) |
| `store-front-mcp` | MCP server exposing store-front functionality as AI assistant tools (Python) |
| `store-admin-mcp` | MCP server exposing store-admin functionality as AI assistant tools (Python) |
| `mongodb` | MongoDB instance for persisted data |
| `rabbitmq` | RabbitMQ for an order queue |

![Logical Application Architecture Diagram](assets/demo-arch-with-openai.png)

## Run the app on Azure Kubernetes Service (AKS)

To learn how to deploy this app on AKS, see [Quickstart: Deploy an Azure Kubernetes Service (AKS) cluster using Azure CLI](https://learn.microsoft.com/azure/aks/learn/quick-kubernetes-deploy-cli).

> [!NOTE]
> The above article shows a simplified version of the store app with some services removed. For the full application, you can use the `aks-store-all-in-one.yaml` file in this repo.

## Run on any Kubernetes

This application uses public images stored in GitHub Container Registry and Microsoft Container Registry (MCR). Once your Kubernetes cluster of choice is setup, you can deploy the full app with the below commands.

This deployment deploys everything except the `ai-service` that integrates OpenAI. If you want to try integrating the OpenAI component, take a look at this article: [Deploy an application that uses OpenAI on Azure Kubernetes Service (AKS)](https://learn.microsoft.com/azure/aks/open-ai-quickstart?tabs=aoai).

The `store-front` and `store-admin` web portals are protected with HTTP Basic
authentication (see [Authentication](#authentication)), so create the
`store-auth` secret with the credentials you want to sign in with before
deploying:

```bash
kubectl create ns pets

kubectl create secret generic store-auth -n pets \
  --from-literal=username='<your-username>' \
  --from-literal=password='<your-password>'

kubectl apply -f https://raw.githubusercontent.com/Azure-Samples/aks-store-demo/main/aks-store-all-in-one.yaml -n pets
```

## Run the app locally

The application is designed to be [run in an AKS cluster](#run-the-app-on-aks), but can also be run locally using Docker Compose.

> [!TIP]
> You must have [Docker Desktop](https://www.docker.com/products/docker-desktop) installed to run this app locally. If you do not have it installed locally, you can try opening this repo in a [GitHub Codespace instead](#run-the-app-with-github-codespaces)

To run this app locally:

Clone the repo to your development computer and navigate to the directory:

```console
git clone https://github.com/Azure-Samples/aks-store-demo.git
cd aks-store-demo
```

Configure your Azure OpenAI or OpenAI API keys in [`docker-compose.yml`](./docker-compose.yml) using the environment variables in the `ai-service` section:

```yaml
  ai-service:
    build: src/ai-service
    container_name: 'ai-service'
    ...
    environment:
      - USE_AZURE_OPENAI=True # set to False if you are not using Azure OpenAI
      - AZURE_OPENAI_DEPLOYMENT_NAME= # required if using Azure OpenAI
      - AZURE_OPENAI_ENDPOINT= # required if using Azure OpenAI
      - OPENAI_API_KEY= # always required
      - OPENAI_ORG_ID= # required if using OpenAI
    ...
```

Alternatively, if you do not have access to Azure OpenAI or OpenAI API keys, you can run the app without the `ai-service` by commenting out the `ai-service` section in [`docker-compose.yml`](./docker-compose.yml). For example:

```yaml
#  ai-service:
#    build: src/ai-service
#    container_name: 'ai-service'
...
#    networks:
#      - backend_services
```

Set the credentials used to sign in to the `store-front` and `store-admin`
portals (see [Authentication](#authentication)) and start the app using
`docker compose`. For example:

```bash
export AUTH_USERNAME=<your-username>
export AUTH_PASSWORD=<your-password>

docker compose up
```

To stop the app, you can hit the `CTRL+C` key combination in the terminal window where the app is running.

## Authentication

The two web portals and the two MCP servers all require credentials:

| Component | Mechanism | Credentials from |
| --- | --- | --- |
| `store-front` / `store-admin` | Login page in the app; nginx enforces HTTP Basic auth on every `/api/*` call | `AUTH_USERNAME` / `AUTH_PASSWORD` env vars (Kubernetes: the `store-auth` secret) |
| `store-front-mcp` / `store-admin-mcp` | HTTP Basic auth on the `/mcp` endpoint | `MCP_AUTH_USERNAME` / `MCP_AUTH_PASSWORD` env vars (Kubernetes: the `mcp-auth` secret) |

Signing in to a portal stores the credentials for the browser session only; the
"Sign out" button in the navigation bar clears them. Containers refuse to start
when the credentials are missing; set `AUTH_ENABLED=false` (portals) or
`MCP_AUTH_ENABLED=false` (MCP servers) to run without authentication during
local development.

Since HTTP Basic credentials are sent on every request, always serve these
components over HTTPS outside of local development.

For instructions on connecting the MCP servers to ChatGPT, Claude Desktop and
Microsoft 365 Copilot, see [docs/mcp-clients.md](./docs/mcp-clients.md).

## Run the app with GitHub Codespaces

This repo also includes [DevContainer configuration](./.devcontainer/devcontainer.json), so you can open the repo using [GitHub Codespaces](https://docs.github.com/en/codespaces/overview). This will allow you to run the app in a container in the cloud, without having to install Docker on your local machine. When the Codespace is created, you can run the app using the same instructions as above.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=648726487)

## Deploy the app to Azure using Azure Developer CLI

See the [Azure Developer CLI](./docs/azd.md) documentation for instructions on how to quickly deploy the app to Azure.

## MCP Servers

This repository includes Model Context Protocol (MCP) servers that expose the store functionality as tools for AI assistants. The MCP servers are located in the [`mcp-servers/`](./mcp-servers/) directory.

### Available MCP Servers

- **Store Front MCP Server** (`store_front_server.py`) - Provides tools for customer shopping workflows:
  - Browse products
  - Manage shopping cart
  - Submit orders

- **Store Admin MCP Server** (`store_admin_server.py`) - Provides tools for administrative tasks:
  - Product management (create, read, update, delete)
  - Order management and processing
  - AI-powered product description generation
  - Order analytics and statistics

### Quick Start

1. Install dependencies:
   ```bash
   cd mcp-servers
   pip install -r requirements.txt
   ```

2. Run the servers:
   ```bash
   # Store front server
   python store_front_server.py
   
   # Store admin server  
   python store_admin_server.py
   ```

3. Use with any MCP-compatible AI assistant or client.

For detailed documentation, see the [MCP Servers README](./mcp-servers/README.md).

## Additional Resources

- AKS Documentation. https://learn.microsoft.com/azure/aks
- Kubernetes Learning Path. https://azure.microsoft.com/resources/kubernetes-learning-path 
