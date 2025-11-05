#!/usr/bin/env bash
set -euo pipefail

# Setup script for Amazon Linux EC2 instance
# Installs Docker, AWS CLI, Git and prepares the instance for pulling/running ECR images
# Usage: sudo ./setup-ec2-amazon-linux.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  SUDO="sudo"
else
  SUDO=""
fi

echo -e "${GREEN}Starting Amazon Linux EC2 setup...${NC}"

# Detect OS
OS_ID="unknown"
OS_VERSION=""
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS_ID=${ID:-$OS_ID}
  OS_VERSION=${VERSION_ID:-$OS_VERSION}
  echo -e "${GREEN}Detected: ${OS_ID} ${OS_VERSION}${NC}"
fi

echo -e "${YELLOW}Updating system packages...${NC}"
$SUDO yum update -y

echo -e "${YELLOW}Installing common tools (unzip, jq)...${NC}"
$SUDO yum install -y unzip jq || true

echo -e "${YELLOW}Installing Docker (if missing)...${NC}"
if command -v docker &> /dev/null; then
  echo -e "${GREEN}Docker already installed: $(docker --version)${NC}"
else
  $SUDO yum install -y docker
  echo -e "${GREEN}Docker installed${NC}"
fi

echo -e "${YELLOW}Enabling and starting Docker service...${NC}"
$SUDO systemctl enable --now docker

# Add current user to docker group
CURRENT_USER=$(whoami)
if id -nG "$CURRENT_USER" | grep -qw docker; then
  echo -e "${GREEN}User $CURRENT_USER already in docker group${NC}"
else
  echo -e "${YELLOW}Adding $CURRENT_USER to docker group (you may need to re-login)...${NC}"
  $SUDO usermod -aG docker "$CURRENT_USER" || true
fi

echo -e "${YELLOW}Installing AWS CLI v2 (if missing)...${NC}"
if command -v aws &> /dev/null; then
  echo -e "${GREEN}AWS CLI already installed: $(aws --version)${NC}"
else
  TMPDIR=$(mktemp -d)
  pushd "$TMPDIR" >/dev/null
  curl -sS "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
  unzip -q awscliv2.zip
  $SUDO ./aws/install --update || $SUDO ./aws/install
  popd >/dev/null
  rm -rf "$TMPDIR"
  echo -e "${GREEN}AWS CLI installed${NC}"
fi

echo -e "${YELLOW}Installing Git (if missing)...${NC}"
if command -v git &> /dev/null; then
  echo -e "${GREEN}Git already installed: $(git --version)${NC}"
else
  $SUDO yum install -y git
fi

echo ""
echo -e "${GREEN}Basic setup complete.${NC}"

echo -e "${YELLOW}ECR helper: you can now login and pull images from ECR.${NC}"
cat <<'EOT'
# Example usage (replace /path/to/.env with the actual path to your .env):
# 1) Configure AWS credentials (if not configured):
#    aws configure
#    or export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION in the shell
# 2) Login to ECR:
#    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
# 3) Pull image:
#    docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/grade-manager:latest
# 4) Run image (use absolute path to your .env):
#    docker run -d --name grade-manager --env-file /path/to/.env -p 8050:8050 ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/grade-manager:latest

# Notes:
# - If the RDS instance is private, ensure the EC2 instance has network access (same VPC or VPN).
# - After adding the user to the docker group you may need to log out and back in for permissions to take effect.
EOT

echo ""
echo -e "${GREEN}Done. If you added the user to the docker group, logout/login to apply group membership.${NC}"

exit 0
