terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

# Sufixo aleatório para garantir nomes únicos globalmente (storage, search, openai)
resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

locals {
  suffix = random_string.suffix.result
  tags = {
    projeto    = var.project_name
    ambiente   = var.environment
    criado_por = "terraform-demo"
  }
}

# 1. Resource Group -----------------------------------------------------
resource "azurerm_resource_group" "rag" {
  name     = "demo_terraform"
  location = var.location
  tags     = local.tags
}

# 2. Storage Account (documentos fonte do RAG) ---------------------------
resource "azurerm_storage_account" "docs" {
  name                     = "st${var.project_name}${local.suffix}"
  resource_group_name      = azurerm_resource_group.rag.name
  location                 = azurerm_resource_group.rag.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.tags
}

resource "azurerm_storage_container" "docs" {
  name                  = "documentos"
  storage_account_name  = azurerm_storage_account.docs.name
  container_access_type = "private"
}

# 3. Azure AI Search (índice vetorial / busca do RAG) --------------------
resource "azurerm_search_service" "rag" {
  name                = "srch-${var.project_name}-${local.suffix}"
  resource_group_name = azurerm_resource_group.rag.name
  location            = azurerm_resource_group.rag.location
  sku                 = "basic"
  tags                = local.tags
}

# 4. Azure OpenAI (modelo de chat + embeddings) ---------------------------
resource "azurerm_cognitive_account" "openai" {
  name                = "oai-${var.project_name}-${local.suffix}"
  resource_group_name = azurerm_resource_group.rag.name
  location            = var.openai_location
  kind                = "OpenAI"
  sku_name            = "S0"
  tags                = local.tags
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = "chat-gpt4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  sku {
    name     = "Standard"
    capacity = 10
  }
}

resource "azurerm_cognitive_deployment" "embedding" {
  name                 = "embedding-ada"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-ada-002"
    version = "2"
  }

  sku {
    name     = "Standard"
    capacity = 10
  }
}
