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