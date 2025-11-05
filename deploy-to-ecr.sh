#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "📋 Loading configuration from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Configuration
AWS_REGION="${AWS_REGION:-ap-south-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
REPOSITORY_NAME="grade-manager"
IMAGE_NAME="grade-manager"
IMAGE_TAG="latest"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if account ID is set, try to get it from AWS CLI
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠️  AWS_ACCOUNT_ID not set in .env, trying to detect from AWS CLI...${NC}"
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    
    if [ -z "$AWS_ACCOUNT_ID" ] || [ "$AWS_ACCOUNT_ID" == "None" ]; then
        echo -e "${RED}❌ Error: Could not detect AWS_ACCOUNT_ID!${NC}"
        echo "Please set AWS_ACCOUNT_ID in one of these ways:"
        echo ""
        echo "Option 1: Add to .env file: AWS_ACCOUNT_ID=your-account-id"
        echo "Option 2: Export as environment variable: export AWS_ACCOUNT_ID=your-account-id"
        echo "Option 3: Make sure AWS CLI is configured: aws configure"
        exit 1
    else
        echo -e "${GREEN}✅ Detected AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
    fi
else
    echo -e "${GREEN}✅ Using AWS Account ID from .env: ${AWS_ACCOUNT_ID}${NC}"
fi

# Full repository URI
ECR_REPOSITORY_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}"

echo -e "${GREEN}🚀 Starting Docker build and push to ECR...${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI is not installed!${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed!${NC}"
    echo "Install it from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Step 1: Authenticate Docker to ECR
echo -e "${YELLOW}📝 Step 1: Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY_URI}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Authentication failed!${NC}"
    echo "Please check your AWS credentials: aws configure"
    exit 1
fi
echo -e "${GREEN}✅ Authenticated successfully${NC}"
echo ""

# Step 2: Check if repository exists, create if not
echo -e "${YELLOW}📋 Step 2: Checking ECR repository...${NC}"
aws ecr describe-repositories --repository-names ${REPOSITORY_NAME} --region ${AWS_REGION} &> /dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Repository not found. Creating...${NC}"
    aws ecr create-repository \
        --repository-name ${REPOSITORY_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Repository created successfully${NC}"
    else
        echo -e "${RED}❌ Failed to create repository${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Repository exists${NC}"
fi
echo ""

# Step 3: Build Docker image for AMD64/x86_64 architecture
echo -e "${YELLOW}🔨 Step 3: Building Docker image for AMD64/x86_64...${NC}"
echo -e "${YELLOW}   (Building for EC2-compatible architecture)${NC}"

# Build with platform specification for AMD64/x86_64
BUILD_SUCCESS=false

# Try buildx first (more reliable for cross-platform builds)
if docker buildx version &> /dev/null; then
    echo -e "${YELLOW}   Using Docker buildx...${NC}"
    docker buildx build \
        --platform linux/amd64 \
        --tag ${IMAGE_NAME}:${IMAGE_TAG} \
        --load \
        . && BUILD_SUCCESS=true
    
    if [ "$BUILD_SUCCESS" = false ]; then
        echo -e "${YELLOW}   Buildx build failed, trying regular build...${NC}"
        BUILD_SUCCESS=false
    fi
fi

# Fallback to regular docker build with platform flag
if [ "$BUILD_SUCCESS" = false ]; then
    echo -e "${YELLOW}   Using Docker build with platform flag...${NC}"
    docker build --platform linux/amd64 -t ${IMAGE_NAME}:${IMAGE_TAG} .
    
    if [ $? -eq 0 ]; then
        BUILD_SUCCESS=true
    fi
fi

if [ "$BUILD_SUCCESS" = false ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    echo ""
    echo "If you're on Apple Silicon Mac, try:"
    echo "  1. Install/update Docker Desktop"
    echo "  2. Enable 'Use Rosetta for x86/amd64 emulation' in Docker Desktop settings"
    echo "  3. Or build on EC2 instead (recommended)"
    exit 1
fi
echo -e "${GREEN}✅ Image built successfully${NC}"
echo ""

# Step 4: Tag image for ECR
echo -e "${YELLOW}🏷️  Step 4: Tagging image...${NC}"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY_URI}:${IMAGE_TAG}
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY_URI}:latest
echo -e "${GREEN}✅ Image tagged${NC}"
echo ""

# Step 5: Push to ECR
echo -e "${YELLOW}📤 Step 5: Pushing image to ECR...${NC}"
docker push ${ECR_REPOSITORY_URI}:${IMAGE_TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Push failed!${NC}"
    exit 1
fi

docker push ${ECR_REPOSITORY_URI}:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Push failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Successfully pushed to ECR!${NC}"
echo ""
echo -e "${GREEN}📍 Repository URI: ${ECR_REPOSITORY_URI}${NC}"
echo ""
echo -e "${YELLOW}📦 To pull this image:${NC}"
echo "   docker pull ${ECR_REPOSITORY_URI}:latest"
echo ""
echo -e "${YELLOW}🚀 To run locally:${NC}"
echo "   docker run -d -p 8000:8000 \\"
echo "     -e DB_HOST=your-rds-endpoint \\"
echo "     -e DB_PORT=3306 \\"
echo "     -e DB_USER=admin \\"
echo "     -e DB_PASSWORD=your-password \\"
echo "     -e DB_NAME=cloud1 \\"
echo "     ${ECR_REPOSITORY_URI}:latest"

