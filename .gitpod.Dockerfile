# copy from https://github.com/microsoft/vscode-dev-containers/blob/master/containers/typescript-node/.devcontainer/Dockerfile

FROM gitpod/workspace-full

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# Install the Azure CLI and Toolkit
RUN brew update && brew install azure-cli \
    && brew tap azure/functions \
    && brew install azure-functions-core-tools@3 \
    && brew link --overwrite azure-functions-core-tools@3