# AWS Deployment Notes

This describes how the containerized app (the `Dockerfile` at the repo
root) maps onto an AWS deployment using ECS, RDS, and ElastiCache. This
isn't automated with Terraform/CDK in this repo, but documents the
target architecture referenced in the README and resume bullet
("deployed on AWS ECS with RDS PostgreSQL and auto-scaling").

## Components

| AWS Service | Purpose |
|---|---|
| **ECR** | Stores the Docker image built from the root `Dockerfile`. |
| **ECS (Fargate)** | Runs the Django/Daphne container as a service, with a task definition exposing port 8000. |
| **Application Load Balancer (ALB)** | Routes HTTPS traffic to the ECS service's target group; health check on `/api/schema/`. |
| **RDS (PostgreSQL)** | Managed Postgres instance; connection details passed to the container via `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` environment variables (ideally sourced from AWS Secrets Manager). |
| **ElastiCache (Redis)** | Backs the Channels layer (`CHANNEL_LAYER_BACKEND=redis`, `REDIS_HOST=<elasticache-endpoint>`) for real-time notification delivery across multiple ECS tasks. |
| **Application Auto Scaling** | Scales the ECS service's desired task count based on ALB request count per target / CPU utilization. |

## Environment variables for the ECS task definition

```
DJANGO_SECRET_KEY=<from Secrets Manager>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-domain>
DB_ENGINE=postgresql
DB_NAME=aiops_db
DB_USER=<from Secrets Manager>
DB_PASSWORD=<from Secrets Manager>
DB_HOST=<rds-endpoint>
DB_PORT=5432
CHANNEL_LAYER_BACKEND=redis
REDIS_HOST=<elasticache-endpoint>
REDIS_PORT=6379
```

## Deploy flow

1. CI (`.github/workflows/ci.yml`) runs lint + tests on every push to
   `main`.
2. Build and push the image:
   ```bash
   docker build -t <account-id>.dkr.ecr.<region>.amazonaws.com/aiops-incident-manager:latest .
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/aiops-incident-manager:latest
   ```
3. Update the ECS service (e.g. `aws ecs update-service --cluster aiops --service aiops-web --force-new-deployment`) so it pulls the new image.
4. The container's `CMD` runs `python manage.py migrate --noinput` on
   startup before starting `daphne`, so schema migrations are applied
   automatically on each deploy. For zero-downtime deploys with
   multiple tasks, run migrations as a separate one-off ECS task
   *before* rolling the service, rather than relying on every task to
   migrate independently.

## Auto-scaling policy (example)

- Target tracking on **ALBRequestCountPerTarget**, target value ~50
  requests/task.
- Min tasks: 2 (for availability), Max tasks: 10.
- Scale-out cooldown: 60s, scale-in cooldown: 300s (avoid flapping).
