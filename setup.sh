#!/bin/bash

# Get the user's home directory
HOME_DIR=$(eval echo ~${USER})

# Create the .bin directory in the home directory if it doesn't exist
mkdir -p "${HOME_DIR}/.bin"

# Get the current working directory
CURRENT_DIR=$(pwd)

# Ensure batc.py exists in the current directory
if [ ! -f "${CURRENT_DIR}/batc.py" ]; then
    echo "batc.py not found in the current directory."
    exit 1
fi

# Make batc.py executable
chmod +x "${CURRENT_DIR}/batc.py"

# Move batc.py to the .bin directory
mv "${CURRENT_DIR}/batc.py" "${HOME_DIR}/.bin/"

# Add an alias to .bashrc or .zshrc
if [ -f "${HOME_DIR}/.bashrc" ]; then
    echo "alias batc='${HOME_DIR}/.bin/batc.py'" >> "${HOME_DIR}/.bashrc"
    # Source the .bashrc to apply changes
    source "${HOME_DIR}/.bashrc"
elif [ -f "${HOME_DIR}/.zshrc" ]; then
    echo "alias batc='${HOME_DIR}/.bin/batc.py'" >> "${HOME_DIR}/.zshrc"
    # Source the .zshrc to apply changes
    source "${HOME_DIR}/.zshrc"
else
    echo "Neither .bashrc nor .zshrc found. Please create one and add the alias manually."
fi

# Delete the repository directory
cd $CURRENT_DIR

# Delete this setup script
rm -f "${CURRENT_DIR}/setup_batc.sh"

cd ..
REPO_DIR=$(basename "${CURRENT_DIR}")
rm -rf "${REPO_DIR}"
echo "Setup complete and cleanup done. You can now use the 'batc' command."
