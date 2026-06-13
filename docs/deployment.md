# Deployment Guide

## Single Machine Setup

Perfect for development and small-scale usage.

```bash
# Start system
direktor tracker &
direktor workers &

# Submit job
direktor submit article.txt --watch
```

## Multi-Machine Setup

Scale across multiple servers for production workloads.

### Coordinator Node

Runs job tracking and coordination:

```bash
# Set network binding
export NNG_DISTRIBUTOR_ADDRESS=tcp://0.0.0.0
export NNG_TRACKER_ADDRESS=tcp://0.0.0.0:5560

# Start services
direktor tracker &

# Submit jobs
direktor submit batch/*.txt
```

### Worker Nodes

Connect to coordinator and process jobs:

```bash
# Point to coordinator
export NNG_DISTRIBUTOR_ADDRESS=tcp://coordinator.local
export NNG_TRACKER_ADDRESS=tcp://coordinator.local:5560

# Run CPU workers
direktor worker script &
direktor worker audio &
direktor worker transcript &
direktor worker prompts &
```

### GPU Nodes

Dedicated machines for GPU-intensive work:

```bash
# Point to coordinator
export NNG_DISTRIBUTOR_ADDRESS=tcp://coordinator.local
export NNG_TRACKER_ADDRESS=tcp://coordinator.local:5560

# Run GPU workers
direktor worker images &
direktor worker video &
```

## Docker Deployment

### Single Container

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN pip install .

EXPOSE 5550-5560

