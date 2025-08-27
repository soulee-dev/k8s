# Manual Scheduling

## 개념

* Kubernetes에서 기본적으로 Pod는 **kube-scheduler**가 자동으로 노드를 선택해 배치함
* Manual Scheduling은 관리자가 **직접 노드를 지정**하는 방식임
* 주로 학습이나 테스트용으로 사용됨

---

## 방법 1. Pod 생성 시 `nodeName` 지정

Pod 생성 시 `spec.nodeName`을 지정하면, 스케줄러를 거치지 않고 바로 해당 노드에 스케줄링됨

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-manual
spec:
  containers:
  - name: nginx
    image: nginx
  nodeName: node01   # 수동 지정
```

특징

* 잘못된 노드명을 넣으면 Pod는 `Pending` 상태 유지
* 운영 환경에서는 `nodeSelector`, `affinity`, `taints/tolerations` 같은 정책 기반 방식이 선호됨

---

## 방법 2. 이미 생성된 Pod 스케줄링 (Binding API)

* Pod의 `spec.nodeName`은 **immutable** → 생성된 후에는 수정 불가
* `Pending` 상태의 Pod를 특정 노드에 붙이려면 **Binding API**를 사용해야 함

예시 (binding.yaml)

```yaml
apiVersion: v1
kind: Binding
metadata:
  name: nginx   # 바인딩할 Pod 이름
target:
  apiVersion: v1
  kind: Node
  name: node01  # 할당할 노드
```

적용

```sh
kubectl create -f binding.yaml --namespace=default
```

REST API 호출 예시

```sh
curl -X POST \
  -H "Content-Type: application/json" \
  --data '{
    "apiVersion": "v1",
    "kind": "Binding",
    "metadata": { "name": "nginx" },
    "target": {
      "apiVersion": "v1",
      "kind": "Node",
      "name": "node01"
    }
  }' \
  http://$APISERVER/api/v1/namespaces/default/pods/nginx/binding
```

## Practice Test - Manual Scheduling
```sh
kubectl get pods --namespace=kube-system
```

# Labels & Selectors

## Labels

* key=value 형식의 메타데이터임
* Pod, Node, Service, Deployment 등 Kubernetes 리소스에 붙일 수 있음
* 목적: 리소스를 그룹화하거나 구분할 수 있도록 태깅
* 예시

  ```yaml
  metadata:
    labels:
      app: nginx
      env: dev
  ```

## Selectors

* 특정 label을 가진 리소스를 선택하는 방법임
* Controller(ReplicaSet, Deployment 등)나 Service가 Pod를 선택할 때 사용됨
* 종류

  1. **Equality-based**

     * `=` , `==` , `!=` 사용
     * 예: `app=nginx`, `env!=prod`
  2. **Set-based**

     * `in`, `notin`, `exists` 사용
     * 예: `env in (dev,qa)`, `tier notin (frontend)`, `app` (exists)

## 사용 예시

* **Service가 Pod 선택**

  ```yaml
  kind: Service
  metadata:
    name: nginx-service
  spec:
    selector:
      app: nginx
    ports:
      - port: 80
  ```

  → label `app=nginx` 을 가진 Pod에 트래픽 전달

* **ReplicaSet이 Pod 관리**

  ```yaml
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
  ```

## Practice Test - Labels and Selectors
```sh
kubectl get pods --selector env=dev --no-headers | wc -l
kubectl get pods --selector bu=finance --no-headers | wc -l
kubectl get pods --selector env=prod,bu=finance,tier=frontend
```

# Taints & Tolerations

## 개념

* **Taints (Node 단위)**: 특정 조건의 Pod가 해당 Node에 **스케줄되지 못하게 제한**
* **Tolerations (Pod 단위)**: 특정 Taint를 **허용**하여 Node에 스케줄 가능

👉 Node는 Taint로 Pod를 **거부(push)**, Pod는 Toleration으로 Node를 **허용(accept)**

## Taint 형식

```
key=value:effect
```

* **Effect 종류**

  * `NoSchedule`: Toleration 없으면 스케줄 불가
  * `PreferNoSchedule`: 가능하면 스케줄 피함 (soft)
  * `NoExecute`: 기존 Pod도 퇴출(evict)

## 명령어 예시

```sh
# Node에 taint 추가
kubectl taint nodes node1 key=value:NoSchedule

# Node의 taint 확인
kubectl describe node node1 | grep Taint
```

## Pod 예시 (toleration)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
  - name: mycontainer
    image: nginx
  tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
```

