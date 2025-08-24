# Cluster Architecture


## 구성요소
- Control Plane
  - API Server
  - etcd
  - Scheduler
  - Controller

- Worker Node
  - kubelet
  - kube-proxy
  - CRI (Docker, containerD)

## Docker vs ContainerD
### Docker의 시작

- 초창기 컨테이너 생태계에서는 **Docker**가 사실상 표준.
- **이미지 빌드 + 실행 + CLI**를 모두 제공 → 사용자가 쓰기 편했음.
- Kubernetes도 처음에는 Docker를 런타임으로 사용하도록 만들어짐.

### CRI & OCI
다양한 Runtime(rkt)등에 호환을 갖추기 위해 표균 규격을 갖추게 됨.
- **CRI (Container Runtime Interface)**
  - Kubernetes가 컨테이너 런타임과 통신하기 위한 표준 인터페이스.
- **OCI (Open Container Initiative)**
  - 컨테이너 이미지 및 실행 형식을 표준화하기 위한 규격.

Docker는 CRI를 직접 지원하지 않았음. Kubernetes는 이를 해결하기 위해 **Dockershim**이라는 중간 계층을 두었음.

### containerd로 전환 (K8s v1.24)
- 사실 Docker 내부에도 **containerd**가 포함되어 있었음.
- 불필요하게 Docker를 거칠 필요가 없어졌기 때문에, v1.24부터는 **dockershim이 제거**됨.

### CLI

- **ctr**: containerd 기본 CLI
  ```bash
  ctr images pull docker.io/library/redis:alpine
  ```

- **nerdctl**: Docker와 유사한 CLI를 제공하는 툴 (ctr보다 편리)

  ```bash
  nerdctl run -d --name redis redis:alpine
  ```

- **crictl**: CRI 호환 런타임(containerd, CRI-O 등)을 다룰 수 있는 CLI
- 디버깅용으로만 사용 권장 (일반 실행/운영은 kubelet이 알아서 함)

## etcd

### 1. 개념
- **etcd**: Key-Value 기반의 분산 데이터베이스
- Kubernetes에서 클러스터 상태(노드, Pod, Config, Secret 등)를 저장하는 **중앙 저장소**
- **RAFT 합의 알고리즘** 기반으로 안정성과 일관성 보장

### 2. 주요 특징
- **Key-Value DB**: 단순한 구조지만 빠른 읽기/쓰기 지원
- **RAFT 알고리즘 (v2.0\~)**: 분산 환경에서 합의 보장, 초당 약 10k 쓰기 가능
- **API 버전**:
  - v2: 예전 방식 (`etcdctl set/get`)
  - v3: 현재 기본 (`etcdctl put/get`)
  - 전환 예시:

    ```shell
    ETCDCTL_API=3 etcdctl version
    ```
- **포트**: 기본적으로 `2379` 포트 사용
- **배포**: `kubeadm`으로 클러스터 설치 시 자동으로 etcd 구성


### 3. etcd 저장 데이터 (Kubernetes 기준)
- **Cluster Metadata**
  - nodes, pods, configs, secrets
  - accounts, roles, role bindings
  - 그 외 모든 리소스 상태 정보

### 4. 주요 명령어

```shell
# v2
etcdctl set key1 value1
etcdctl get key1

# v3
etcdctl put key1 value1
etcdctl get key1
```

## kube-apiserver

### 개념
- Kubernetes **Control Plane의 중심 컴포넌트**로, 클러스터의 모든 요청을 받아들이는 **API 게이트웨이** 역할을 한다.
- **Stateless**하며 클러스터 상태는 `etcd`에 저장된다.
- 모든 구성 요소(kubectl, scheduler, controller-manager, kubelet)는 **직접 etcd와 통신하지 않고** 반드시 kube-apiserver를 통해 요청을 처리한다.


### 주요 기능
1. **인증(Authentication)**
  - 요청을 보낸 사용자가 누구인지 확인 (인증서, 토큰, OIDC 등).