CMD ["direktor", "tracker"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  tracker:
    build: .
    command: direktor tracker
    environment:
      - NNG_DISTRIBUTOR_ADDRESS=tcp://0.0.0.0
      - NNG_TRACKER_ADDRESS=tcp://0.0.0.0:5560
    ports:
      - "5550-5560:5550-5560"
    env_file:
      - .env

  cpu-worker:
    build: .
    command: direktor worker script
    environment:
      - NNG_DISTRIBUTOR_ADDRESS=tcp://tracker
      - NNG_TRACKER_ADDRESS=tcp://tracker:5560
    depends_on:
      - tracker
    env_file:
      - .env
    deploy:
      replicas: 3

  gpu-worker:
    build: .
    command: direktor worker images
    environment:
      - NNG_DISTRIBUTOR_ADDRESS=tcp://tracker
      - NNG_TRACKER_ADDRESS=tcp://tracker:5560
    depends_on:
      - tracker
    env_file:
      - .env
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: direktor-tracker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: direktor-tracker
  template:
    metadata:
      labels:
        app: direktor-tracker
    spec:
      containers:
      - name: tracker
        image: direktor:latest
        command: ["direktor", "tracker"]
        env:
        - name: NNG_DISTRIBUTOR_ADDRESS
          value: "tcp://0.0.0.0"
        - name: NNG_TRACKER_ADDRESS
          value: "tcp://0.0.0.0:5560"
        ports:
        - containerPort: 5560
        envFrom:
        - secretRef:
            name: direktor-secrets

---
apiVersion: v1
kind: Service
metadata:
  name: direktor-tracker
spec:
  selector:
    app: direktor-tracker
  ports:
  - port: 5560
    targetPort: 5560
  - port: 5550
    targetPort: 5550

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: direktor-workers
spec:
  replicas: 5
  selector:
    matchLabels:
      app: direktor-workers
  template:
    metadata:
      labels:
        app: direktor-workers
    spec:
      containers:
      - name: worker
        image: direktor:latest
        command: ["direktor", "worker", "script"]
        env:
        - name: NNG_DISTRIBUTOR_ADDRESS
          value: "tcp://direktor-tracker"
        - name: NNG_TRACKER_ADDRESS
          value: "tcp://direktor-tracker:5560"
        envFrom:
        - secretRef:
            name: direktor-secrets
```

### GPU Node Pool

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: direktor-gpu-workers
spec:
  replicas: 2
  selector:
    matchLabels:
      app: direktor-gpu-workers
  template:
    metadata:
      labels:
        app: direktor-gpu-workers
    spec:
      nodeSelector:
        accelerator: nvidia-tesla-k80
      containers:
      - name: gpu-worker
        image: direktor:latest
        command: ["direktor", "worker", "images"]
        env:
        - name: NNG_DISTRIBUTOR_ADDRESS
          value: "tcp://direktor-tracker"
        - name: NNG_TRACKER_ADDRESS
          value: "tcp://direktor-tracker:5560"
        resources:
          limits:
            nvidia.com/gpu: 1
        envFrom:
        - secretRef:
            name: direktor-secrets
```

## Cloud Provider Examples

### AWS ECS

```json
{
  "family": "direktor-tracker",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "tracker",
      "image": "direktor:latest",
      "command": ["direktor", "tracker"],
      "portMappings": [
        {
          "containerPort": 5560,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NNG_DISTRIBUTOR_ADDRESS",
          "value": "tcp://0.0.0.0"
        },
        {
          "name": "NNG_TRACKER_ADDRESS",
          "value": "tcp://0.0.0.0:5560"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:direktor-openai-key"
        }
      ]
    }
  ]
}
```

### Google Cloud Run

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: direktor-tracker
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containers:
      - image: gcr.io/project/direktor:latest
        command: ["direktor", "tracker"]
        env:
        - name: NNG_DISTRIBUTOR_ADDRESS
          value: "tcp://0.0.0.0"
        - name: NNG_TRACKER_ADDRESS
          value: "tcp://0.0.0.0:5560"
        ports:
        - containerPort: 5560
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
```

## Configuration Management

### Environment Variables

```bash
# Network Configuration
export NNG_DISTRIBUTOR_ADDRESS=tcp://coordinator.local
export NNG_TRACKER_ADDRESS=tcp://coordinator.local:5560

# Processing Configuration
export TEMP_DIR_BASE=/tmp/direktor
export LOG_LEVEL=INFO

# API Configuration
export OPENAI_API_KEY=sk-...
export REPLICATE_API_TOKEN=r8_...
```

### Secrets Management

**Docker Secrets:**
```bash
echo "sk-your-openai-key" | docker secret create openai_api_key -
echo "r8_your-replicate-token" | docker secret create replicate_token -
```

**Kubernetes Secrets:**
```bash
kubectl create secret generic direktor-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key \
  --from-literal=REPLICATE_API_TOKEN=r8_your-token
```

## Monitoring

### Health Checks

```bash
# Check tracker health
curl -f http://tracker:5560/health || exit 1

# Check worker connectivity
direktor stats | grep -q "pending\|in_progress" || exit 1
```

### Logging

```bash
# Centralized logging
direktor tracker 2>&1 | tee -a /var/log/direktor/tracker.log
direktor worker script 2>&1 | tee -a /var/log/direktor/script-worker.log
```

### Metrics

```bash
# Queue statistics
direktor stats | grep -E "(pending|in_progress|completed|failed)"

# Job throughput
watch -n 5 "direktor stats | grep completed"
```

## Scaling Guidelines

### Worker Scaling

| Stage | Resource | Workers per Core | Notes |
|-------|----------|------------------|--------|
| script | CPU | 1-2 | API rate limited |
| audio | CPU | 2-4 | Moderate compute |
| transcript | Network | 1 | API limited |
| prompts | CPU | 1-2 | API rate limited |
| images | GPU | 1 per GPU | GPU memory bound |
| video | CPU+GPU | 1 per GPU | Memory intensive |

### Resource Requirements

**Minimum (Development):**
- 2 CPU cores
- 4GB RAM
- 10GB disk space

**Production (Medium Scale):**
- 8 CPU cores
- 16GB RAM
- 100GB disk space
- 1 GPU (for images/video)

**Enterprise (High Scale):**
- 16+ CPU cores per node
- 32GB+ RAM per node
- 500GB+ shared storage
- 4+ GPUs per GPU node

## Security

### Network Security

```bash
# Firewall rules (UFW example)
sudo ufw allow from 10.0.0.0/8 to any port 5550:5560
sudo ufw deny 5550:5560
```

### Secret Rotation

```bash
# Update API keys
kubectl patch secret direktor-secrets -p='{"data":{"OPENAI_API_KEY":"'$(echo -n "new-key" | base64)'"}}'

# Restart workers to pick up new keys
kubectl rollout restart deployment/direktor-workers
```

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
netstat -tulpn | grep 555
# Change base port if needed
export NNG_DISTRIBUTOR_ADDRESS=tcp://127.0.0.1:6000
```

**Worker connectivity:**
```bash
# Test network connectivity
telnet coordinator.local 5560
# Check firewall rules
```

**Job failures:**
```bash
# Check specific job
direktor status job_12345

# View failed jobs
direktor stats | grep failed
```

**Resource exhaustion:**
```bash
# Monitor resources
htop
df -h /tmp

# Clean up temp files
rm -rf /tmp/direktor/*
```