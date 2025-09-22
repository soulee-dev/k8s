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