## kubemaster와 Taints

* Kubernetes 설치 시, **Master Node(제어 플레인)** 에는 기본적으로 다음과 같은 taint가 적용됨:

  ```
  node-role.kubernetes.io/control-plane:NoSchedule
  ```

  (구버전에서는 `node-role.kubernetes.io/master:NoSchedule`)

* 의미: Master Node에는 일반 Pod이 스케줄되지 않도록 막음

* 이유: Master Node는 API 서버, etcd, 컨트롤러 등 **클러스터 관리용 프로세스**를 실행하기 때문에, 일반 workload가 올라가면 안정성이 떨어질 수 있음

## Pradctice Test - Taints and Tolerations
```sh
kubectl get nodes

kubectl taint nodes node01 spray=mortein:NoSchedule

kubectl taint nodes controlplane node-role.kubnernetes.io/control-plane:NoSchedule-
```

# Node Selectors

## 개념

* `nodeSelector`는 파드가 특정 노드에 스케줄링되도록 제한하는 가장 기본적인 방법임
* 파드의 `spec.nodeSelector` 필드에 **key-value 형태의 라벨 조건**을 지정하면, 해당 라벨을 가진 노드에만 파드가 배치됨
* 단순 매칭만 가능 (`=`, `!=` 같은 복잡 조건 불가)

---

## 동작 방식

1. 노드에 라벨을 먼저 설정해야 함

   ```sh
   kubectl label nodes <노드명> disktype=ssd
   ```
2. 파드 YAML에서 nodeSelector 추가

   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: nginx-pod
   spec:
     containers:
       - name: nginx
         image: nginx
     nodeSelector:
       disktype: ssd
   ```
3. 스케줄러는 `disktype=ssd` 라벨이 붙은 노드 중 하나를 선택해 파드를 배치

# Node Affinity

## 개념

* Node Affinity는 **Pod를 특정 Node에 스케줄링하기 위한 규칙**임
* `nodeSelector`의 확장된 기능으로, **더 풍부한 표현식**을 지원하고 **soft/hard 제약 조건**을 설정할 수 있음
* `labels`를 기반으로 동작하며, Node가 가진 Label과 Pod가 요구하는 조건이 일치할 때 해당 Node에 스케줄링됨

---

## 종류

### 1. `requiredDuringSchedulingIgnoredDuringExecution`

* 반드시 조건을 만족해야 Pod가 Node에 배치됨 (hard requirement)
* 조건이 만족되지 않으면 Pod는 스케줄되지 못함

### 2. `preferredDuringSchedulingIgnoredDuringExecution`

* 조건을 만족하는 Node에 우선 배치되지만, 조건을 만족하지 않아도 다른 Node에 배치 가능 (soft requirement)

---

## 특징

* `IgnoredDuringExecution`은 실행 중에는 Node Label이 바뀌더라도 Pod는 그대로 실행됨
* (추가 기능으로 향후 `requiredDuringExecution` 같은 타입이 도입될 수 있음 → 아직 일반적으로 사용되지 않음)

---

## 예시

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:   # 하드 제약
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
      preferredDuringSchedulingIgnoredDuringExecution:  # 소프트 제약
      - weight: 1
        preference:
          matchExpressions:
          - key: region
            operator: In
            values:
            - us-east-1
  containers:
  - name: nginx
    image: nginx
```

* `requiredDuringSchedulingIgnoredDuringExecution`: `disktype=ssd` 라벨이 있는 노드에서만 실행
* `preferredDuringSchedulingIgnoredDuringExecution`: 가능하다면 `region=us-east-1` 노드를 선호

---

## Operator 종류

* `In`: 특정 값 중 하나와 일치해야 함
* `NotIn`: 특정 값과 일치하지 않아야 함
* `Exists`: 해당 key가 존재해야 함
* `DoesNotExist`: 해당 key가 없어야 함
* `Gt`, `Lt`: 숫자 비교

---

## Node Selector와 비교

| 특징    | Node Selector   | Node Affinity                          |
| ----- | --------------- | -------------------------------------- |
| 표현식   | key=value 단순 매칭 | In, NotIn, Exists, Gt, Lt 등 다양한 표현식 지원 |
| 조건 종류 | hard 조건만 가능     | hard + soft 조건 모두 가능                   |
| 유연성   | 낮음              | 높음                                     |

