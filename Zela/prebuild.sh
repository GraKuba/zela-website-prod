#!/bin/bash

# Azure Oryx prebuild script
echo "Running prebuild script..."

# Disable Oryx compression
export ENABLE_ORYX_BUILD=true
export SCM_DO_BUILD_DURING_DEPLOYMENT=true
export DISABLE_COMPRESS=true

echo "Prebuild configuration complete"