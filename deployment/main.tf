locals {
  keyvault-name = lower(join("", [var.project-name, "-kv-", var.resource-group-name]))
  timestamp_string = tostring(formatdate("YYYYMMDDhhmmss", timestamp()))
}
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.62.1"
    }
  }
  backend "azurerm" {
    container_name   = "tfstate"
    key              = "terraform.tfstate"
    use_azuread_auth = true
  }

  required_version = ">= 1.1.0"
}

provider "azurerm" {
  features {}
  storage_use_azuread = true
}

data "azurerm_resource_group" "rg" {
  name = var.resource-group-name
}
#### key vault with env variables for function ######################################################################
data "azurerm_key_vault" "keyvault" {
  resource_group_name = var.resource-group-name
  name                = local.keyvault-name
}

data "azurerm_key_vault_secret" "open-api-key" {
  key_vault_id = data.azurerm_key_vault.keyvault.id
  name         = "openai-api-key"
}

data "azurerm_key_vault_secret" "twitter-consumer-key" {
  key_vault_id = data.azurerm_key_vault.keyvault.id
  name         = "twitter-consumer-key"
}

data "azurerm_key_vault_secret" "twitter-consumer-secret" {
  key_vault_id = data.azurerm_key_vault.keyvault.id
  name         = "twitter-consumer-secret"
}

data "azurerm_key_vault_secret" "twitter-token" {
  key_vault_id = data.azurerm_key_vault.keyvault.id
  name         = "twitter-token"
}

data "azurerm_key_vault_secret" "twitter-token-secret" {
  key_vault_id = data.azurerm_key_vault.keyvault.id
  name         = "twitter-token-secret"
}
#### Archiving function source code to deploy on azure #################################################################
data "archive_file" "function_archive" {

  type        = "zip"
  source_dir  = "../"
  excludes    = ["venv", "deployment", ".gitignore", "Makefile", ".idea", ".git", "__pycache__", ".env"]
  output_path = "${path.module}/files/${local.timestamp_string}.zip"

}

resource "azurerm_storage_account" "checkpoint-storage" {
  tags                     = { "Project" : var.project-name, "Location" : data.azurerm_resource_group.rg.location }
  account_replication_type = "LRS"
  account_tier             = "Standard"
  location                 = data.azurerm_resource_group.rg.location
  name                     = lower(join("", [var.project-name, "cpst", var.resource-group-name]))
  resource_group_name      = var.resource-group-name
}

resource "azurerm_storage_container" "stories-container" {
  name                 = "stories"
  storage_account_name = azurerm_storage_account.checkpoint-storage.name
}

resource "azurerm_role_assignment" "storage_account_access" {
  scope                = azurerm_storage_account.checkpoint-storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.function.identity[0].principal_id
}

resource "azurerm_application_insights" "function-insights" {
  tags                = { "Project" : var.project-name, "Location" : data.azurerm_resource_group.rg.location }
  application_type    = "web"
  location            = data.azurerm_resource_group.rg.location
  name                = lower(join("",[var.project-name,"-fn-in-",var.resource-group-name]))
  resource_group_name = var.resource-group-name
}

resource "azurerm_storage_account" "function-storage" {
  tags                     = { "Project" : var.project-name, "Location" : data.azurerm_resource_group.rg.location }
  account_replication_type = "LRS"
  account_tier             = "Standard"
  location                 = data.azurerm_resource_group.rg.location
  name                     = lower(join("", [var.project-name, "fnst", var.resource-group-name]))
  resource_group_name      = var.resource-group-name
}

resource "azurerm_service_plan" "function-plan" {
  tags                = { "Project" : var.project-name, "Location" : data.azurerm_resource_group.rg.location }
  location            = data.azurerm_resource_group.rg.location
  name                = lower(join("", [var.project-name, "-fn-pl-", var.resource-group-name]))
  os_type             = "Linux"
  resource_group_name = var.resource-group-name
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "function" {
  tags                = { "Project" : var.project-name, "Location" : data.azurerm_resource_group.rg.location }
  location            = data.azurerm_resource_group.rg.location
  name                = lower(join("", [var.project-name, "-fn-", var.resource-group-name]))
  resource_group_name = var.resource-group-name

  service_plan_id            = azurerm_service_plan.function-plan.id
  storage_account_name       = azurerm_storage_account.function-storage.name
  storage_account_access_key = azurerm_storage_account.function-storage.primary_access_key

  zip_deploy_file = data.archive_file.function_archive.output_path

  identity {
    type = "SystemAssigned"
  }

  functions_extension_version = "~4"
  site_config {
    application_stack {
      python_version = "3.10"
    }
    application_insights_connection_string = azurerm_application_insights.function-insights.connection_string
    application_insights_key = azurerm_application_insights.function-insights.instrumentation_key
  }
  app_settings = {
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = true
    "PYTHON_ISOLATE_WORKER_DEPENDENCIES" : 1
    "AZURE_OPENAI_KEY" : data.azurerm_key_vault_secret.open-api-key.value
    "TWITTER_CONSUMER_KEY" : data.azurerm_key_vault_secret.twitter-consumer-key.value
    "TWITTER_CONSUMER_SECRET" : data.azurerm_key_vault_secret.twitter-consumer-secret.value
    "TWITTER_TOKEN" : data.azurerm_key_vault_secret.twitter-token.value
    "TWITTER_TOKEN_SECRET" : data.azurerm_key_vault_secret.twitter-token-secret.value
    "AZURE_ACCOUNT_URL" : azurerm_storage_account.checkpoint-storage.primary_blob_endpoint
    "AZURE_CONTAINER_NAME" : azurerm_storage_container.stories-container.name
  }
}