# copy from https://github.com/microsoft/vscode-dev-containers/blob/master/containers/typescript-node/.devcontainer/Dockerfile

FROM gitpod/workspace-full

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# Install the Azure CLI and Toolkit
#RUN brew update && brew install azure-cli \
#    && brew tap azure/functions \
#    && brew install azure-functions-core-tools@3 \
#    && brew link --overwrite azure-functions-core-tools@3

RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg \
    && sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list' \
    && sudo apt-get update \
    && sudo apt-get update \
    && sudo apt-get install azure-functions-core-tools-3