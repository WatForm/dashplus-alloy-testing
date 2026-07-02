#!/bin/bash

# Create bin directory if it doesn't exist
if [ ! -d "./libs" ]; then
    echo "Creating ./libs directory..."
    mkdir -p ./libs
fi

# Function to download a file if missing
download_if_missing() {
    local file_path=$1
    local url=$2
    local name=$3
    
    if [ ! -f "$file_path" ]; then
        echo "$name not found in ./libs. Downloading..."
        wget -O "$file_path" "$url"
        if [ $? -eq 0 ]; then
            echo "Download complete: $file_path"
            return 0
        else
            echo "Error: Download failed for $name!"
            return 1
        fi
    else
        echo "$name already exists in ./libs"
        return 0
    fi
}

# Download tla2tools.jar
download_if_missing "./libs/tla2tools.jar" \
    "https://github.com/tlaplus/tlaplus/releases/latest/download/tla2tools.jar" \
    "tla2tools.jar"

# Download Apalache jar
# Note: Replace the version number with the latest from https://github.com/apalache-mc/apalache/releases
download_if_missing "./libs/apalache.zip" \
    "https://github.com/apalache-mc/apalache/releases/download/v0.58.2/apalache.zip" \
    "apalache.zip"

rm -rf ./libs/apalache
unzip ./libs/apalache.zip -d ./libs

echo "Setup complete."