2. **인가(Authorization)**
  - RBAC/ABAC/Node Authorizer 등을 통해 권한을 검사.

3. **어드미션 컨트롤(Admission Control)**
  - 요청이 etcd에 저장되기 전 정책 검증 수행 (네임스페이스 제한, 리소스 쿼터 등).

4. **요청 검증 및 변환**
  - YAML/JSON 요청을 스키마에 맞게 검증하고, 기본값을 설정하거나 필요한 경우 변환.

5. **etcd와의 통신**
  - 최종적으로 클러스터 상태를 `etcd`에 저장하거나 읽어옴.

6. **이벤트 전달 및 브로커 역할**
  - 스케줄러, 컨트롤러 매니저, kubelet 등 다른 컴포넌트가 etcd 상태 변화를 감시할 수 있도록 이벤트를 전달.
  - 예: Pod 생성 요청이 들어오면 스케줄러에게 알리고, kubelet이 실행하도록 지시.

## kube-controller-manager

### 개념

`kube-controller-manager`는 쿠버네티스 클러스터의 여러 **컨트롤러(controller)**를 모아 실행하는 컴포넌트다.
각 컨트롤러는 클러스터의 **현재 상태(Current State)**를 주기적으로 확인하고, 사용자가 정의한 **원하는 상태(Desired State)**와 다르면 이를 맞추도록 조정한다.
컨트롤러들은 모두 **kube-apiserver**를 통해 etcd의 데이터를 읽고/갱신한다.

### 주요 컨트롤러

#### Node Controller
- **역할**: 노드의 상태(헬스 체크)를 모니터링하고, 문제가 생기면 대응
- **상세 동작**
  - 5초마다 노드 상태 확인 (Heartbeat 기반)
  - 40초 동안 응답이 없으면 `NotReady`로 표시
  - 5분(`pod eviction timeout`)이 지나면 해당 노드의 Pod를 다른 노드로 옮김(퇴거, Eviction)

#### Replication Controller
- **역할**: 특정 수(Replica)의 Pod가 항상 유지되도록 보장
- **상세 동작**
  - 현재 실행 중인 Pod 수와 사용자가 정의한 Replica 수 비교
  - 부족하면 새 Pod 생성, 초과하면 Pod 삭제

### 기타 컨트롤러
- **Deployment Controller**: 애플리케이션의 롤링 업데이트/롤백 관리
- **Endpoint Controller**: Service와 연결된 Pod의 IP를 관리
- **ServiceAccount & Token Controller**: 네임스페이스 기본 ServiceAccount 및 인증 토큰 생성
- **Job / CronJob Controller**: 일회성, 주기적 작업 실행 보장

### 동작 원리 (Control Loop)
1. 사용자가 매니페스트 정의 → API Server → etcd 저장
2. Controller-Manager는 API Server에서 리소스 상태 확인
3. Desired State와 Current State 비교
4. 불일치 발생 시 조정 (Pod 생성/삭제, 노드 제거 등)
5. 이 과정을 무한 루프로 반복

## kube-scheduler

### 개념

**kube-scheduler**는 쿠버네티스의 핵심 컴포넌트 중 하나로, **새로운 Pod를 어떤 노드에 배치할지 결정하는 역할**을 한다.
즉, Pod가 생성되면 kube-apiserver를 통해 etcd에 저장되는데, 이때 아직 어떤 노드에도 할당되지 않은 상태다.
이 Pod를 **스케줄링 대상(pending 상태)** 으로 감지하고, 가장 적합한 노드를 찾아서 **binding** 한다.

### 동작 과정

1. **Watch**
- API 서버에서 "스케줄되지 않은 Pod"를 watch 한다.

2. **Filtering (Predicates)**
- Pod가 실행될 수 없는 노드를 제거한다.
- 예시:
  - Node Selector, Node Affinity 불일치
  - Taints/Tolerations 불일치
  - 자원 부족(CPU, Memory 등)

