# Design and Install a Kubernetes Cluster
## Designing a Kubernetes Cluster

### 목적 (Purpose)

* **Education**

  * Minikube
  * 단일 노드 클러스터 (kubeadm / GCP / AWS)
* **Development & Test**

  * 멀티 노드 클러스터 (Single Master + 여러 Worker)
  * kubeadm 또는 GCP/AWS/AKS에서 빠른 프로비저닝
* **Production Hosting**

  * HA 멀티 노드 클러스터 (여러 Master + 여러 Worker)
  * kubeadm / GCP / kOps(AWS)
  * 규모: 최대 5000 노드, 150,000 Pods, 300,000 Containers, 노드당 100 Pods

---

### 클라우드 vs 온프레미스 (Cloud or On-Prem)

* **On-Prem** → kubeadm 사용
* **GCP** → GKE 사용
* **AWS** → EKS 사용

---

### 워크로드 고려 사항 (Workload Considerations)

#### Storage

* 고성능 SSD 백엔드 스토리지
* 네트워크 기반 스토리지 (동시 연결 지원)
* Persistent Shared Volumes (여러 Pod 공유 가능)
* 디스크 타입별 노드 라벨링
* NodeSelector로 특정 디스크 타입 노드에 워크로드 스케줄링

#### Nodes

* 물리/가상 머신 모두 가능
* 최소 4개 노드 구성 (워크로드에 따라 확장)
* Master vs Worker 구분
* Master 노드도 워크로드 실행 가능하지만, **Best Practice는 Master에 워크로드를 배치하지 않는 것**

---

### 설계 시 주요 질문

* **노드 수**: 몇 개를 둘 것인가? (최소 4개 이상 권장)
* **노드 타입**: VM / Bare-metal
* **애플리케이션 요구사항**: CPU, Memory, Storage
* **트래픽**: 예상 부하와 네트워크 요구사항

## Choosing Kubernetes Infrastructure

### 1. Local / Self-Managed 방식

* **Minikube**

  * 단일 노드 클러스터 실행
  * 주로 로컬 개발 및 테스트 용도
  * VM에 쿠버네티스 단일 클러스터 배포

* **Kubeadm**

  * 단일/멀티 노드 클러스터 구성 가능
  * VM/물리 서버 직접 준비 필요
  * 설치 및 설정을 수동으로 진행


### 2. Turnkey Solutions (반자동 배포)

* 특징

  * 사용자가 VM을 프로비저닝
  * VM 설정 및 클러스터 설치 스크립트 실행
  * VM 운영 및 유지보수 책임은 사용자
* 예시

  * **KOPS** (AWS 기반 쿠버네티스 배포)
  * OpenShift (Red Hat 기반)
  * Cloud Foundry Container Runtime
  * VMware Cloud PKS
  * Vagrant

### 3. Hosted Solutions (Managed Kubernetes)

* 특징

  * 클라우드 제공자가 VM 및 쿠버네티스 클러스터를 관리
  * 사용자는 애플리케이션 배포와 운영에 집중
  * 인프라 운영 부담 최소화
* 예시

  * **GKE** (Google Kubernetes Engine)
  * **EKS** (AWS Elastic Kubernetes Service)
  * **AKS** (Azure Kubernetes Service)
  * OpenShift Online

## Configure High Availability (HA)

### 마스터 노드 장애 시

* 기존에 실행 중인 컨테이너는 정상 동작함 (노드와 파드 단위 동작은 유지됨)
* 새로운 파드 생성/복구 불가 (컨트롤 플레인 동작 불가)
* `kubectl` 접속 불가 (API 서버 접근 불가)
* **단일 마스터 환경은 SPOF(Single Point of Failure)** → 반드시 다중 마스터 구성이 필요

### API Server

* Active-Active 모드로 동작 가능
* 외부에서 접근할 때는 **로드 밸런서**(nginx, HAProxy 등) 앞단 구성 필요

### Controller-Manager / Scheduler

* 동시에 여러 개가 실행될 수 없음 (Active-Standby) > 동시에 실행시 충돌 위험
* **리더 선출(Leader Election) 메커니즘** 사용

  * 기본 옵션

    * `--leader-elect-lease-duration=15s`
    * `--leader-elect-renew-deadline=10s`
    * `--leader-elect-retry-period=2s`
  * 하나가 리더가 되어 Lock을 획득하고 나머지는 대기

### Etcd

클러스터 상태 저장소 → 고가용성 핵심

* **Stacked topology** (마스터 노드에 etcd 포함)

  * 장점: 설정/관리 용이, 서버 수 적음
  * 단점: 마스터 장애 시 위험도 증가

* **External etcd topology** (마스터와 분리된 etcd 전용 클러스터)

  * 장점: 장애 내성이 강함, 더 안전
  * 단점: 구성 복잡, 서버 수 증가

* 설정 예시

  ```
  --etcd-servers=https://<etcd1>,https://<etcd2>,https://<etcd3>
  ```

  → 어느 etcd 서버든 읽기/쓰기 가능
