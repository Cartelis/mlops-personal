# Kubernetes Setup - Week 5

## Clusters

| Environment | Platform | Purpose |
|-------------|----------|---------|
| Dev | Minikube | CPU inference |
| Cloud | GKE Autopilot | CPU inference |
| HPC | University K8s | GPU DDP training |

## Prerequisites

- `kubectl` >= 1.28
- Week 3 Docker images built (`mlops-cpu`, `mlops-gpu`)

### Minikube (local)

```bash
minikube start --cpus=4 --memory=8192
eval $(minikube docker-env)
docker build -f docker/Dockerfile.cpu -t mlops-cpu:v1.2.0 .
# deployment uses imagePullPolicy: IfNotPresent
```

### GKE Autopilot

```bash
gcloud container clusters create-auto mlops-cpu --region=europe-west1
gcloud container clusters get-credentials mlops-cpu --region=europe-west1
# Push image to Artifact Registry (week 4) and update k8s/deployment-cpu.yaml
```

### HPC GPU

```bash
export KUBECONFIG=~/.kube/hpc-config
kubectl get nodes -l accelerator=nvidia
docker build -f docker/Dockerfile.gpu -t mlops-gpu:v1.2.0 .
# Push to HPC registry per local instructions
```

## Deploy CPU inference

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/resourcequota.yaml
kubectl apply -f k8s/deployment-cpu.yaml
kubectl apply -f k8s/service-cpu.yaml

kubectl rollout status deployment/mlops-fraud-api -n mlops
kubectl port-forward svc/mlops-fraud-api 8080:80 -n mlops
curl http://localhost:8080/health
```

## Deploy GPU DDP training (HPC)

```bash
kubectl apply -f k8s/job-training-single-node.yaml
kubectl wait --for=condition=complete job/pytorch-ddp-2gpu -n mlops --timeout=600s
kubectl logs job/pytorch-ddp-2gpu -n mlops | tee docs/ddp-training.log
```

## Cleanup

```bash
kubectl delete namespace mlops
```