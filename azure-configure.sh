#!/bin/bash

# Azure App Service Configuration Script
# This script helps configure the Azure App Service with the correct settings

echo "Azure App Service Configuration Helper"
echo "======================================"
echo ""
echo "This script will help you configure your Azure App Service."
echo "Run this locally with Azure CLI installed and logged in."
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "ERROR: Azure CLI is not installed. Please install it first."
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Variables
RESOURCE_GROUP="your-resource-group"
APP_NAME="app-zela-prod"
STARTUP_COMMAND="cd /tmp/8ddfae* && . antenv/bin/activate && cd Zela && gunicorn --bind 0.0.0.0:8000 Zela.wsgi:application"

echo "Please enter your Azure configuration:"
read -p "Resource Group name (default: $RESOURCE_GROUP): " input_rg
RESOURCE_GROUP=${input_rg:-$RESOURCE_GROUP}

read -p "App Service name (default: $APP_NAME): " input_app
APP_NAME=${input_app:-$APP_NAME}

echo ""
echo "Configuring App Service: $APP_NAME in Resource Group: $RESOURCE_GROUP"
echo ""

# Function to set app settings
set_app_settings() {
    echo "Setting application settings..."
    
    # Note: Replace these with your actual values
    az webapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_NAME" \
        --settings \
        DJANGO_SETTINGS_MODULE="Zela.settings.production" \
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
        WEBSITE_HTTPLOGGING_RETENTION_DAYS="7" \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" \
        PYTHON_VERSION="3.11"
    
    echo "Application settings configured."
}

# Function to set startup command
set_startup_command() {
    echo "Setting startup command..."
    
    az webapp config set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_NAME" \
        --startup-file "$STARTUP_COMMAND"
    
    echo "Startup command configured."
}

# Function to enable logging
enable_logging() {
    echo "Enabling application logging..."
    
    az webapp log config \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_NAME" \
        --application-logging filesystem \
        --level information \
        --web-server-logging filesystem \
        --docker-container-logging filesystem
    
    echo "Logging enabled."
}

# Function to show current configuration
show_configuration() {
    echo "Current App Service Configuration:"
    echo "=================================="
    
    echo ""
    echo "App Settings:"
    az webapp config appsettings list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_NAME" \
        --output table
    
    echo ""
    echo "General Settings:"
    az webapp config show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_NAME" \
        --output table
}

# Main menu
while true; do
    echo ""
    echo "Select an option:"
    echo "1. Set application settings"
    echo "2. Set startup command"
    echo "3. Enable logging"
    echo "4. Show current configuration"
    echo "5. Apply all recommended settings"
    echo "6. Exit"
    echo ""
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            set_app_settings
            ;;
        2)
            set_startup_command
            ;;
        3)
            enable_logging
            ;;
        4)
            show_configuration
            ;;
        5)
            set_app_settings
            set_startup_command
            enable_logging
            echo ""
            echo "All recommended settings applied!"
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
done