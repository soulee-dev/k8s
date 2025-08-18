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
