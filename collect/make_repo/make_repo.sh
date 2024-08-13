#!/usr/bin/env bash

# Mirror repository to https://github.com/swe-bench
# Usage make_repo.sh {gh organization}/{gh repository}

# Abort on error
set -euo pipefail

REPO_TARGET=$1

# Check if the target repository exists
gh repo view "$REPO_TARGET" > /dev/null || exit 1

# Set the organization and repository names
ORG_NAME=${2:-"METR-SWE-BENCH"}

# Check if the organization exists, and if the user has access to it
gh api orgs/$ORG_NAME > /dev/null || exit 1
if [ $? -eq 0 ]; then
    echo "** Organization $ORG_NAME exists."
else
    echo "Organization $ORG_NAME does not exist."
    exit 1
fi

gh api orgs/$ORG_NAME/memberships/$(gh api user | jq -r .login) --jq '.state' > /dev/null || exit 1
if [ $? -eq 0 ]; then
    echo "** User has access to organization $ORG_NAME."
else
    echo "User does not have access to organization $ORG_NAME."
    exit 1
fi

# Does user have access to create repositories in the organization?
gh api orgs/$ORG_NAME/memberships/$(gh api user | jq -r .login) --jq '.role' | grep 'admin' || exit 1
if [ $? -eq 0 ]; then
    echo "** User has access to create repositories in organization $ORG_NAME."
else
    echo "User does not have access to create repositories in organization $ORG_NAME."
    exit 1
fi

NEW_REPO_NAME="${REPO_TARGET//\//__}"

echo "** Creating mirror repository $ORG_NAME/$NEW_REPO_NAME..."


# Create mirror repository
gh repo create "$ORG_NAME/$NEW_REPO_NAME" --private


# Check if the repository creation was successful
if [ $? -eq 0 ]; then
    echo "** Repository created successfully at $ORG_NAME/$NEW_REPO_NAME."
else
    echo "Failed to create the repository."
    exit 1
fi

# Clone the target repository
echo "** Cloning $REPO_TARGET..."
TARGET_REPO_DIR="${REPO_TARGET##*/}.git"

# Check if the local repository directory already exists
if [ -d "$TARGET_REPO_DIR" ]; then
    echo "The local repository directory $TARGET_REPO_DIR already exists."
    exit 1
fi

git clone --bare git@github.com:$REPO_TARGET.git

# Push files to the mirror repository
echo "** Performing mirror push of files to $ORG_NAME/$NEW_REPO_NAME..."
cd "$TARGET_REPO_DIR"; git push --mirror git@github.com:$ORG_NAME/$NEW_REPO_NAME

# Remove the target repository
cd ..; rm -rf "$TARGET_REPO_DIR"

# Clone the mirror repository
git clone git@github.com:$ORG_NAME/$NEW_REPO_NAME.git

# Delete .github/workflows if it exists
if [ -d "$NEW_REPO_NAME/.github/workflows" ]; then
    # Remove the directory
    rm -rf "$NEW_REPO_NAME/.github/workflows"

    # Commit and push the changes
    cd "$NEW_REPO_NAME";
    git add -A;
    git commit -m "Removed .github/workflows";
    git push;
    cd ..;
else
    echo "$REPO_NAME/.github/workflows does not exist. No action required."
fi

rm -rf "$NEW_REPO_NAME"
