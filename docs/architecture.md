# Direktor NNG Architecture

## Overview

Direktor now uses NNG (nanomsg-next-generation) for distributed processing, providing a modern, efficient, and serverless queue system that doesn't require external dependencies like Redis.

## Why NNG?

- **Zero Configuration**: No need to install or manage a separate queue server
- **High Performance**: Low-latency, high-throughput messaging
- **Scalability**: Built-in patterns for distributed computing (PUSH/PULL, REQ/REP)
- **Reliability**: Automatic reconnection and fault tolerance
- **Simple Deployment**: Single binary deployment without external services

## Architecture Components

### 1. NNG Distributor (PUSH/PULL Pattern)

**Purpose**: Distributes jobs across workers for each processing stage.

```
[Producer] --PUSH--> [Queue] --PULL--> [Worker1]
                             --PULL--> [Worker2]
                             --PULL--> [WorkerN]
```

**Addresses**:
- Script: `tcp://127.0.0.1:5550`
- Audio: `tcp://127.0.0.1:5551`
- Transcript: `tcp://127.0.0.1:5552`
- Prompts: `tcp://127.0.0.1:5553`
- Images: `tcp://127.0.0.1:5554`
- Video: `tcp://127.0.0.1:5555`

### 2. NNG Job Tracker (REQ/REP Pattern)

**Purpose**: Central job status tracking and management.

```
[Client] --REQ--> [Tracker] --REP--> [Client]
```

**Address**: `tcp://127.0.0.1:5560`

**Operations**:
- Create job
- Update job status
- Get job status
- List jobs
- Get statistics

## Usage Patterns

### 1. Local Development

Run everything on a single machine:

```bash
# Terminal 1: Start job tracker
direktor tracker

# Terminal 2: Start all workers
direktor workers

# Terminal 3: Submit jobs
direktor submit input.txt --watch
```

### 2. Distributed Processing

Scale across multiple machines:

```bash
# Machine 1 (Coordinator): Run tracker and submit jobs
direktor tracker &
direktor submit input.txt

# Machine 2: Run script workers
direktor worker script

# Machine 3: Run GPU-intensive workers
direktor worker images
direktor worker video

# Machine 4: Run other workers
direktor worker audio
direktor worker transcript
direktor worker prompts
```

### 3. Cloud/Container Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  tracker:
    image: direktor:latest
    command: direktor tracker
    ports:
      - "5560:5560"

  script-worker:
    image: direktor:latest
    command: direktor worker script
    depends_on: [tracker]

  gpu-worker:
    image: direktor:latest
    command: direktor worker images
    depends_on: [tracker]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Configuration

### Environment Variables

```env
# NNG Configuration
NNG_DISTRIBUTOR_ADDRESS=tcp://127.0.0.1  # Base address for job distribution
NNG_TRACKER_ADDRESS=tcp://127.0.0.1:5560  # Job tracker address

# For distributed setups
NNG_DISTRIBUTOR_ADDRESS=tcp://coordinator.local
NNG_TRACKER_ADDRESS=tcp://coordinator.local:5560
```

### Network Topology

```
                    Job Tracker (REQ/REP)
                    tcp://host:5560
                           |
                           |
    ┌─────────────────────────────────────────┐
    │              Coordinator                │
    └─────────────────────────────────────────┘
                           |
                    Job Distribution
                         (PUSH)
                           |
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    v                      v                      v
  Script                 Audio                 Images
  PULL:5550             PULL:5551            PULL:5554
    │                      │                      │
    v                      v                      v
[Worker1]              [Worker1]             [Worker1]
[Worker2]              [Worker2]             [Worker2]
[WorkerN]              [WorkerN]             [WorkerN]
```

## Job Lifecycle

1. **Submission**: Client submits job to tracker and pushes to distribution queue
2. **Processing**: Worker pulls job, updates status to IN_PROGRESS, processes
3. **Completion**: Worker updates status to COMPLETED, optionally chains to next stage
4. **Retry**: Failed jobs automatically retry up to max_retries limit
5. **Tracking**: All status changes logged in tracker for monitoring

## Monitoring and Operations

### CLI Commands

```bash
# Submit job and watch progress
direktor submit article.txt --watch

# Check specific job
direktor status job_12345678

# View queue statistics
direktor stats

# Run complete pipeline
direktor pipeline article.txt --watch
```

