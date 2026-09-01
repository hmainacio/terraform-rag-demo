variable "project_name" {
  description = "Nome curto do projeto (usado como prefixo dos recursos)"
  type        = string
  default     = "ragdemo"
}

variable "environment" {
  description = "Ambiente (demo, dev, prod...)"
  type        = string
  default     = "demo"
}

variable "location" {
  description = "Região Azure para o Resource Group e demais recursos"
  type        = string
  default     = "eastus2"
}

variable "openai_location" {
  description = "Região com disponibilidade de Azure OpenAI (pode diferir da region principal)"
  type        = string
  default     = "eastus2"
}
