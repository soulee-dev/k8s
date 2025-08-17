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