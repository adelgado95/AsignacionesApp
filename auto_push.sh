#!/bin/bash

# Start SSH agent
eval "$(ssh-agent -s)"

# Add your private key
ssh-add ~/.ssh/id_rsa.pub

# Navigate to the repo
cd /home/ubuntu/AsignacionesApp || exit

# Ensure correct git identity
git config user.name "Alfonso delgado"
git config user.email "ajdfdelgado@gmail.com"

# Add, commit, and push
git add -A
git commit -m "update repo" || echo "Nothing to commit"
git push origin main

