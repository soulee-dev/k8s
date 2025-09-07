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