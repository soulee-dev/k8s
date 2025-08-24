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