### Queue Statistics

```bash
$ direktor stats

📊 Queue Statistics
==================================================

📝 SCRIPT:
   Total jobs: 5
   ⏳ pending: 2
   🔄 in_progress: 1
   ✅ completed: 2

🎵 AUDIO:
   Total jobs: 3
   ⏳ pending: 1
   ✅ completed: 2

🖼️ IMAGES:
   Total jobs: 1
   🔄 in_progress: 1
```

## Fault Tolerance

### Automatic Recovery

- **Connection Loss**: NNG automatically reconnects when network issues resolve
- **Worker Failure**: Jobs timeout and retry automatically
- **Tracker Restart**: Job state persists in memory (can be enhanced with persistence)

### Manual Recovery

```bash
# Check for stuck jobs
direktor stats

# If workers died, restart them
direktor worker script --max-jobs 10

# If tracker died, restart (jobs in progress may be lost)
direktor tracker
```

## Performance Characteristics

### Latency
- **Local**: Sub-millisecond job distribution
- **Network**: Depends on network latency, typically <10ms on LAN

### Throughput
- **Single Worker**: Limited by processing time (minutes per job)
- **Multiple Workers**: Linear scaling up to resource limits
- **Network**: 1000+ jobs/second distribution capacity

### Resource Usage
- **Memory**: Minimal overhead, jobs stored in tracker memory
- **CPU**: Negligible for queue operations
- **Network**: Low bandwidth, only job metadata transferred

## Security Considerations

### Network Security
- Use VPN or private networks for distributed deployments
- Consider TLS encryption for sensitive content (requires custom NNG setup)
- Firewall rules to restrict access to NNG ports (5550-5560)

### Data Security
- Job data includes file contents and API keys in environment
- Ensure secure file permissions on temporary directories
- Use secrets management for API keys in production

## Scaling Guidelines

### Vertical Scaling
- **CPU**: More cores help with parallel processing within stages
- **Memory**: Required for larger files and batch processing
- **GPU**: Essential for image generation and video processing stages

### Horizontal Scaling
- **Script/Prompts**: CPU-bound, scale with general compute
- **Audio**: Moderate compute, can run multiple workers per machine
- **Transcript**: API-limited, fewer workers needed
- **Images**: GPU-bound, scale with GPU availability
- **Video**: CPU+GPU intensive, dedicated machines recommended

### Recommended Deployments

**Small Scale (1-10 jobs/day)**:
- Single machine with all workers
- Local NNG addresses

**Medium Scale (10-100 jobs/day)**:
- Coordinator + 2-3 worker machines
- Dedicated GPU machine for images/video

**Large Scale (100+ jobs/day)**:
- Load-balanced coordinators
- Auto-scaling worker pools
- Dedicated machines per stage type
- Persistent job tracking with database

## Migration from Redis

The NNG implementation maintains the same API surface as the Redis version:

```python
# Same interface works with both implementations
queue_manager = get_queue_manager()
job_id = queue_manager.create_job('script', input_data)
job = queue_manager.get_next_job('script')
queue_manager.complete_job(job_id, output_data, 'audio')
```

Key differences:
- No external Redis server required
- Built-in networking and distribution
- Different addressing scheme (TCP ports vs Redis keys)
- Memory-based job tracking (vs Redis persistence)

## Troubleshooting

### Common Issues

**Port Conflicts**:
```bash
# Check if ports are in use
netstat -tulpn | grep 555

# Use different base address
export NNG_DISTRIBUTOR_ADDRESS=tcp://127.0.0.1:6000
```

**Network Connectivity**:
```bash
# Test basic connectivity
telnet coordinator.local 5560

# Check firewall rules
sudo ufw status
```

**Job Starvation**:
```bash
# Check if workers are running
direktor stats

# Restart stuck workers
pkill -f "direktor worker"
direktor workers
```

**Memory Issues**:
```bash
# Monitor memory usage
htop

# Clear completed jobs (restart tracker)
pkill -f "direktor tracker"
direktor tracker
```

## Future Enhancements

- **Persistence**: Add database backend for job tracking
- **TLS**: Secure communication for production deployments
- **Load Balancing**: Multiple tracker instances with consensus
- **Metrics**: Prometheus/Grafana integration
- **Auto-scaling**: Dynamic worker scaling based on queue depth
- **Web UI**: Browser-based monitoring and job management