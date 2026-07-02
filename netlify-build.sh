#!/usr/bin/env bash
set -euo pipefail
# Install the latest Quarto release, then render the site to _site/.
QVER=$(curl -s https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest \
        | grep -oP '"tag_name":\s*"v\K[^"]+')
echo "Installing Quarto $QVER"
curl -sL "https://github.com/quarto-dev/quarto-cli/releases/download/v${QVER}/quarto-${QVER}-linux-amd64.tar.gz" \
  | tar -xz
export PATH="$PWD/quarto-${QVER}/bin:$PATH"
quarto render