3. **Scoring (Priorities)**
- 남은 후보 노드들 중 "얼마나 적합한지" 점수를 매긴다.
- 예시:
  - Least Requested Priority (자원이 많이 남은 노드 선호)
  - Balanced Resource Allocation (CPU/Memory 균형)
  - Pod Affinity / Anti-affinity 고려

4. **Binding**
- 가장 점수가 높은 노드를 선택해 API 서버에 Binding 객체를 생성 → Pod가 해당 노드로 스케줄된다.

### 주요 특징
- **스케줄링 단위**는 **Pod** (ReplicaSet, Deployment는 결국 Pod 단위로 처리됨)
- **플러그인 구조**: Scheduling Framework를 통해 Custom Scheduler 구현 가능
- **다중 스케줄러 지원**: 기본 kube-scheduler 외에도, 사용자 정의 스케줄러를 함께 사용할 수 있음 (Pod spec에 `schedulerName` 지정)

## kubelet

### 개념

- **Kubelet**은 Kubernetes 클러스터의 각 **노드(Node)** 위에서 동작하는 핵심 에이전트임.
- PodSpec(파드의 스펙)을 받아 해당 노드에서 파드와 컨테이너가 정상적으로 실행되도록 보장하는 역할을 함.
- Control Plane의 **kube-apiserver**와 통신하며, 해당 노드 상태와 파드 상태를 지속적으로 보고함.

## Kube-proxy
### 개념
- **kube-proxy**는 Kubernetes 클러스터의 각 노드에서 실행되는 네트워크 컴포넌트임.
- Service 오브젝트를 구현하기 위해 **클러스터 내부 트래픽 라우팅**을 담당함.
- 쉽게 말해, **“Service → Pod” 트래픽이 잘 연결되도록 보장하는 네트워크 프록시**.

### 주요 역할

1. **Service 가상 IP 관리**
- Kubernetes Service는 고정된 ClusterIP를 갖지만, 실제 뒷단은 여러 Pod로 이루어짐.
- kube-proxy는 이 가상 IP로 들어온 요청을 실제 Pod로 전달해줌 (Load Balancing).

2. **트래픽 라우팅**
- iptables 또는 IPVS를 사용하여 서비스 트래픽을 적절한 파드로 분산.
- Round Robin, 랜덤 등 기본 로드밸런싱 수행.

3. **노드 간 통신 보장**
- 클러스터 내부 노드들이 Pod/Service 간에 통신할 수 있도록 네트워크 규칙을 관리.

## Pod

### 개념

- **Pod**는 Kubernetes에서 가장 작은 배포 단위이자 실행 단위.
- 하나 이상의 **컨테이너(Container)** 를 묶어서 **동일한 네트워크 네임스페이스(IP, 포트)** 와 **스토리지 볼륨**을 공유하는 단위.
- Pod 내부의 컨테이너들은 **로컬호스트(localhost)** 로 통신 가능.
- Pod는 보통 하나의 애플리케이션을 감싸지만, **사이드카 패턴**처럼 보조 컨테이너를 함께 두기도 함.

### 특징

1. **공유 리소스**
- **네트워크**: Pod 안 컨테이너들은 같은 IP를 공유.
- **스토리지**: Pod 안 컨테이너는 같은 Volume을 공유 가능.
- **환경 설정**: 같은 PodSpec으로 설정된 리소스 제한, Secret, ConfigMap 등을 공유.

2. **생명 주기**
- Pod는 자체적으로 유지되지 않고, 필요 시 **Controller** (예: Deployment, ReplicaSet, StatefulSet)가 관리.
- Pod 자체는 **휘발성(temporary)** 이라서 죽으면 그대로 사라짐.
- Controller가 정의된 스펙을 보고 새로운 Pod를 생성해서 보장.

3. **Pod 사용 패턴**
- **단일 컨테이너 Pod**: 가장 일반적. 하나의 앱만 실행.
- **멀티 컨테이너 Pod**: 보조 역할을 하는 사이드카(Container)와 함께 동작.
  - 예: Nginx(메인) + 로그 수집기(사이드카).

