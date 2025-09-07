# Application Lifecycle Management

# Rolling Updates and Rollbacks

## Rollout과 버전 관리

* Deployment는 새로운 버전을 배포할 때마다 **revision**을 생성함
* 상태 확인

  ```sh
  kubectl rollout status deployment/myapp-deployment
  ```
* 배포 이력 확인

  ```sh
  kubectl rollout history deployment/myapp-deployment
  ```

## Deployment Strategy

* **Recreate**

  * 기존 Pod을 모두 종료 후 새 Pod 생성
  * 잠시 동안 서비스가 중단될 수 있음
  * 이벤트를 보면 기존 ReplicaSet이 0으로 스케일 다운되고 새로운 ReplicaSet이 원하는 수치(예: 5)로 스케일 업됨
* **Rolling Update (기본값)**

  * 기존 Pod을 하나씩 줄이면서 동시에 새 Pod을 하나씩 늘림
  * 무중단 배포 가능
  * 이벤트를 보면 old ReplicaSet이 하나 줄고, new ReplicaSet이 하나 증가하는 식으로 교차 진행됨

## Kubectl apply

* `kubectl apply`를 통해 매니페스트를 업데이트하면 Deployment의 **새로운 revision**이 생성됨
* 애플리케이션이 정상적으로 동작 중인지 여부는 rollout status나 Pod 상태를 통해 확인해야 함

## Rollback

* 문제가 생기면 이전 revision으로 되돌릴 수 있음

  ```sh
  kubectl rollout undo deployment/myapp-deployment
  ```

## 주요 명령어 요약

```sh
kubectl rollout status deployment/myapp-deployment    # 현재 rollout 상태 확인
kubectl rollout history deployment/myapp-deployment   # 배포 이력 확인
kubectl rollout undo deployment/myapp-deployment      # 이전 버전으로 롤백
```

## Practice Test - Rolling Updates and Rollbacks
```sh
# 페이지 내용이 너무 길떈 'less'명령어
kubectl describe deployment frontend | less
```

# Commands and Arguments in Docker
## CMD
- 기본 실행 명령어 정의
- 사용자가 run에서 인자를 주면 **덮어쓰기**됨

```dockerfile
FROM ubuntu
CMD ["sleep", "5"]
```

```sh
docker run ubuntu-sleeper

docker run ubuntu-sleeper sleep 10
```

## ENTRYPOINT
- 컨테이너 실행 시 항상 실행되어야 하는 **고정 실행 명령어**
- 사용자가 인자를 주더라도 ENTRYPOINT는 덮어쓰기 되지 않고 뒤에 인자로 붙음

```dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
```

```sh
docker run ubuntu-sleeper 5
```

## CMD + ENTRYPOINT
- ENTRYPOINT: 실행 파일 지정 (고정).
- CMD: ENTRYPOINT에 전달될 기본 인자(default arguments).
- 즉, docker run에서 아무 인자 안주면 CMD가 기본값으로 사용되고, 인자를 주면 CMD 대신 그 값이 사용됨