## Practice Test - Node Affinity
```sh
kubectl label node node01 color=blue

kubectl create deployment blue --image=nginx --replicas=3

kubectl describe node controlplane | grep -i taints

kubectl get pods -o wide
```

# Taints & Tolerations vs Node Affinity

## Taints & Tolerations

* 특정 Node에 **Pod가 배치되지 않도록 차단(taint)** + 예외 허용(toleration)
* Node에 `taints` 설정
* Pod Spec에 `tolerations` 설정
* 원리

  * Node에 taint가 있으면 해당 Node에 Pod는 기본적으로 스케줄링 불가
  * Pod에 대응하는 toleration이 있으면 스케줄링 가능

## Node Affinity

* 특정 Node에 **Pod가 배치되도록 유도**하는 스케줄링 제약 조건
* Pod Spec에 `affinity.nodeAffinity` 설정
* 종류

  * **requiredDuringSchedulingIgnoredDuringExecution**: 반드시 만족해야 배치 가능
  * **preferredDuringSchedulingIgnoredDuringExecution**: 만족하면 우선 배치, 불만족 시 다른 Node에도 가능
* 보통 `nodeSelector`의 확장된 형태 (연산자 In, NotIn, Exists 등 지원)

## 차이점 비교

| 구분    | Node Affinity                 | Taints & Tolerations         |
| ----- | ----------------------------- | ---------------------------- |
| 목적    | 특정 Node **로 보내기**             | 특정 Node **에서 막기**            |
| 적용 위치 | Pod → Node로 조건 검사             | Node → Pod 차단, Pod이 예외적으로 허용 |
| 제어 방식 | 스케줄러의 배치 정책                   | 스케줄러+Kubelet에서 실행 차단         |
| 강제성   | required: 반드시, preferred: 우선권 | toleration 없으면 절대 불가         |

## 같이 사용하는 경우

* **Node Affinity**는 “가야 하는 곳”을 정의
* **Taints & Tolerations**는 “못 가는 곳”을 정의

예시 시나리오:

1. 특정 Node에 `taint=nodeType=gpu:NoSchedule` 설정 → 일반 Pod은 배치 불가
2. GPU 작업을 하는 Pod에 `tolerations` 추가 → GPU Node에도 배치 가능
3. 동시에 Pod에 `nodeAffinity`를 `nodeType=gpu` 로 설정 → 스케줄러가 GPU Node를 반드시 선택
   → 결과적으로 해당 Pod는 **GPU Node에만 스케줄링**됨

즉,

* Node Affinity는 **긍정적 선택(어디로 가야 하는가)**
* Taints & Tolerations는 **부정적 필터링(어디는 못 간다, 허용해야만 가능)**
* 두 개를 함께 쓰면 Pod 배치 제어를 더 정밀하게 할 수 있음

# Resource Requirements, Limits, Quotas

## Resource Requirements & Limits 개념

Pod/Container는 CPU와 Memory 같은 리소스를 사용함.
Kubernetes는 스케줄링, 성능 보장, 안정성을 위해 `requests`와 `limits` 두 가지 개념을 사용함.

* **requests**

  * 최소한 보장받을 리소스 양
  * 스케줄러가 Pod를 어느 노드에 배치할지 결정할 때 기준으로 사용됨
  * 예: `cpu: 500m`, `memory: 256Mi` → 노드에 이 정도 리소스 여유가 있어야 배치됨

* **limits**

  * 해당 컨테이너가 사용할 수 있는 최대치
  * CPU: cgroups를 통해 제한. 초과 시 throttling (속도 조절) 발생
  * Memory: cgroups를 통해 제한. 초과 시 OOM(Out Of Memory) Kill 발생

---

## CPU / Memory 조합별 동작

| requests | limits | CPU 동작                                        | Memory 동작                                         | QoS Class                                              |
| -------- | ------ | --------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------ |
| 없음       | 없음     | 스케줄러 고려 없음, 남는 CPU 사용, 부족 시 쉽게 빼앗김            | 남는 메모리 사용, 부족 시 OOM Kill, 최저 우선순위                 | **BestEffort**                                         |
| 없음       | 있음     | 스케줄러 고려 없음, 실행 시 limit까지 사용, throttling 발생 가능 | limit까지 사용, 초과 시 OOM Kill                         | **Burstable**                                          |
| 있음       | 있음     | 스케줄러가 requests 기준으로 배치, 실행 시 limit까지 사용       | requests 기준으로 배치, limit까지 사용, 초과 시 OOM Kill       | requests == limits → **Guaranteed**, 아니면 **Burstable** |
| 있음       | 없음     | requests 기준으로 배치, limit 없어 남는 CPU 전부 사용 가능    | requests 기준으로 배치, limit 없어 무제한 사용 가능, 노드 전체 영향 가능 | **Burstable**                                          |