4. **명령어**
```sh
kubectl run nginx --image=nginx
kubectl get pods
kubectl describe pod {pod}
```

```sh

5. **YAML**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
spec:
  containers:
  - name: myapp
    image: nginx
    ports:
    - containerPort: 80
```

```sh
kubectl create -f pod-definition.yml
```
Pod-Spec을 정의한 파일을 `kubectl create`를 통해 Pod를 생성할수 있다.

### Practice Test - Pods
```sh
# Pod 개수 확인
kubectl get pods

# nginx 이미지로 Pod 생성
kubectl run nginx --image=nginx

# 다시 Pod 개수 확인
kubectl get pods

# newpods-* Pod의 이미지 확인
kubectl describe pod newpods-cp9kj

# webapp Pod 삭제
kubectl delete pod webapp

# redis Pod 편집
kubectl edit pod redis
```

## ReplicaSet

ReplicaSet은 **Kubernetes에서 Pod의 개수를 일정하게 유지하기 위한 리소스 오브젝트**다.
즉, 사용자가 지정한 수만큼 Pod가 항상 실행되도록 보장하는 역할을 한다.

### 주요 개념

- **Pod 복제 관리**
  특정 Pod의 개수가 부족하면 새로운 Pod를 생성하고, 많으면 불필요한 Pod를 삭제해서 **원하는 개수(Desired State)** 를 유지한다.
- **선언적 방식**
  `spec.replicas`에 원하는 Pod 개수를 선언하면, ReplicaSet이 지속적으로 실제 상태를 모니터링하고 조정한다.
- **Selector 기반 관리**
  `spec.selector`로 관리할 Pod를 선택한다. 해당 Selector와 일치하는 Pod들을 감시하면서 개수를 조정한다.
- **Self-healing**
  어떤 이유로 Pod가 삭제되거나 노드 장애가 발생하더라도 ReplicaSet이 자동으로 새로운 Pod를 재생성한다.

### 구조 (YAML 예시)

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
spec:
  replicas: 3   # 항상 유지할 Pod 개수
  selector:
    matchLabels:
      app: nginx
  template:     # Pod 템플릿 (ReplicaSet이 관리할 Pod의 정의)
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
```

- **replicas**: 유지할 Pod 개수 (Desired count)
- **selector**: 어떤 Pod를 관리할지 지정 (label 기반)
- **template**: Pod 생성 시 사용할 템플릿 정의

### ReplicaSet vs ReplicationController
- **ReplicationController(RC)** 는 ReplicaSet 이전 세대 리소스
- ReplicaSet은 **더 강력한 selector (matchExpressions 등)** 를 지원
- 현재는 **ReplicaSet이 RC를 대체**한 상태

## ReplicaSet Scaling

ReplicaSet은 Pod의 개수를 보장하기 때문에, **scale 조정**을 통해 실행되는 Pod의 수를 늘리거나 줄일 수 있다.

###  `kubectl scale` 명령어
**scale 조정**을 통해 실행되는 Pod의 수를 늘리거나 줄일 수 있다.

```sh
kubectl scale replicaset <rs-name> --replicas=<개수>
```

### 막간으로 알아보는 명령어 차이점

| 명령어         | 리소스 없을 때 | 리소스 있을 때       | 특징                   | 사용 목적       |
| ----------- | -------- | -------------- | -------------------- | ----------- |
| **create**  | 새로 생성    | 에러 발생          | 단순 생성, idempotent 아님 | 처음 리소스 만들 때 |
| **apply**   | 새로 생성    | 변경 사항만 반영      | 선언적 관리, 가장 많이 사용     | 운영 환경 관리용   |
| **replace** | 새로 생성 가능 | 기존 리소스 삭제 후 생성 | 순간적 중단 가능, 완전 교체     | 리소스 갈아치울 때  |

### Practice Test - ReplicaSets
```sh
# Pod 목록 확인
kubectl get pods

