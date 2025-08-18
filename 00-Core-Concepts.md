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