## QoS Class 정리

Kubernetes는 Pod의 리소스 정의 방식에 따라 **QoS Class**를 부여함.

| QoS Class  | 조건                                       |
| ---------- | ---------------------------------------- |
| Guaranteed | 모든 컨테이너가 CPU/Memory requests == limits   |
| Burstable  | requests는 있으나 limits와 다름, 혹은 일부 컨테이너만 설정 |
| BestEffort | 모든 컨테이너에 requests/limits 없음              |

---

## Resource Quotas

* Namespace 단위에서 리소스 사용량을 제한하는 정책
* 관리자가 여러 팀/서비스가 클러스터를 공유할 때 과도한 사용을 막기 위해 설정
* 예시:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "4"       # team-a 전체에서 최소 요청 CPU 합은 4 core까지만
    requests.memory: 8Gi
    limits.cpu: "10"        # team-a 전체에서 최대 사용 CPU 합은 10 core
    limits.memory: 16Gi
    pods: "20"              # Pod 개수 제한
```

* Pod가 생성될 때 Namespace의 quota와 비교하여 넘으면 생성 거부됨
* **LimitRange**와 함께 사용하면 각 Pod/Container가 기본 requests/limits를 강제 가능

## Practice Test - Resource Limits
```sh
kubectl get pod elephant -oyaml > elephant.yml
```

# DaemonSet

## 개념

* DaemonSet은 **클러스터의 모든(또는 특정) 노드에서 반드시 1개씩 실행되는 Pod**을 보장하는 리소스임.
* 주로 **노드 단위의 에이전트/데몬**을 배포할 때 사용됨.

  * 예: 로그 수집기(Fluentd, Filebeat), 모니터링 에이전트(Node Exporter), 네트워크 관리(CNI 플러그인) 등.

## 특징

* 새로 노드가 추가되면 자동으로 Pod을 배포함.
* 노드가 제거되면 해당 Pod도 같이 제거됨.
* 기본적으로 각 노드에 하나씩 Pod이 생성되지만, `nodeSelector`, `nodeAffinity`, `taints/tolerations` 등을 설정해서 특정 노드에만 배포 가능.
* Deployment처럼 ReplicaSet을 직접 생성하지 않고, **DaemonSet Controller**가 Pod을 직접 관리함.

## 내부 동작

* DaemonSet은 Pod 스케줄링을 **직접 하는 게 아니라**, 내부적으로는 **Default Scheduler**를 그대로 사용함.
* 다만 DaemonSet Controller가 Pod을 만들 때, 해당 노드에서만 실행되도록 **NodeAffinity**를 자동으로 추가함.

  * 예: `kubernetes.io/hostname=<노드명>` 형태의 **RequiredDuringSchedulingIgnoredDuringExecution** NodeAffinity 조건을 Pod에 붙임.
* 그 결과, 스케줄러는 해당 노드에서만 Pod을 실행하도록 강제됨.

## Practice Test - DaemonSets
```sh
kubectl get daemonsets --all-namespaces
kubectl describe daemonset kube-proxy --namepsace=kube-system
```

# Static Pods

## 개념

* **Static Pod**는 **kube-apiserver를 거치지 않고**, 특정 노드의 **kubelet이 직접 생성하고 관리하는 Pod**임
* 즉, Control Plane의 `kube-scheduler`가 개입하지 않고 노드 단위에서만 실행됨
* 각 노드에 개별적으로 정의해야 하며, 자동으로 ReplicaSet, Deployment 같은 고수준 오브젝트로 관리되지 않음

## 특징

* Pod의 상태는 `kube-apiserver`에 **mirror pod** 형태로 등록됨 (조회 가능)

  ```sh
  kubectl get pods -n kube-system
  ```

  → 이때 mirror pod는 수정 불가, 단순히 kubelet이 생성한 static pod의 상태를 보여주는 것임
* 노드가 죽으면 다른 노드에 스케줄링되지 않음 (일반 Pod와 다름)
* `kubelet`이 PodSpec YAML 파일을 직접 읽어서 실행

---

## 경로 설정 방법

Static Pod는 kubelet이 **`--pod-manifest-path`** 또는 **`--config`** 옵션으로 지정한 디렉토리에서 YAML 파일을 읽음

1. **kubelet 실행 옵션 확인**

   ```sh
   ps -ef | grep kubelet
   ```

   * 예시:

     ```
     --pod-manifest-path=/etc/kubernetes/manifests
     ```

2. **해당 경로에 YAML 배치**

   ```sh
   ls /etc/kubernetes/manifests
   ```

   * 여기 있는 모든 `.yaml` 파일을 kubelet이 읽고 Pod 생성

3. **예시: etcd static pod**

   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: etcd
     namespace: kube-system
   spec:
     containers:
     - name: etcd
       image: k8s.gcr.io/etcd:3.4.13-0
       command:
       - etcd
   ```

   → `/etc/kubernetes/manifests/etcd.yaml` 에 저장 시 자동 실행