# ReplicaSet 목록 확인
kubectl get replicasets

# 특정 ReplicaSet 상세 조회
kubectl describe replicaset new-replica-set

# 모든 Pod 상세 조회
kubectl describe pods

# 특정 Pod 삭제
kubectl delete pod new-replica-set-689gj

# 특정 ReplicaSet 삭제
kubectl delete replicaset replicaset-1

# ReplicaSet 편집
kubectl edit replicaset new-replica-set
# ⚠️ edit 후에는 기존 Pod을 모두 지워줘야 함
# (ReplicaSet은 Pod 템플릿을 자동 업데이트하지 않음)

# ReplicaSet 스케일링 (replica 수 변경)
kubectl scale replicaset new-replica-set --replicas=5
```

## Deployments

### 개념

* **Deployment**는 Kubernetes에서 애플리케이션을 배포하고 관리하기 위한 상위 개념의 리소스임
* ReplicaSet을 자동으로 생성하고 관리하며, Pod의 선언적(Declarative) 업데이트를 제공함
* 무중단 배포(rolling update), 이전 상태로의 롤백(rollback) 등 배포 전략을 쉽게 적용할 수 있음

### 주요 기능

* **Pod/ReplicaSet 관리**

  * 원하는 수의 Pod를 항상 유지 (self-healing)
  * ReplicaSet을 생성/교체하여 애플리케이션 버전을 관리
* **Rolling Update**

  * 새로운 버전으로 점진적으로 교체 → 서비스 중단 최소화
* **Rollback**

  * 문제가 생기면 이전 버전으로 손쉽게 되돌릴 수 있음
* **Declarative Update**

  * yaml(manifest) 파일에 원하는 상태를 선언하면, Kubernetes가 실제 상태를 그에 맞게 조정

### 동작 방식

1. 사용자가 Deployment 객체를 생성하면, Kubernetes가 해당 Deployment에 맞는 **ReplicaSet**을 생성
2. ReplicaSet은 정의된 수만큼의 Pod을 생성하고 유지
3. Deployment를 수정하면 새로운 ReplicaSet이 생성되고, **Rolling Update** 방식으로 기존 ReplicaSet의 Pod을 점진적으로 교체
4. 문제가 생기면 Deployment는 자동으로 **Rollback** 가능

### Practice Tests - Deployments
```sh
kubectl get all

kubectl describe deployment frontend-deployment
```

## Kubernetes Services

Service는 Pod들을 네트워크 상에서 안정적으로 접근할 수 있도록 해주는 추상화 객체임.

Pod는 동적으로 생성·삭제되기 때문에 IP가 고정되지 않음 → 이 문제를 해결하기 위해 Service가 고정된 접근점(가상 IP, DNS 이름)을 제공함.

### 주요 개념

* Pod 집합에 대한 **추상화된 네트워크 엔드포인트**
* **Label Selector**를 사용해 어떤 Pod들을 대상으로 할지 정의함
* 클러스터 내부/외부에서 Pod에 안정적으로 접근 가능
* 각 Service는 ClusterIP(가상 IP)를 가짐

### Service 타입

* **ClusterIP (기본값)**
  * 클러스터 내부에서만 접근 가능한 가상 IP를 부여함
  * 외부에서는 접근 불가

* **NodePort**
  * 각 노드의 특정 포트를 열어서 외부 접근을 허용함
  * `NodeIP:NodePort` 형태로 접근

* **LoadBalancer**
  * 클라우드 환경에서 외부 로드밸런서를 자동 생성
  * 외부에서 접근 가능한 공인 IP 제공
  * CSP나 LoadBalancer를 사용할수 있돌고 설정된 환경에서만 사용 가능

* **ExternalName**
  * 클러스터 외부의 DNS 이름을 그대로 서비스로 매핑
  * 실제 외부 서비스와 연결할 때 사용

### 동작 방식

1. 사용자가 Service에 요청 →
2. kube-proxy가 요청을 받아 적절한 Pod으로 트래픽을 라우팅
3. Pod이 교체되거나 IP가 바뀌어도 Service IP는 고정되어 안정적인 접근 가능

### Practice Test - Services
```sh
kubectl get services

