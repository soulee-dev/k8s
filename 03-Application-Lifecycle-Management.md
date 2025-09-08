# Application Lifecycle Management

# Rolling Updates and Rollbacks

## Rollout과 버전 관리

* Deployment는 새로운 버전을 배포할 때마다 **revision**을 생성함
* 상태 확인

  ```sh
  kubectl rollout status deployment/myapp-deployment
  ```
* 배포 이력 확인

  ```sh
  kubectl rollout history deployment/myapp-deployment
  ```

## Deployment Strategy

* **Recreate**

  * 기존 Pod을 모두 종료 후 새 Pod 생성
  * 잠시 동안 서비스가 중단될 수 있음
  * 이벤트를 보면 기존 ReplicaSet이 0으로 스케일 다운되고 새로운 ReplicaSet이 원하는 수치(예: 5)로 스케일 업됨
* **Rolling Update (기본값)**

  * 기존 Pod을 하나씩 줄이면서 동시에 새 Pod을 하나씩 늘림
  * 무중단 배포 가능
  * 이벤트를 보면 old ReplicaSet이 하나 줄고, new ReplicaSet이 하나 증가하는 식으로 교차 진행됨

## Kubectl apply

* `kubectl apply`를 통해 매니페스트를 업데이트하면 Deployment의 **새로운 revision**이 생성됨
* 애플리케이션이 정상적으로 동작 중인지 여부는 rollout status나 Pod 상태를 통해 확인해야 함

## Rollback

* 문제가 생기면 이전 revision으로 되돌릴 수 있음

  ```sh
  kubectl rollout undo deployment/myapp-deployment
  ```

## 주요 명령어 요약

```sh
kubectl rollout status deployment/myapp-deployment    # 현재 rollout 상태 확인
kubectl rollout history deployment/myapp-deployment   # 배포 이력 확인
kubectl rollout undo deployment/myapp-deployment      # 이전 버전으로 롤백
```

## Practice Test - Rolling Updates and Rollbacks
```sh
# 페이지 내용이 너무 길떈 'less'명령어
kubectl describe deployment frontend | less
```

# Commands and Arguments in Docker
## CMD
- 기본 실행 명령어 정의
- 사용자가 run에서 인자를 주면 **덮어쓰기**됨

```dockerfile
FROM ubuntu
CMD ["sleep", "5"]
```

```sh
docker run ubuntu-sleeper

docker run ubuntu-sleeper sleep 10
```

## ENTRYPOINT
- 컨테이너 실행 시 항상 실행되어야 하는 **고정 실행 명령어**
- 사용자가 인자를 주더라도 ENTRYPOINT는 덮어쓰기 되지 않고 뒤에 인자로 붙음

```dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
```

```sh
docker run ubuntu-sleeper 5
```

## CMD + ENTRYPOINT
- ENTRYPOINT: 실행 파일 지정 (고정).
- CMD: ENTRYPOINT에 전달될 기본 인자(default arguments).
- 즉, docker run에서 아무 인자 안주면 CMD가 기본값으로 사용되고, 인자를 주면 CMD 대신 그 값이 사용됨

# Commands and Arguments in Kubernetes
## 1. command

* 컨테이너가 실행할 **프로세스 자체**를 지정.
* Dockerfile에 `ENTRYPOINT`가 있으면 그것을 무시하고 새로운 실행 명령으로 바꿈.

```yaml
containers:
  - name: app
    image: busybox
    command: ["sleep"]   # 실행할 프로그램
```

---

## 2. args

* `command`에 전달할 **인자(arguments)** 를 지정.
* Dockerfile의 `CMD`를 덮어씌우는 역할.

```yaml
containers:
  - name: app
    image: busybox
    command: ["sleep"]   # 실행할 프로그램
    args: ["3600"]       # sleep에 전달할 인자
```

