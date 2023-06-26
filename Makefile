.PHONY: help

help:
	@echo "Available commands:"
	@echo ""
	@grep -E '^([a-zA-Z_-]+):.*## (.+)' $(MAKEFILE_LIST) | awk -F '## ' '{printf "%-20s %s\n", $$1, $$2}'

init: ## Init terraform with resource_group_name= and storage_account_name=
	@cd ./deployment && \
		terraform init -backend-config="resource_group_name=$(resource_group_name)" -backend-config="storage_account_name=$(storage_account_name)"

deploy: ## Deploy terraform with resource_group_name= and storage_account_name=
	@$(MAKE) init resource_group_name=$(resource_group_name) storage_account_name=$(storage_account_name)
	@cd ./deployment && \
		terraform apply -var="resource-group-name=$(resource_group_name)" -auto-approve

validate: ## Validate terraform resource_group_name= and storage_account_name=
	@$(MAKE) init resource_group_name=$(resource_group_name) storage_account_name=$(storage_account_name)
	@cd ./deployment && \
		terraform validate

plan: ## Plan terraform with resource_group_name= and storage_account_name=
	@$(MAKE) init resource_group_name=$(resource_group_name) storage_account_name=$(storage_account_name)
	@cd ./deployment && \
		terraform plan -var="resource-group-name=$(resource_group_name)"


#### Commands with predefined input ##################################################################################

init-experiments: ## Init terraform with Experiments resource group
	@cd ./deployment && \
		terraform init -backend-config="resource_group_name=Experiments" -backend-config="storage_account_name=tfstateexperiments"

deploy-experiments: ## Deploy terraform with Experiments resource group
	@$(MAKE) init-experiments
	@cd ./deployment && \
	    terraform apply -var="resource-group-name=Experiments" -auto-approve

validate-experiments: ## Validate terraform with Experiments resource group
	@$(MAKE) init-experiments
	@cd ./deployment && \
	    terraform validate

plan-experiments: ## Plan terraform with Experiments resource group
	@$(MAKE) init-experiments
	@cd ./deployment && \
	    terraform plan -var="resource-group-name=Experiments"
