# PowerShell Automated AWS ECR & Deployment Script
Param(
    [string]$AWS_REGION = "us-east-1",
    [string]$AWS_ACCOUNT_ID = "YOUR_ACCOUNT_ID",
    [string]$REPO_NAME = "columbia-library-datagraph"
)

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " Columbia Library Data Graph - AWS Deployment Script   " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

$ECR_URL = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "`n[1/4] Building Docker Image..." -ForegroundColor Yellow
docker build -t ${REPO_NAME}:latest .

Write-Host "`n[2/4] Logging in to Amazon ECR ($AWS_REGION)..." -ForegroundColor Yellow
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

Write-Host "`n[3/4] Tagging Docker Image for ECR..." -ForegroundColor Yellow
docker tag ${REPO_NAME}:latest ${ECR_URL}/${REPO_NAME}:latest

Write-Host "`n[4/4] Pushing Container Image to ECR..." -ForegroundColor Yellow
docker push ${ECR_URL}/${REPO_NAME}:latest

Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host " Docker Container Image Successfully Pushed to ECR!    " -ForegroundColor Green
Write-Host " Target ECR Image URI: ${ECR_URL}/${REPO_NAME}:latest  " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
