# RealidadStore DevOps Platform

[![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.28.15-326CE5?logo=kubernetes&logoColor=white)](#)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind-61DAFB?logo=react&logoColor=black)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](#)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)](#)
[![Monitoring](https://img.shields.io/badge/Monitoring-Prometheus%20%2B%20Grafana-E6522C?logo=prometheus&logoColor=white)](#)
[![Logging](https://img.shields.io/badge/Logging-Loki%20%2B%20Alloy-F2CC0C?logo=grafana&logoColor=black)](#)
[![CI](https://img.shields.io/badge/CI-Tekton-FF6F00)](#)
[![CD](https://img.shields.io/badge/CD-Argo%20CD-EF7B4D?logo=argo&logoColor=white)](#)

**RealidadStore** es un ecommerce de productos de **Realidad Virtual, Realidad Aumentada y Gaming**, construido como una plataforma DevOps completa sobre Kubernetes.

El proyecto integra una aplicación de tres capas, alta disponibilidad básica, almacenamiento persistente NFS, escalamiento horizontal, observabilidad, centralización de logs y un flujo CI/CD con Tekton, Docker Hub, GitHub y Argo CD.

> Repositorio: `https://github.com/AngelUri03/realidadstore-devops`

---

## Arquitectura completa

![Arquitectura completa de RealidadStore](./Diagrama%20Arquitectura.png)

### Flujo general DevOps y GitOps

```text
Cambio de código
      │
      ▼
GitHub: realidadstore-devops
      │
      ▼
Tekton Pipeline
  ├── clone-source
  ├── build-backend  ──┐
  ├── build-frontend ──┼──► Docker Hub
  └── update-git-manifests
             │
             ▼
GitHub: k8s/app actualizado
             │
             ▼
Argo CD
             │
             ▼
Kubernetes realiza el rollout
```

### Flujo funcional del ecommerce

```text
Cliente web
    │
    ▼
NodePort 30080
    │
    ▼
Frontend React + Tailwind + Nginx
    │
    ▼
Service backend
    │
    ▼
Backend FastAPI
    │
    ▼
Service PostgreSQL
    │
    ▼
PostgreSQL StatefulSet + PVC NFS
```

### Flujo de observabilidad

```text
Métricas:
Pods / nodos / aplicación
          │
          ▼
      Prometheus
          │
          ▼
       Grafana

Logs:
Frontend / Backend / PostgreSQL
          │
          ▼
     Grafana Alloy
          │
          ▼
         Loki
          │
          ▼
   Grafana Explore / LogQL
```

---

## Objetivos del proyecto

- Desplegar una aplicación de **tres capas** en Kubernetes.
- Mantener disponibilidad básica mediante réplicas y distribución entre workers.
- Escalar el backend automáticamente con **HorizontalPodAutoscaler**.
- Persistir PostgreSQL, Loki y Workspaces de Tekton mediante **NFS CSI**.
- Obtener métricas reales con Prometheus, node-exporter, metrics-server y ServiceMonitor.
- Crear dashboards técnicos y de negocio en Grafana.
- Centralizar e indexar logs con Grafana Alloy y Loki.
- Construir y publicar imágenes con Tekton y Buildah.
- Aplicar GitOps con Argo CD y sincronización automática.
- Mantener secretos y credenciales fuera del repositorio.

---

## Infraestructura del laboratorio

| Rol | Hostname | Dirección IP |
|---|---|---:|
| Control plane / NFS Server | `k8s-master01` | `192.168.222.132` |
| Worker 1 | `k8s-worker01` | `192.168.222.133` |
| Worker 2 | `k8s-worker02` | `192.168.222.134` |

### NFS

| Propiedad | Valor |
|---|---|
| Servidor NFS | `192.168.222.132` |
| Export | `/srv/nfs/k8s-storage` |
| Red autorizada | `192.168.222.0/24` |
| StorageClass | `nfs-csi` |
| Acceso principal | `ReadWriteMany` |
| Uso | PostgreSQL, Loki y Workspace CI/CD |

Validación:

```bash
showmount -e 192.168.222.132
kubectl get storageclass
kubectl get pv
kubectl get pvc -A
```

---

## Namespaces

| Namespace | Responsabilidad |
|---|---|
| `realidadstore` | Frontend, backend, PostgreSQL, Services, HPA y PVC |
| `monitoring` | Prometheus, Grafana, node-exporter, kube-state-metrics y ServiceMonitor |
| `logging` | Loki y Grafana Alloy |
| `cicd` | Tasks, Pipelines, PipelineRuns, Secrets y Workspace de Tekton |
| `argocd` | Componentes y Application de Argo CD |
| `tekton-pipelines` | Controladores internos de Tekton |

---

## Tecnologías

### Aplicación

- **Frontend:** React, Vite, Tailwind CSS y Nginx.
- **Backend:** Python y FastAPI.
- **Base de datos:** PostgreSQL.
- **Comunicación:** HTTP/REST.
- **Contenedores:** Dockerfiles independientes para frontend y backend.

### Plataforma

- Kubernetes `v1.28.15`.
- NFS CSI.
- Metrics Server.
- HorizontalPodAutoscaler.
- StatefulSet para PostgreSQL.
- Deployments para frontend y backend.
- NodePort para acceso desde el laboratorio.

### Observabilidad

- Prometheus.
- Grafana.
- node-exporter como DaemonSet.
- kube-state-metrics.
- ServiceMonitor del backend.
- Métricas personalizadas del ecommerce.
- Loki.
- Grafana Alloy.
- LogQL.

### CI/CD

- GitHub.
- Tekton Pipelines.
- Buildah.
- Docker Hub.
- Argo CD.
- GitOps sobre `k8s/app`.

---

## Estructura del repositorio

```text
realidadstore-devops/
├── app/
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── frontend/
│       ├── Dockerfile
│       ├── index.html
│       ├── nginx.conf
│       ├── package.json
│       ├── postcss.config.js
│       ├── tailwind.config.js
│       └── src/
│           ├── index.css
│           ├── main.jsx
│           └── styles.css
├── cicd/
│   ├── argocd/
│   │   ├── argocd-nodeport.yaml
│   │   └── 01-realidadstore-application.yaml
│   └── tekton/
│       ├── 00-workspace-pvc.yaml
│       ├── 01-service-account.yaml
│       ├── 02-task-git-clone.yaml
│       ├── 03-pipeline-ci.yaml
│       ├── 04-pipelinerun-clone.yaml
│       ├── 05-task-buildah.yaml
│       ├── 06-pipelinerun-build.yaml
│       ├── 07-task-update-git.yaml
│       └── 08-pipelinerun-gitops.yaml
├── docs/
│   └── arquitectura-devops-realidadstore.png
├── k8s/
│   ├── app/
│   │   ├── 00-namespace.yaml
│   │   ├── 04-postgres-secret.yaml.example
│   │   ├── 05-postgres-configmap.yaml
│   │   ├── 06-postgres-service.yaml
│   │   ├── 07-postgres-statefulset.yaml
│   │   ├── 08-backend-deployment.yaml
│   │   ├── 09-backend-service.yaml
│   │   ├── 10-frontend-deployment.yaml
│   │   ├── 11-frontend-service.yaml
│   │   └── 12-backend-hpa.yaml
│   ├── cluster/
│   │   └── 01-storageclass-nfs.yaml
│   └── tests/
│       ├── 02-pvc-test.yaml
│       └── 03-pod-test-nfs.yaml
├── logging/
│   ├── alloy-values.yaml
│   └── loki-values.yaml
├── monitoring/
│   ├── kube-prometheus-values.yaml.example
│   └── realidadstore-backend-servicemonitor.yaml
├── .gitignore
└── README.md
```

> La carpeta `k8s/app` representa el estado deseado de la aplicación y es la ruta observada por Argo CD.

---

## Aplicación de tres capas

### Frontend

- React + Tailwind CSS.
- Servido por Nginx.
- Dos réplicas en estado normal.
- Expuesto mediante Service y NodePort `30080`.
- Preparado para múltiples clientes simultáneos.

### Backend

- FastAPI.
- Dos réplicas mínimas.
- Escalamiento automático hasta seis réplicas.
- Service interno `backend`.
- Endpoints de negocio, métricas y carga controlada.
- Métricas HTTP por endpoint, método, código y latencia.

### PostgreSQL

- StatefulSet `postgres`.
- Un pod estable: `postgres-0`.
- Service interno `postgres`.
- PVC dinámico sobre `nfs-csi`.
- Persistencia de productos, carritos, órdenes y stock.

---

## Alta disponibilidad y escalamiento

### Frontend

El frontend utiliza dos réplicas para mantener disponibilidad básica:

```bash
kubectl get deployment frontend -n realidadstore
kubectl get pods -n realidadstore -l app=frontend -o wide
```

### Backend y HPA

El backend mantiene al menos dos pods y puede escalar hasta seis:

```text
Mínimo: 2
Máximo: 6
Objetivo de CPU: 40 %
```

Validación:

```bash
kubectl get hpa -n realidadstore
kubectl get deployment backend -n realidadstore
kubectl get pods -n realidadstore -l app=backend -o wide
kubectl top pods -n realidadstore
```

El HPA controla `spec.replicas` del backend. Argo CD ignora esa diferencia para evitar competir con el autoscaler.

---

## Persistencia

### PVC de PostgreSQL

```bash
kubectl get pvc -n realidadstore
kubectl describe pvc postgres-data-postgres-0 -n realidadstore
```

Estado esperado:

```text
STATUS: Bound
STORAGECLASS: nfs-csi
CAPACITY: 5Gi
```

### PVC de Tekton

```bash
kubectl get pvc realidadstore-cicd-workspace -n cicd
```

Este volumen comparte el repositorio clonado entre las Tasks del Pipeline.

### Persistencia de Loki

Loki usa almacenamiento persistente para conservar chunks e índices de logs.

---

## Accesos del laboratorio

| Componente | URL |
|---|---|
| RealidadStore | `http://192.168.222.132:30080` |
| Grafana | `http://192.168.222.132:30300` |
| Prometheus | `http://192.168.222.132:30090` |
| Argo CD | `http://192.168.222.132:30081` |

> Estas direcciones corresponden al laboratorio local y no deben considerarse endpoints de producción.

---

## Preparación de secretos

Los secretos reales no se almacenan en Git.

### PostgreSQL

```bash
kubectl create secret generic postgres-secret \
  -n realidadstore \
  --from-literal=POSTGRES_DB='realidadstoredb' \
  --from-literal=POSTGRES_USER='realidad_user' \
  --from-literal=POSTGRES_PASSWORD='CAMBIAR_PASSWORD' \
  --dry-run=client \
  -o yaml |
kubectl apply -f -
```

### Docker Hub para Tekton

Crear un Access Token en Docker Hub y generar el Secret:

```bash
read -rp "Docker Hub ID: " DOCKER_USER
read -rsp "Docker Hub Access Token: " DOCKER_TOKEN
echo

DOCKER_AUTH="$(
  printf '%s:%s' "${DOCKER_USER}" "${DOCKER_TOKEN}" |
  base64 |
  tr -d '\n'
)"

cat > /tmp/docker-config.json <<EOF
{
  "auths": {
    "https://index.docker.io/v1/": {
      "auth": "${DOCKER_AUTH}"
    }
  }
}
EOF

kubectl create secret generic dockerhub-config \
  -n cicd \
  --from-file=config.json=/tmp/docker-config.json \
  --dry-run=client \
  -o yaml |
kubectl apply -f -

unset DOCKER_TOKEN DOCKER_AUTH
rm -f /tmp/docker-config.json
```

### GitHub para el commit GitOps

Crear un Fine-grained Personal Access Token limitado al repositorio, con permiso:

```text
Contents: Read and write
```

Guardar el token sin incluirlo en el historial:

```bash
read -rsp "GitHub token: " GITHUB_TOKEN
echo

kubectl create secret generic github-write-credentials \
  -n cicd \
  --from-literal=username='AngelUri03' \
  --from-literal=token="${GITHUB_TOKEN}" \
  --dry-run=client \
  -o yaml |
kubectl apply -f -

unset GITHUB_TOKEN
```

---

## Despliegue inicial

### 1. Verificar el clúster

```bash
kubectl get nodes -o wide
kubectl get namespaces
kubectl get storageclass
```

Los tres nodos deben estar en `Ready`.

### 2. Crear namespace y Secret

```bash
kubectl apply -f k8s/app/00-namespace.yaml
```

Crear `postgres-secret` antes de sincronizar la aplicación.

### 3. Recursos generales de almacenamiento

```bash
kubectl apply -f k8s/cluster/01-storageclass-nfs.yaml
```

> El driver NFS CSI debe estar instalado previamente.

### 4. Aplicación mediante Argo CD

```bash
kubectl apply -f cicd/argocd/01-realidadstore-application.yaml
```

Validación:

```bash
kubectl get application realidadstore -n argocd
kubectl get all -n realidadstore
kubectl get pvc -n realidadstore
```

Estado esperado:

```text
Argo CD: Synced / Healthy
Frontend: 2 réplicas
Backend: 2 o más réplicas
PostgreSQL: 1 pod
PVC: Bound
```

---

## Monitoreo con Prometheus y Grafana

### Componentes

- Prometheus recolecta métricas.
- Grafana visualiza métricas y logs.
- node-exporter obtiene métricas de cada nodo.
- kube-state-metrics expone estado de objetos Kubernetes.
- metrics-server alimenta `kubectl top` y HPA.
- ServiceMonitor descubre las métricas de FastAPI.

### Validación

```bash
kubectl get pods -n monitoring -o wide
kubectl top nodes
kubectl top pods -n realidadstore
```

Node Exporter debe responder en:

```text
192.168.222.132:9100
192.168.222.133:9100
192.168.222.134:9100
```

### Dashboard principal

Nombre recomendado:

```text
RealidadStore DevOps Dashboard
```

Secciones:

1. `Cluster / Workers`
2. `Pods RealidadStore`
3. `Backend FastAPI`
4. `HPA / Escalamiento`
5. `Ecommerce / Negocio`
6. `PostgreSQL / Persistencia`
7. `Disponibilidad / Salud`
8. `Logs / Loki`

### Métricas principales

- CPU de cada nodo.
- Memoria usada por nodo.
- Disco raíz por nodo.
- Load average.
- CPU y memoria por pod.
- Pods Running por componente.
- Reinicios por pod.
- Requests por endpoint.
- Métodos HTTP.
- Errores por código.
- Latencia p95.
- Requests en el rango seleccionado.
- Réplicas actuales y deseadas del HPA.
- CPU del backend contra objetivo del HPA.
- Búsquedas por categoría.
- Productos agregados al carrito.
- Carritos activos.
- Checkouts por resultado.
- Órdenes registradas.
- Estado, capacidad y uso del PVC PostgreSQL.

### Ejemplos PromQL

CPU por nodo:

```promql
100 * (
  1 - avg by(instance) (
    rate(node_cpu_seconds_total{mode="idle"}[2m])
  )
)
```

Memoria usada:

```promql
100 * (
  1 -
  (
    node_memory_MemAvailable_bytes
    /
    node_memory_MemTotal_bytes
  )
)
```

CPU por pod:

```promql
sum by(pod) (
  rate(container_cpu_usage_seconds_total{
    namespace="realidadstore",
    container!="",
    container!="POD"
  }[2m])
)
```

Pods Running por componente:

```promql
sum by(label_app) (
  kube_pod_status_phase{
    namespace="realidadstore",
    phase="Running"
  }
  * on(namespace, pod)
  group_left(label_app)
  kube_pod_labels{namespace="realidadstore"}
)
```

Uso del volumen PostgreSQL:

```promql
100 *
max(
  kubelet_volume_stats_used_bytes{
    namespace="realidadstore",
    persistentvolumeclaim="postgres-data-postgres-0"
  }
)
/
max(
  kubelet_volume_stats_capacity_bytes{
    namespace="realidadstore",
    persistentvolumeclaim="postgres-data-postgres-0"
  }
)
```

---

## Logging con Loki y Grafana Alloy

### Flujo

```text
Pods de realidadstore
      │
      ▼
Grafana Alloy
  - descubrimiento Kubernetes
  - labels
  - enriquecimiento
      │
      ▼
Loki
  - almacenamiento
  - indexación
      │
      ▼
Grafana Explore
```

### Labels disponibles

- `namespace`
- `app`
- `pod`
- `container`
- `node`
- `cluster`
- `environment`
- `job`

### Consultas LogQL

Todos los logs:

```logql
{namespace="realidadstore"}
```

Backend sin probes:

```logql
{namespace="realidadstore", container="backend"}
!= "/health"
!= "/metrics"
```

Errores HTTP reales:

```logql
{namespace="realidadstore", container="backend"}
| regexp `"(?P<method>[A-Z]+) (?P<path>[^ ]+) HTTP/[^"]+" (?P<status>[0-9]{3})`
| status=~"4..|5.."
```

Logs de PostgreSQL con problemas:

```logql
{namespace="realidadstore", container="postgres"}
|~ "(?i)error|fatal|panic|warning"
```

Volumen por contenedor:

```logql
sum by(container) (
  count_over_time(
    {namespace="realidadstore"}[$__interval]
  )
)
```

---

## Pipeline CI/CD

### Estado actual

El Pipeline es completo, pero su disparo es manual:

```text
CI: iniciado manualmente con un PipelineRun
CD: automático mediante Argo CD
```

El PipelineRun manual se conserva para una demostración controlada y para recuperaciones.

### Tasks

| Orden | Task | Función |
|---:|---|---|
| 1 | `clone-source` | Clona GitHub y valida la estructura |
| 2a | `build-backend` | Construye y publica la imagen FastAPI |
| 2b | `build-frontend` | Construye y publica la imagen React/Nginx |
| 3 | `update-git-manifests` | Actualiza imágenes en `k8s/app`, crea commit y hace push |

Las construcciones del backend y frontend se ejecutan en paralelo.

### Tags de imagen

Cada imagen usa el SHA del commit clonado:

```text
docker.io/angeluri/realidadstore-backend:<commit-sha>
docker.io/angeluri/realidadstore-frontend:<commit-sha>
```

Esto permite trazabilidad entre:

- Código fuente.
- Imagen de contenedor.
- Manifiesto GitOps.
- Deployment activo.

### Ejecutar el Pipeline completo

Después de subir el cambio a GitHub:

```bash
git add .
git commit -m "feat: describe el cambio"
git pull --rebase origin main
git push origin main
```

Crear un nuevo PipelineRun:

```bash
kubectl create -f cicd/tekton/08-pipelinerun-gitops.yaml
```

Obtener el último run:

```bash
export RUN="$(
  kubectl get pipelinerun \
    -n cicd \
    -l app.kubernetes.io/component=gitops-deployment \
    --sort-by=.metadata.creationTimestamp \
    -o name |
  tail -1 |
  cut -d/ -f2
)"

echo "${RUN}"
```

Monitorear:

```bash
watch -n 3 "
kubectl get pipelinerun ${RUN} -n cicd
echo
kubectl get taskrun -n cicd \
  -l tekton.dev/pipelineRun=${RUN}
echo
kubectl get pods -n cicd \
  -l tekton.dev/pipelineRun=${RUN}
"
```

Resultado esperado:

```text
clone-source             Succeeded
build-backend            Succeeded
build-frontend           Succeeded
update-git-manifests     Succeeded
PipelineRun              Succeeded
```

Logs:

```bash
kubectl logs \
  -n cicd \
  -l "tekton.dev/pipelineRun=${RUN}" \
  --all-containers=true \
  --prefix=true
```

---

## GitOps con Argo CD

Argo CD observa:

```text
Repositorio: https://github.com/AngelUri03/realidadstore-devops.git
Rama: main
Ruta: k8s/app
```

Políticas:

```text
Automated sync
Self-heal
Prune
CreateNamespace
RespectIgnoreDifferences
```

El backend ignora `/spec/replicas`, porque el número de pods pertenece al HPA.

### Validación

```bash
kubectl get application realidadstore -n argocd
```

Resultado esperado:

```text
SYNC STATUS: Synced
HEALTH STATUS: Healthy
```

Imágenes desplegadas:

```bash
kubectl get deployment backend frontend \
  -n realidadstore \
  -o custom-columns='DEPLOYMENT:.metadata.name,IMAGE:.spec.template.spec.containers[0].image'
```

Rollouts:

```bash
kubectl rollout status deployment/backend -n realidadstore
kubectl rollout status deployment/frontend -n realidadstore
```

---

## Flujo para publicar un cambio

Ejemplo de cambio en frontend:

```bash
cd ~/realidadstore

git add app/frontend
git commit -m "feat(frontend): actualiza interfaz"
git pull --rebase origin main
git push origin main
```

Ejecutar CI/CD:

```bash
kubectl create -f cicd/tekton/08-pipelinerun-gitops.yaml
```

Resultado:

```text
1. Tekton clona el nuevo commit.
2. Buildah construye backend y frontend.
3. Docker Hub recibe imágenes con el SHA.
4. Tekton actualiza los Deployments en k8s/app.
5. Tekton publica un commit GitOps.
6. Argo CD detecta el commit.
7. Kubernetes reemplaza los pods.
8. El cambio aparece en NodePort 30080.
```

Actualizar la copia local después del commit automático:

```bash
git pull --ff-only origin main
```

---

## Pruebas funcionales

### Estado general

```bash
kubectl get nodes
kubectl get all -n realidadstore
kubectl get pvc -n realidadstore
kubectl get hpa -n realidadstore
```

### API

```bash
curl -s http://192.168.222.132:30080/api/products
curl -s http://192.168.222.132:30080/api/categories
curl -s http://192.168.222.132:30080/api/store/summary
```

### Error controlado

```bash
curl -i http://192.168.222.132:30080/api/products/999999
```

### Carrito

```bash
curl -s -X POST \
  http://192.168.222.132:30080/api/cart/items \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: prueba-readme" \
  -d '{"product_id":1,"quantity":1}'
```

### Persistencia

```bash
kubectl exec -n realidadstore postgres-0 -- \
  psql -U realidad_user -d realidadstoredb \
  -c "SELECT now();"
```

### Escalamiento

```bash
kubectl get hpa -n realidadstore -w
```

Durante una prueba de carga, el backend debe subir desde dos réplicas y regresar gradualmente al mínimo configurado.

---

## Comandos de operación

### Estado de la aplicación

```bash
kubectl get deploy,statefulset,pods,svc,hpa,pvc -n realidadstore
```

### Monitoreo

```bash
kubectl get pods -n monitoring
kubectl top nodes
kubectl top pods -n realidadstore
```

### Logging

```bash
kubectl get pods,svc,pvc -n logging
kubectl logs -n logging deployment/alloy -c alloy --tail=100
kubectl logs -n logging loki-0 --tail=100
```

### Tekton

```bash
kubectl get task,pipeline,pipelinerun,taskrun -n cicd
```

### Argo CD

```bash
kubectl get applications -n argocd
kubectl get pods -n argocd
```

---

## Solución de problemas

### `kubectl top` muestra `Metrics API not available`

Verificar:

```bash
kubectl get pods -n kube-system | grep metrics-server
kubectl logs -n kube-system deployment/metrics-server
```

El pod debe estar `Running` y disponible.

### Node Exporter aparece DOWN

Probar desde el master:

```bash
curl -s http://192.168.222.132:9100/metrics | head
curl -s http://192.168.222.133:9100/metrics | head
curl -s http://192.168.222.134:9100/metrics | head
```

Verificar que el firewall permita `9100/tcp` en los tres nodos.

### Loki Gateway responde 404 en `/ready`

El gateway Nginx puede no publicar esa ruta. Validar la API:

```bash
curl -s \
  http://loki-gateway.logging.svc.cluster.local/loki/api/v1/status/buildinfo
```

### Tekton no puede modificar archivos del Workspace

La Task de clonado normaliza permisos:

```bash
find . -mindepth 1 -exec chmod a+rwX {} +
```

Esto permite que la imagen `yq` modifique los YAML creados en el PVC NFS.

### GitHub devuelve `Invalid username or token`

Verificar que el Fine-grained token:

- No esté vencido.
- Pertenezca a `AngelUri03`.
- Incluya `realidadstore-devops`.
- Tenga `Contents: Read and write`.
- Esté almacenado en `github-write-credentials`.

### Argo CD aparece OutOfSync por las réplicas del backend

La Application debe incluir:

```yaml
ignoreDifferences:
  - group: apps
    kind: Deployment
    name: backend
    namespace: realidadstore
    jsonPointers:
      - /spec/replicas
```

Esto evita conflictos entre Argo CD y HPA.

### El cambio del frontend no aparece

1. Confirmar que el cambio esté en `origin/main`.
2. Ejecutar un PipelineRun nuevo.
3. Validar que Tekton publicó el commit GitOps.
4. Confirmar `Synced / Healthy`.
5. Revisar la nueva imagen del Deployment.
6. Recargar el navegador con `Ctrl + F5`.

---

## Seguridad

- No almacenar contraseñas, tokens ni archivos `.dockerconfigjson` en Git.
- Mantener configuraciones reales como archivos `*.local.yaml`.
- Revocar inmediatamente cualquier token expuesto.
- Usar tokens de alcance mínimo.
- No usar NodePort e interfaces HTTP sin TLS en producción.
- El acceso actual está diseñado para un laboratorio aislado.
- En producción se recomienda Ingress, TLS, RBAC restrictivo, NetworkPolicies y un Secret Manager.

---

## Cobertura de la rúbrica

| Rubro | Implementación |
|---|---|
| Cluster funcional con HA básico | Tres nodos, frontend replicado y backend distribuido |
| PV/PVC/StorageClass NFS | NFS CSI, StorageClass dinámica y PVC para PostgreSQL, Loki y Tekton |
| App de tres capas | React/Nginx, FastAPI y PostgreSQL |
| Prometheus + Grafana | Métricas reales de nodos, pods, API, HPA, negocio y persistencia |
| EFK/Loki | Alloy recolecta y Loki indexa logs de frontend, backend y PostgreSQL |
| Tekton + Argo CD | Build, push, actualización GitOps y despliegue automático |
| Defensa técnica individual | Arquitectura, comandos, pruebas y troubleshooting documentados |

---

## Autores

**Morales Galicia Angel Uriel**

**Elizalde Pérez Alan**

**Saldivar Pantoja Oscar**

---

## Estado del proyecto

```text
Cluster Kubernetes:        Operativo
Aplicación de tres capas:  Operativa
PostgreSQL persistente:    Operativo
HPA:                       Operativo
Prometheus y Grafana:      Operativos
Loki y Alloy:              Operativos
Tekton Pipeline:           Operativo
Docker Hub:                Operativo
Argo CD GitOps:            Synced / Healthy
```

> RealidadStore demuestra un flujo DevOps completo, reproducible y observable, desde el código fuente hasta el despliegue final en Kubernetes.