## Practice Test - Commands and Arguments
```sh
# Pod에서 command/args를 업데이트 하는건 불가능 하다
kubectl replace --force -f ubuntu-sleeper-3.yaml
```

# Configure Environment Variables in Applications
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: envar-demo
  labels:
    purpose: demonstrate-envars
spec:
  containers:
  - name: envar-demo-container
    image: gcr.io/google-samples/hello-app:2.0
    env:
    - name: DEMO_GREETING
      value: "Hello from the environment"
    - name: DEMO_FAREWELL
      value: "Such a sweet sorrow"
```


- Plain Key
- ConfigMap
- Secrets


# Configuring ConfigMaps in Applications

ConfigMap은 애플리케이션에서 사용하는 **환경 설정 데이터**를 관리하기 위한 Kubernetes 오브젝트임.
Pod 정의와는 별도로 key-value 형식의 설정을 저장하고, Pod에 주입하여 애플리케이션이 동적으로 설정을 읽을 수 있게 함.

---

## 생성 방법

### 1. Imperative 방식

```sh
kubectl create configmap <config-name> \
  --from-literal=<key>=<value>
```

### 2. Declarative 방식 (YAML 정의)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_COLOR: blue
```

---

## Pod에 주입 방법

ConfigMap은 Pod 내부에서 **환경 변수** 또는 **Volume** 형태로 사용 가능함.

### 1. envFrom (전체 주입)

```yaml
spec:
  containers:
  - name: app
    envFrom:
      - configMapRef:
          name: app-config
```

### 2. 단일 환경변수 주입

```yaml
spec:
  containers:
  - name: app
    env:
      - name: APP_COLOR
        valueFrom:
          configMapKeyRef:
            name: app-config
            key: APP_COLOR
```

### 3. Volume으로 마운트

ConfigMap 데이터를 파일로써 컨테이너 내부에 주입 가능

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
      - name: config-volume
        mountPath: /etc/config
  volumes:
    - name: config-volume
      configMap:
        name: app-config
```

컨테이너 내부에서는 `/etc/config/APP_COLOR` 같은 파일 형태로 접근 가능함.

## Practice Test - Env Variables
vi에서 탭을 누를떄 스페이스로 하려면
```vim
:set expandtab
:set tabstop=2
:set shiftwidth=2
```

Syntax를 켜려면
```vim
:syntax on
```

```sh
kubectl get configmaps
kubectl describe configmap db-config

kubectl create configmap  webapp-config-map \
--from-literal=APP_COLOR=darkblue --from-literal=APP_OTHER=disregard
```

# Secrets

Kubernetes Secret은 민감한 데이터(비밀번호, 토큰, 인증서 등)를 저장하고 Pod에서 참조할 수 있도록 하는 리소스임. ConfigMap과 비슷하지만, 보안 데이터를 저장하는 용도로 사용됨.

---

## Secret 생성 방법

### 1. Imperative 방식

```sh
kubectl create secret generic <secret-name> \
  --from-literal=<key>=<value>
```

### 2. Declarative 방식

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  username: dXNlcm5hbWU=   # base64 encoded
  password: cGFzc3dvcmQ=   # base64 encoded
```

### base64 인코딩/디코딩

```sh
echo -n <value> | base64           # 인코딩
echo -n <base64-value> | base64 --decode  # 디코딩
```

> Secret은 base64로 인코딩되어 저장되지만, **기본적으로 암호화(encryption)는 아님**. (etcd에 저장될 때 암호화 옵션을 따로 설정해야 함)

---

## Pod에 Secret 주입 방법

### 1. 환경 변수 전체 주입

```yaml
envFrom:
  - secretRef:
      name: app-secret
```

### 2. 특정 key를 환경 변수로 주입

```yaml
env:
  - name: DB_USER
    valueFrom:
      secretKeyRef:
        name: app-secret
        key: username
```

### 3. Volume으로 주입

