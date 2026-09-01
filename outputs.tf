output "resource_group_name" {
  value = azurerm_resource_group.rag.name
}

output "storage_account_name" {
  value = azurerm_storage_account.docs.name
}

output "search_service_name" {
  value = azurerm_search_service.rag.name
}

output "search_service_endpoint" {
  value = "https://${azurerm_search_service.rag.name}.search.windows.net"
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "openai_chat_deployment" {
  value = azurerm_cognitive_deployment.chat.name
}

output "openai_embedding_deployment" {
  value = azurerm_cognitive_deployment.embedding.name
}

# Dica para a demo: as chaves NÃO ficam em output por segurança.
# Para pegar ao vivo, usar no terminal:
#   az cognitiveservices account keys list --name <openai_name> -g <rg_name>
#   az search admin-key show --service-name <search_name> -g <rg_name>