kubectl describe service kubernetes
```

## Namespace
- Kubernetes의 Namespace는 클러스터 내부의 리소스를 논리적으로 구분하기 위한 가상 공간
- 하나의 클러스터를 여러 개의 가상 클러스터처럼 나누어 사용할 수 있게 해줌

### 특징
* 클러스터 내 리소스를 논리적으로 분리함 → 팀/환경별(개발/운영 등)로 자원을 격리 가능
* 리소스 이름은 Namespace 단위로 고유해야 함 (즉, 같은 이름의 Pod도 다른 Namespace에서 생성 가능)
* 기본적으로 `default`, `kube-system`, `kube-public` 등의 Namespace가 제공
* 네트워크적으로 완전히 차단되는 것은 아니고, **논리적 분리** (네트워크 정책으로 격리 가능)
* RBAC(Role-Based Access Control), ResourceQuota 등과 결합해 팀/사용자별 리소스 관리에 활용

### 기본 Namespace 종류
* **default**: 별도 지정하지 않으면 생성되는 리소스가 속하는 기본 Namespace
* **kube-system**: Kubernetes 시스템 컴포넌트(Pod, DNS 등)가 동작하는 공간
* **kube-public**: 모든 사용자가 접근할 수 있는 Namespace, 주로 클러스터 정보 공개용

### 자주 쓰는 명령어

* 모든 Namespace 조회

  ```sh
  kubectl get namespaces
  ```
* 특정 Namespace에 속한 Pod 조회

  ```sh
  kubectl get pods -n <namespace-name>
  ```
* 리소스를 생성할 때 Namespace 지정

  ```sh
  kubectl create deployment nginx --image=nginx -n dev
  ```
* 현재 Context의 기본 Namespace 변경

  ```sh
  kubectl config set-context --current --namespace=dev
  ```

### 활용 예시

* **개발/테스트/운영 환경 분리**: dev, stage, prod 네임스페이스 생성
* **팀 단위 격리**: frontend, backend, data-team 등으로 구분
* **리소스 관리**: 팀별로 CPU/메모리 할당량을 `ResourceQuota`로 제한

### 접속 규칙

  * 같은 Namespace 내: `db-service`
  * 다른 Namespace 접근 시: `db-service.dev.svc.cluster.local`

### Practice Test - Namespaces

```sh
# namespace 개수 확인
kubectl get namespaces | wc -l
kubectl get namespaces --no-headers | wc -l   # header 제외

# 특정 namespace의 pod 조회
kubectl get pods --namespace=research

# 특정 namespace에 pod 생성
kubectl run redis --image=redis --namespace=finance

# 모든 namespace에서 특정 pod 찾기
kubectl get pods --all-namespaces | grep blue
kubectl get pod blue --all-namespaces
```

## Imperative vs Declarative (명령형 vs 선언형)

### Imperative

* 관리자가 **명령형으로 직접 지시**하는 방식
* `kubectl` 명령어로 리소스를 바로 생성, 수정, 삭제
* 현재 상태를 "명령"으로 바로 반영
* 예시

  ```sh
  kubectl run nginx --image=nginx
  kubectl create deployment myapp --image=nginx
  kubectl delete pod mypod
  ```

### Declarative

* 관리자가 **원하는 최종 상태를 정의(YAML/JSON)**
* Kubernetes가 현재 상태(Current State)를 최종 상태(Desired State)에 맞게 조정
* `kubectl apply -f` 명령어를 사용해 선언적 관리
* 협업, 버전 관리, 재현성에 유리
* 예시

  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: myapp
  spec:
    replicas: 3
    selector:
      matchLabels:
        app: myapp
    template:
      metadata:
        labels:
          app: myapp
      spec:
        containers:
        - name: nginx
          image: nginx
  ```

  ```sh
  kubectl apply -f deployment.yaml
  ```