```yaml
volumes:
  - name: secret-vol
    secret:
      secretName: app-secret

containers:
  - name: app
    volumeMounts:
      - name: secret-vol
        mountPath: "/etc/secret"
```

* key 이름으로 파일이 생성되고, 그 내용이 value가 됨

## Practice Test - Secrets
```sh
kubectl get secrets

kubectl describe secret dashboard-token

kubectl get pod webapp-pod -o yaml > webapp-definition.yaml
```

VI에서 `dd`로 지운 명령를 다시 되도리려면 `u`를 사용할 수 있다.

# Multi Container Pods

## 개념

* 여러 컨테이너가 하나의 Pod 안에서 동작
* **생성/삭제 함께 수행** (created together, destroyed together)
* **공유 리소스**: lifecycle, network, storage

```yaml
spec:
  containers:
    - name: webapp
      image: nginx
    - name: main-app
      image: busybox
```

---

## Multi Container Pod Design Pattern

### 1. Co-located containers

* 같은 Pod 안에서 함께 시작하고 종료됨
* 주로 **서로 보완적인 기능**을 수행

  * 예: 하나는 데이터 처리, 다른 하나는 결과 노출

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: co-located-example
spec:
  containers:
    - name: main-app
      image: busybox
      command: ["sh", "-c", "while true; do echo Hello from main-app; sleep 5; done"]
    - name: helper
      image: busybox
      command: ["sh", "-c", "while true; do echo Helper running; sleep 5; done"]
```

---

### 2. Init Containers

* 메인 컨테이너가 실행되기 전에 **한 번만 실행되는 컨테이너**
* 환경 설정, 데이터 준비, 권한 설정 등 선행 작업에 사용

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-example
spec:
  initContainers:
    - name: init-myservice
      image: busybox
      command: ['sh', '-c', 'echo initializing...; sleep 5;']
  containers:
    - name: main-app
      image: busybox
      command: ["sh", "-c", "echo The app is running! && sleep 3600"]
```

---

### 3. Sidecar Containers

* 메인 컨테이너를 보조하는 컨테이너
* **메인 컨테이너보다 먼저 시작**되며 주로 **로그 수집, 데이터 동기화, 프록시 역할** 수행
* 메인 컨테이너와 함께 실행되며 `restartPolicy: Always` 사용

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-example
spec:
  containers:
    - name: main-app
      image: busybox
      command: ["sh", "-c", "while true; do echo Running app...; sleep 5; done"]
  initContainers:
    - name: sidecar
      image: busybox
      command: ["sh", "-c", "while true; do echo Collecting logs...; sleep 5; done"]
  restartPolicy: Always
```

---

## Real world scenario

* **Sidecar Filebeat + ELK Stack**

  * 메인 애플리케이션 컨테이너: 로그 생성
  * 사이드카 컨테이너(Filebeat): 로그를 수집하여 Elasticsearch로 전송
  * Kibana를 통해 시각화

## Practice Test - Multi Container Pods
```sh
kubectl -n elastic-stack exec -it app -- cat /log/app.log
```

# Init Containers

## 개념

* 일반 컨테이너는 Pod의 라이프사이클 동안 항상 살아 있어야 함
  (예: 웹 애플리케이션 + 로그 에이전트)
* 하지만 **한 번 실행되고 종료되는 작업**이 필요한 경우 존재
  (예: 코드/바이너리 다운로드, 외부 서비스 준비 대기)
* 이런 경우 사용하는 것이 **InitContainer**임

## 특징

* `spec.initContainers` 섹션에 정의
* 일반 컨테이너와 동일하게 정의하지만 **반드시 완료(Complete) 상태**가 되어야 함
* 모든 InitContainer가 순차적으로 실행 완료된 후에 메인 컨테이너 실행
* 만약 InitContainer가 실패하면 Pod는 반복적으로 재시작하여 InitContainer가 성공할 때까지 재시도

## 사용 사례

1. **애플리케이션 시작 전 준비 작업**

   * Git 리포지토리에서 코드/바이너리 다운로드
   * Config 파일 생성
2. **외부 서비스 준비 대기**

   * DB, 다른 서비스가 준비될 때까지 `nslookup`이나 `curl` 등으로 확인 후 대기

## 예시 1: 단일 InitContainer

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
spec:
  containers:
  - name: myapp-container
    image: busybox:1.28
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
  initContainers:
  - name: init-myservice
    image: busybox
    command: ['sh', '-c', 'git clone <repo-url>']
```