---

## Use Case

1. **Control Plane 컴포넌트 실행**

   * `kubeadm`으로 클러스터를 구성하면
     `kube-apiserver`, `kube-scheduler`, `kube-controller-manager` 등은 **Static Pod** 형태로 `/etc/kubernetes/manifests`에 배치됨
   * 이유: API Server 자체가 뜨지 않은 상태에서도 Control Plane을 구동할 수 있어야 하기 때문

2. **Node 레벨 필수 데몬 실행**

   * 클러스터 관리자가 특정 노드에서 반드시 실행해야 하는 Pod (예: 로깅/모니터링 에이전트)

3. **API Server 다운 대비**

   * Control Plane이 죽었더라도 kubelet이 static pod를 계속 실행하여 복구 가능

## Practice Test - Static Pods
```sh
# Static pods는 pod 이름에 -<Node Name>이 붙는다
kubectl get pods --all-namespaces

# kubelet의 파라미터(설정)을 확인한다
ps -aux | grep kubelet
```

# PriorityClass

## 개념

* **PriorityClass**는 Kubernetes에서 Pod의 우선순위를 정의하는 리소스임
* 스케줄링 시 어떤 Pod을 먼저 배치할지 결정하거나, 리소스 부족 시 어떤 Pod을 먼저 축출(preemption)할지 결정하는 기준이 됨
* 기본적으로 Pod은 `priorityClassName`을 명시하지 않으면 우선순위 0으로 설정됨

## 동작 방식

1. **PriorityClass 리소스 생성**

   * `PriorityClass` 오브젝트를 만들어 우선순위 값(`value`)을 정의함
   * 값이 클수록 우선순위가 높음
   * `globalDefault`를 `true`로 설정하면, 우선순위가 지정되지 않은 Pod들이 이 클래스의 우선순위를 가짐

2. **Pod과 연결**

   * Pod spec에 `priorityClassName`을 명시
   * 스케줄러는 우선순위가 높은 Pod을 먼저 스케줄링 시도함

3. **Preemption (축출)**

   * 클러스터에 리소스가 부족해 Pod을 스케줄링할 수 없는 경우, 스케줄러는 낮은 우선순위 Pod을 축출하여 높은 우선순위 Pod을 배치함

## YAML 예시

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "High priority pods"
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: important-app
spec:
  priorityClassName: high-priority
  containers:
  - name: app
    image: nginx
```

## PreemptionPolicy

### 개념

* **PreemptionPolicy**는 Kubernetes Pod의 우선순위 기반 축출(preemption) 동작을 제어하는 속성임
* 기본적으로 Pod은 `PriorityClass`를 통해 우선순위를 갖고, 리소스 부족 시 스케줄러는 낮은 우선순위 Pod을 **축출(evict)** 해서 높은 우선순위 Pod을 배치함
* 이때 Pod의 스펙에서 `preemptionPolicy`를 설정해 축출 정책을 세밀하게 제어할 수 있음

### 설정 값

* `PreemptLowerPriority` (기본값)

  * 우선순위가 높은 Pod이 스케줄링될 수 없다면, 낮은 우선순위 Pod을 축출해서 자리를 마련함
  * 일반적으로 PriorityClass와 함께 사용하는 기본 동작

* `Never`

  * 이 Pod은 다른 Pod을 축출하지 않음
  * 즉, 이 Pod이 스케줄링될 때 리소스가 부족하더라도 기존 Pod들을 내쫓지 않고, 그냥 Pending 상태로 대기

## Practice Test - Priority Classes
```sh
kubectl get priorityclass

kubectl get pod critical-app -o yaml > critical-app.yaml
```