# Live AWS Production Application

🌐 **Public AWS App Runner URL**: **[https://bwjbnvzhui.us-east-1.awsapprunner.com](https://bwjbnvzhui.us-east-1.awsapprunner.com)**
🗄️ **AWS Neptune Endpoint**: `https://columbia-library-neptune.cluster-ckj0wuc0o6zy.us-east-1.neptune.amazonaws.com:8182`
🔄 **Auto-Deployments**: Enabled (Every `git push` to `main` automatically deploys live to AWS).

---

# Step-by-Step AWS Deployment Guide

This guide details how to deploy the **Columbia Library Data Graph** application and Knowledge Graph onto AWS using **AWS Neptune**, **Amazon ECR**, and **AWS ECS Fargate**.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |         Route 53 / Web Browser        |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     Application Load Balancer (ALB)   |
                      +---------------------------------------+
                                          |
                                          v
  +----------------------------------------------------------------------------------+
  |                           AWS ECS FARGATE SERVICE                                |
  |                                                                                  |
  |  +----------------------------------------------------------------------------+  |
  |  | Docker Container: ColumbiaLibraryDataGraph (Flask + BAAI/bge-small-en-v1.5)  |  |
  |  +----------------------------------------------------------------------------+  |
  +----------------------------------------------------------------------------------+
                                          |
                                          v OpenCypher HTTPS Queries (Port 8182)
  +----------------------------------------------------------------------------------+
  |                                AWS NEPTUNE DB                                    |
  |                                                                                  |
  |  - Property Graph (Datasets, Libguides, Platforms, Specialists, Edges)           |
  |  - OpenCypher Engine                                                             |
  +----------------------------------------------------------------------------------+
```

---

## Phase 1: Provision AWS Neptune Graph Database

1. **Open AWS Console** -> Go to **Amazon Neptune** -> **Create Database**.
2. Settings:
   - **Database Name**: `columbia-library-neptune`
   - **Engine Version**: `>= 1.2.0.0` (OpenCypher enabled)
   - **DB Instance Class**: `db.t3.medium` (or `db.r5.large` for production)
   - **VPC**: Select your default VPC and enable IAM Database Authentication.
3. Once provisioned, copy the **Neptune Endpoint URL**:
   `https://columbia-library-neptune.cluster-ckj0wuc0o6zy.us-east-1.neptune.amazonaws.com:8182`

---

## Phase 2: Bulk Load OpenCypher Data to Neptune

1. **Create Amazon S3 Bucket**:
   ```bash
   aws s3 mb s3://columbia-library-graph-data
   ```
2. **Upload OpenCypher CSV Files**:
   ```bash
   aws s3 cp data/opencypher/ s3://columbia-library-graph-data/opencypher/ --recursive
   ```
3. **Execute Neptune Bulk Loader**:
   ```bash
   curl -X POST https://columbia-library-neptune.cluster-ckj0wuc0o6zy.us-east-1.neptune.amazonaws.com:8182/loader \
     -H 'Content-Type: application/json' \
     -d '{
           "source" : "s3://columbia-library-graph-data/opencypher/",
           "format" : "opencypher",
           "iamRoleArn" : "arn:aws:iam::YOUR_ACCOUNT_ID:role/NeptuneS3ReadRole",
           "region" : "us-east-1",
           "failOnError" : "TRUE",
           "parallelism" : "MEDIUM"
         }'
   ```

---

## Phase 3: Push Docker Image to Amazon ECR

1. **Create ECR Repository**:
   ```bash
   aws ecr create-repository --repository-name columbia-library-datagraph
   ```
2. **Authenticate Docker to ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   ```
3. **Build & Tag Docker Image**:
   ```bash
   docker build -t columbia-library-datagraph .
   docker tag columbia-library-datagraph:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/columbia-library-datagraph:latest
   ```
4. **Push Image to ECR**:
   ```bash
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/columbia-library-datagraph:latest
   ```

---

## Phase 4: Deploy Container to AWS ECS Fargate

1. **Create ECS Task Definition**:
   - Go to **Amazon ECS** -> **Task Definitions** -> **Create new Task Definition**.
   - **Launch Type**: `Fargate`
   - **CPU / Memory**: `1 vCPU / 2 GB RAM`
   - **Container Image**: `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/columbia-library-datagraph:latest`
   - **Port Mappings**: Port `5000`
   - **Environment Variables**:
     - `NEPTUNE_ENDPOINT` = `https://YOUR-NEPTUNE-ENDPOINT:8182`
     - `REDIVIS_API_TOKEN` = `your_redivis_token_here`

2. **Run ECS Service**:
   - Create an ECS Cluster `columbia-library-cluster`.
   - Launch Service using Fargate with an **Application Load Balancer (ALB)**.
   - Access the live web application on your ALB DNS URL!