## 예시 2: 다중 InitContainer

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
spec:
  containers:
  - name: myapp-container
    image: busybox:1.28
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
  initContainers:
  - name: init-myservice
    image: busybox:1.28
    command: ['sh', '-c', 'until nslookup myservice; do echo waiting for myservice; sleep 2; done;']
  - name: init-mydb
    image: busybox:1.28
    command: ['sh', '-c', 'until nslookup mydb; do echo waiting for mydb; sleep 2; done;']
```

## 정리

* InitContainer는 Pod 시작 전에 실행되는 준비 단계 컨테이너
* 반드시 **성공적으로 완료**되어야 본 컨테이너 실행
* 여러 개를 정의하면 **순차적 실행**
* Pod의 안정적 구동과 외부 의존성 준비에 활용됨

# Autoscaling
- Horizontal
- Vertical

Load increases,

Vertical Scaling (Increase size of existing server, CPU, Memory)

Horizontal Scaling (Adding more servers)

Two ways to scaling

1. Scaling Workload
  - Horizontal (Creating More pods)
      - kubectl scale ... (manual)
      - Horizontal Pod Autoscaler
  - Vertical (Increasing more allocated resource)
      - kubectl edit ... (manual)
      - Vertical Pod Autoscaler
2. Scaling Cluster Infra
  - kubeadm join (manual)
  - Cluster Autoscaler (Automated)

## Horizontal Pod Autoscaler (HPA)
 Manual Way
```sh
kubectl scale deploymeny my-app --replicas=3
```

HPA
- Observes metrics
- Adds pods
- Balances thresholds

```sh
kubectl autoscale deploymeny my-app \
  --cpu-percent=50 --min=1 --max=10
```

Usage goes beyond 50%, 

```sh
kubectl get hpa

kubectl delete hpa my-app
```

Declaritive

```yaml
...
kind: HorizontalPodAutoScaler
...
```

Custom Metrics Adapter
External Adapter
 - DATADOG
 - dynatrace
...

## Practice Test - Manual Scaling

`StatefulSets` also be be scaled down as well as `Deployments`

```sh
kubectl scale deployment flask-web-app --replicas=3
```

## Practise Test - HPA
```sh
kubectl get hpa

kubectl get hpa --watch
```

resource가 없는 경우 <unknonw>이 나오고
FailMetric evnet가 나온다

## In-place Resize of Pod Resources
in Beta

resizePolicy
  - resourceNmae: cpu
    restartPolicy: NotRequired
  - resourceName; memory
    restartPoliy: RestartContainer

Limitations
- Only CPU and Memory reousrced
- pod qos class cannot be changed
- init containers and ephemeral containers cannot be resiezed
- resource requests and limits cannobt rremoved once set
- a container's memory limit may not be reduced below its usage. if a request puts a container in this stable, the reisze status will remain InProgress until te desired memory limit becomes feasible
- windows pods cannot be resized

## Vertical Pod Autoscaling
you can edit the resource allocated in the pod by using kubectl edit.

but in the automated mean, vpa(vertical pod autosclaer) observes metrics, adjusts pod resources, balances thresholds

vpa does not come build-in with kubernetes, we must deploy it.

vpa admission controller (creates pods with recommended resources)
vpa updator (evicts them when update is needed)
vpa recommender (collects metrics from metrics server)

