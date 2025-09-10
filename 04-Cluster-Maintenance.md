# Cluster Maintenance

## OS Upgrades

Kubernetes 환경에서 노드 OS 업그레이드 시 고려해야 할 동작 원리와 절차 정리

### Pod Eviction Timeout

* 노드가 **5분 이상 다운**되면(기본 pod-eviction-timeout) 해당 노드에 있던 파드가 다른 노드에서 새로 생성됨
* 만약 노드가 timeout 이후에 복귀하면, 해당 노드는 \*\*빈 상태(blank)\*\*가 됨

### 빠른 업그레이드 & 재부팅

* 워크로드가 ReplicaSet 등으로 다른 노드에 복제본이 존재한다면, **짧은 시간 내 업그레이드 및 재부팅**은 문제 없음
* 하지만 업그레이드 시간이 **5분 이상 소요될지 불확실하다면**, 안전한 절차 필요

### 안전한 절차: Drain

노드를 유지보수 모드로 전환해 파드가 안전하게 옮겨지도록 처리

```sh
kubectl drain node-1
```

* 해당 노드의 파드가 **graceful termination** 후 다른 노드에서 새로 생성
* 동시에 노드는 \*\*cordon 상태(unschedulable)\*\*로 전환됨 → 새로운 파드는 해당 노드에 스케줄되지 않음

### Uncordon

업그레이드 및 재부팅 후, 다시 파드가 스케줄될 수 있도록 노드를 활성화

```sh
kubectl uncordon node-1
```

* 하지만 기존 파드가 자동으로 다시 이 노드로 옮겨오지는 않음

### Cordon

노드를 일시적으로 스케줄 불가능 상태로만 표시 (파드 종료 없음)

```sh
kubectl cordon node-1
```

* 단지 새로운 파드가 스케줄되지 않게 막을 뿐, 기존 파드는 그대로 유지됨

### Practice Test - OS Upgrades
```sh
# Pod이 떠있는 Node 확인
kubectl get pods -o wide

kubectl drain node01 --ignore-daemonsets

kubectl uncordon node01
```

## Cluster Upgrade Process

### 버전 규칙

* Kubernetes 구성 요소 간에는 버전 호환 규칙이 있음
* **kube-apiserver**가 항상 가장 높은 버전이어야 함
* **controller-manager, kube-scheduler** → kube-apiserver보다 최대 **1 버전 낮을 수 있음**
* **kubelet, kube-proxy** → kube-apiserver보다 최대 **2 버전 낮을 수 있음**
* **kubectl** → kube-apiserver와 **동일 / 1 버전 낮음 / 1 버전 높음** 모두 가능
* Kubernetes는 **최대 3개의 minor version**까지만 지원
* **권장**: 한 번에 한 minor version씩 업그레이드

### 업그레이드 방법

* Managed Kubernetes (EKS, GKE, AKS 등): CSP에서 제공하는 UI/CLI로 몇 번의 클릭만으로 업그레이드 가능
* Self-managed Kubernetes: **kubeadm**을 사용해 업그레이드 계획 수립 및 실행

### 업그레이드 절차

1. **Master Node 업그레이드**
2. **Worker Node 업그레이드**

### 업그레이드 전략

1. **모든 노드를 동시에 업그레이드**

   * 빠름
   * 클러스터 전체가 다운됨 (다운타임 발생)

2. **한 번에 하나의 노드 업그레이드**

   * 안전함
   * 워크로드는 다른 노드로 스케줄링됨
   * 다운타임 없음

3. **새 버전 노드를 추가 배포 후 기존 노드 제거**

   * 특히 클라우드 환경에서 유용
   * Blue/Green 방식처럼 새 인프라로 점진적 전환 가능

### Master Node 업그레이드

```sh
# 업그레이드 계획 확인
kubeadm upgrade plan

# kubeadm 업그레이드
apt-get upgrade -y kubeadm=1.12.0-00

# master 업그레이드 실행
kubeadm upgrade apply v1.12.0

# kubelet 업그레이드
apt-get upgrade -y kubelet=1.12.0-00
systemctl restart kubelet
```

### Worker Node 업그레이드

```sh
# 노드 drain (Pod 다른 노드로 이동)
kubectl drain node-1

# kubeadm & kubelet 업그레이드
apt-get upgrade -y kubeadm=1.12.0-00
apt-get upgrade -y kubelet=1.12.0-00

# kubelet 설정 반영
kubeadm upgrade node config --kubelet-version v1.12.0
systemctl restart kubelet

# 노드 다시 스케줄 가능 상태로 변경
kubectl uncordon node-1
```

### Practice Test - Cluster Upgrade Process
```sh
kubectl get nodes
kubectl describe node controlplane | grep -i taint

kubeadm upgrade plan

kubectl drain controlplane --ignore-daemonsets
```

## Backup and Restore Methods

### Backup 대상

* **Resource Configurations**: 클러스터에 정의된 모든 리소스 매니페스트
* **Etcd Cluster**: Kubernetes의 핵심 데이터 저장소
* **Persistent Volumes**: 실제 애플리케이션 데이터 저장소

---

### Resource Configurations

* 클러스터의 Deployment, Service, ConfigMap 등은 선언형 리소스 정의(YAML)로 백업 가능
* **Best Practice**: 리소스 매니페스트를 GitHub 같은 소스코드 저장소에 보관
* 예시 명령어:

  ```sh
  kubectl get all --all-namespaces -o yaml > all-deploy-services.yaml
  ```
* **도구**: Velero → 리소스 및 볼륨 스냅샷을 클라우드 스토리지에 백업 및 복원 가능

---

### Etcd

* Kubernetes의 상태 데이터는 etcd에 저장됨
* etcd 데이터 디렉토리: `--data-dir` 옵션으로 지정됨
* **스냅샷 기능 내장**

  * 수동 스냅샷:

    ```sh
    ETCDCTL_API=3 etcdctl snapshot save snapshot.db
    ```
  * 복원:

    ```sh
    ETCDCTL_API=3 etcdctl snapshot restore snapshot.db
    ```
* etcdctl 사용 시 반드시 인증 관련 플래그(`--endpoints`, `--cert`, `--key`, `--cacert`) 설정 필요

---

### Persistent Volumes

* 앱의 데이터가 실제로 저장되는 영역 → 단순히 매니페스트만 저장하면 복원 불가
* **백업 방식**

  * 스토리지 제공자가 지원하는 스냅샷 기능 사용 (예: AWS EBS snapshot, Ceph RBD snapshot 등)
  * Velero 같은 도구 활용 → PV 데이터를 외부 스토리지에 백업 가능

### Practice Test - Backup and Restore Methods
```sh
etcdctl --endpoints=https://127.0.0.1:2379 \
--cacert=/etc/kubernetes/pki/etcd/ca.crt \
--cert=/etc/kubernetes/pki/etcd/server.crt \
--key=/etc/kubernetes/pki/etcd/server.key \
snapshot save /opt/snapshot-pre-boot.db

etcdutl snapshot restore /opt/snapshot-pre-boot.db --data-dir /var/lib/etcd-from-backup

watch crictl ps
```