### 비교

| 구분  | Imperative                                        | Declarative        |
| --- | ------------------------------------------------- | ------------------ |
| 방식  | 명령으로 즉시 실행                                        | 최종 상태를 정의          |
| 사용법 | `kubectl run`, `kubectl create`, `kubectl delete` | `kubectl apply -f` |
| 장점  | 빠르고 단순                                            | 재현성, 협업, 버전 관리     |
| 단점  | 기록/재현 어려움                                         | 초기 세팅 번거로움         |

---

### 자주 쓰는 Imperative 명령어

```sh
# Pod 생성
kubectl run nginx --image=nginx 

# Deployment 생성
kubectl create deployment nginx --image=nginx 

# Deployment를 Service로 노출 (ClusterIP 기본)
kubectl expose deployment nginx --port=80

# Deployment 편집
kubectl edit deployment nginx

# Deployment 스케일 조정 (replicas=5)
kubectl scale deployment nginx --replicas=5

# Deployment의 컨테이너 이미지 업데이트
kubectl set image deployment nginx nginx=nginx:1.18
```

### Tips & Tricks
```sh
# yaml 파일로 생성
kubectl create deployment --image=nginx nginx --dry-run=client -o yaml
```

### Practice Test - Imperative Commands
```sh
kubectl run nginx-pod --image=nginx:alpine

# dry-run으로 yaml 파일 생성
kubectl run redis --image=redis:alpine --dry-run=client -oyaml > redis-pod.yaml
# 혹은
kubectl run redis -l tier=db --image=redis:alpine

kubectl expose pod redis --port=6379 --name=redis-service --type=ClusterIP

kubectl create deployment webapp --image=kodekloud/webapp-color --replicas=3

kubectl run custom-nginx --imag=nginx --port=8080

kubectl create namespace dev-ns

kubectl create deployment redis --namespace=dev-ns --image=redis

kubectl run httpd --image=httpd:alpine --port=80 --expose
```

## kubectl apply 동작 방식 (3-way merge)

| 구분                             | 설명                                                                                              | 예시                               |
| ------------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------- |
| **Local file**                 | 사용자가 적용하려는 매니페스트(YAML/JSON)                                                                     | `replicas: 3, image: nginx:1.18` |
| **Last applied configuration** | 이전에 `kubectl apply` 했을 때 저장된 설정 (`kubectl.kubernetes.io/last-applied-configuration` annotation) | `replicas: 2, image: nginx:1.17` |
| **Live object configuration**  | 현재 클러스터에 존재하는 리소스의 실시간 상태                                                                       | `replicas: 5, image: nginx:1.17` |

### 동작 방식

* `apply` 실행 시 세 값을 비교하여 **3-way merge** 수행
* Local ↔ Last 차이를 반영
* Last ↔ Live 비교하여 사용자가 변경하지 않은 필드는 유지
* 최종적으로 변경된 부분만 Live object에 업데이트


### 왜 Imperative와 Declarative를 섞으면 안 되는가

#### Declarative (`kubectl apply`)

* YAML 파일을 **진리의 원천(Single Source of Truth)** 으로 삼음
* 상태를 파일에 기록해 두고, 이를 기준으로 클러스터 상태를 유지
* 변경 사항이 `last-applied-configuration` 에 기록됨

#### Imperative (`kubectl edit`, `kubectl scale`, `kubectl set image` 등)

* 클러스터 상태를 직접 수정
* 하지만 `last-applied-configuration` 에는 반영되지 않음

#### 문제점

* Declarative(`apply`)는 Local ↔ Last ↔ Live 비교를 하는데, Imperative 변경은 Last에 기록되지 않음
* 그 결과, 다음 `apply` 시

  * Local과 Last 차이가 없다고 판단 → Imperative로 바꾼 값이 덮어써짐
  * 즉, **수정 내용이 사라지거나 의도치 않게 롤백됨**
