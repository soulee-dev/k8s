# Monitor Cluster Components

클러스터 모니터링은 노드, 파드, 리소스 사용량을 추적하고 알림 및 시각화를 통해 상태를 관리하는 과정임. 주요 컴포넌트는 다음과 같음.

* **Metric Server**

  * Kubernetes 기본 컴포넌트로 CPU/메모리 사용량 같은 리소스를 수집
  * In-Memory 저장 방식 → 과거 데이터 저장 불가 (실시간 모니터링 전용)
  * `kubectl top node`, `kubectl top pod` 명령어로 확인 가능

* **Prometheus**

  * CNCF 프로젝트, 시계열(time-series) DB 기반 모니터링 시스템
  * Kubernetes 클러스터의 다양한 메트릭을 장기적으로 저장 및 쿼리 가능
  * Alertmanager와 Grafana와 통합해 알림 및 시각화 제공

* **Datadog**

  * SaaS 기반 모니터링/로깅/보안 플랫폼
  * Prometheus와 유사하게 메트릭 수집 및 대시보드 제공
  * 멀티클라우드, 하이브리드 환경에서 통합 모니터링 가능

# Managing Application Logs

## Docker Logging

* 컨테이너 애플리케이션은 기본적으로 **stdout**으로 로그 출력
* `docker run -d` → 백그라운드 실행, 로그는 직접 보이지 않음
* `docker logs <container-id>` → 로그 확인
* `docker logs -f <container-id>` → 실시간 로그 스트리밍

## Kubernetes Logging

* `kubectl logs <pod-name>` → pod 로그 확인
* `kubectl logs -f <pod-name>` → 실시간 로그 스트리밍
* Pod 안에 여러 컨테이너 존재 시:

  * `kubectl logs <pod-name> -c <container-name>` → 특정 컨테이너 로그 확인

## Practice Tests - Manaing Application Logs
```sh
kubectl logs webapp-1 | grep USER5

```