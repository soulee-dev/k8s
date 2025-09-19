# Storage
## Storage in Docker
### 기본 저장소 경로

* Docker의 모든 데이터는 기본적으로 `/var/lib/docker` 경로에 저장됨

  * `aufs` / `overlay2` : 스토리지 드라이버
  * `containers` : 실행 중인 컨테이너 데이터
  * `image` : 이미지 데이터
  * `volumes` : 볼륨 데이터

### Layered Architecture

* Docker 이미지는 **레이어 구조**로 구성됨
* `docker build` 시 `Dockerfile`의 각 명령어가 새로운 레이어를 형성
* 각 레이어는 이전 레이어의 **변경분만 저장**
* 캐시 재사용 가능 → **빌드 속도 향상, 저장 공간 절약**

#### 예시

```Dockerfile
FROM ubuntu       # Layer 1 (120MB)
RUN apt install   # Layer 2 (306MB)
RUN update pkg    # Layer 3 (6.3MB)
COPY src/ .       # Layer 4 (229B)
ENTRYPOINT ...    # Layer 5 (0B)
```

* 동일한 Dockerfile에서 **소스 코드만 변경** → 기존 레이어 재사용, 마지막 레이어만 새로 생성


### 컨테이너 실행 시 저장소 구조

* `docker run` 시 이미지 위에 **새로운 writable container layer**가 추가됨

  * 로그 파일, 임시 파일 등이 여기에 기록됨
  * 컨테이너가 삭제되면 이 레이어도 삭제됨
* 이미지 레이어는 **읽기 전용(read-only)**
* 소스 코드 수정 시 → 컨테이너 레이어에 복사(copy-on-write)

### Persistent Storage

#### 1. Docker Volume

* 도커가 직접 관리하는 볼륨
* `/var/lib/docker/volumes` 하위에 저장
* 컨테이너 실행 시 볼륨 마운트 가능

```sh
docker volume create data_volume
docker run -v data_volume:/var/lib/mysql mysql
```

#### 2. Bind Mount

* 호스트의 특정 디렉토리를 직접 마운트
* 경로 지정 방식

```sh
-v /data/mysql:/var/lib/mysql mysql
--mount type=bind,source=/data/mysql,target=/var/lib/mysql mysql
```

* 볼륨은 도커가 관리하는 영역,
* 바인드 마운트는 **호스트 디렉토리 직접 사용**

### Storage Drivers

Docker는 스토리지 드라이버를 이용해 레이어 시스템을 구현함

* `aufs`
* `zfs`
* `btrfs`
* `device mapper`
* `overlay`
* `overlay2` (권장, 최신 리눅스 기본)

> Docker는 자동으로 최적의 스토리지 드라이버를 선택

## Volume Driver Plugins in Docker

* **Volume과 Storage Driver의 차이**

  * Storage Driver: 컨테이너 이미지 계층 관리 (AUFS, overlay2 등)
  * Volume Driver: 컨테이너 데이터 볼륨 관리 (기본은 `local`)

* **기본 동작**

  * 기본 volume driver는 `local`
  * `local`은 `/var/lib/docker/volumes` 경로에 볼륨 생성

* **외부 플러그인 사용 가능**

  * 예: Azure File Storage, Convoy, GCE-Docker, RexRay(EBS) 등
  * 플러그인을 통해 외부 스토리지를 컨테이너 볼륨으로 사용 가능

* **사용 예시 (AWS EBS + rexray/ebs driver)**

  ```sh
  docker run -it \
    --name mysql \
    --volume-driver rexray/ebs \
    --mount src=ebs-vol,target=/var/lib/mysql \
    mysql
  ```

  * `--volume-driver`: 사용할 volume driver 지정
  * `--mount`: 외부 스토리지를 컨테이너 내부 특정 경로에 마운트

## Container Storage Interface (CSI)

* Kubernetes가 스토리지를 표준 방식으로 붙이기 위한 인터페이스임
* 스토리지 벤더가 **CSI 드라이버**만 제공하면, Kubernetes가 볼륨 생성/삭제와 Attach/Mount를 공통 방식으로 처리함
* Controller/Node 구성의 드라이버가 gRPC(RPC)로 요청을 처리해, 벤더 종속성을 줄이고 다양한 스토리지를 동일한 방식으로 사용할 수 있게 함

## Volumes

### Docker

* 컨테이너는 기본적으로 휘발성임
* 데이터를 유지하려면 볼륨을 사용해야 함
* 컨테이너가 삭제되어도 볼륨에 저장된 데이터는 남음

### Kubernetes

* Pod에 Volume을 붙여서 데이터 저장 가능
* 예시: `hostPath`

  * Pod 내부 `/opt`를 노드의 `/data`와 연결
  * 단일 노드 환경에서는 유효하지만, 멀티 노드에서는 한계가 있음

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: myapp
      image: alpine
      volumeMounts:
        - mountPath: /opt
          name: data-volume
  volumes:
    - name: data-volume
      hostPath:
        path: /data
        type: Directory
```

* 여러 노드 환경에서는 `hostPath` 대신 클라우드 스토리지나 네트워크 스토리지를 사용해야 함

  * AWS EBS (`awsElasticBlockStore`)
  * Ceph
  * NFS
  * Flocker
  * Fibre Channel
  * GlusterFS
  * ScaleIO

## Persistent Volumes (PV)

* 클러스터 전체에서 사용할 수 있는 스토리지 리소스
* 관리자가 미리 정의해둔 볼륨
* `spec`에 용량, 접근 모드, 스토리지 클래스, 실제 스토리지 백엔드(hostPath, NFS, EBS 등)를 지정

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-example
spec:
  accessModes:
    - ReadWriteOnce
  capacity:
    storage: 1Gi
  hostPath:
    path: /tmp/data
```

* `persistentVolumeReclaimPolicy`

  * **Retain**: 기본값, PV를 삭제해도 데이터는 유지 → 관리자가 수동으로 정리 필요
  * **Delete**: PVC 삭제 시 PV와 데이터까지 함께 삭제
  * **Recycle** (deprecated): 단순 초기화 후 재사용

---

## Persistent Volume Claims (PVC)

* 사용자가 필요로 하는 스토리지를 요청하는 리소스
* 클러스터 내 PV 중 조건에 맞는 것과 **1:1로 바인딩**됨

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
```

* 매칭 조건

  * 요청 용량
  * 접근 모드(ReadWriteOnce, ReadOnlyMany, ReadWriteMany)
  * 스토리지 클래스
  * 필요 시 Selector로 세부 지정 가능
* 작은 PVC라도 더 큰 PV에 바인딩될 수 있음 (부분 할당 불가 → 남은 용량은 다른 PVC가 사용 불가)
* 조건에 맞는 PV가 없으면 **Pending 상태**

---

### PVC를 Pod에서 사용하는 방법

* Pod → PVC → PV → 실제 스토리지
* Pod은 직접 PV를 참조하지 않고, PVC를 통해서만 접근

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
    - name: myfrontend
      image: nginx
      volumeMounts:
        - mountPath: "/var/www/html"
          name: mypd
  volumes:
    - name: mypd
      persistentVolumeClaim:
        claimName: myclaim
```

---

### 왜 Volume과 Claim을 나눠놨는가?

* **역할 분리**

  * PV: 관리자가 스토리지를 미리 준비하고 제공
  * PVC: 사용자가 스토리지를 요청
* **유연성 확보**

  * Pod이 특정 스토리지 구현(EBS, NFS 등)에 의존하지 않음 → Pod은 단순히 PVC만 참조
  * 스토리지 백엔드를 변경해도 Pod 정의는 수정할 필요 없음
* **멀티테넌시 지원**

  * 여러 사용자/팀이 PVC를 통해 공용 스토리지 풀(PV)을 안전하게 공유
* **동적 프로비저닝**

  * PVC 요청이 들어오면, 스토리지 클래스(StorageClass)에 따라 PV가 자동 생성 가능


## StorageClass

PersistentVolume를 사용할 때, 클라우드 환경에서는 기본적으로 수동으로 스토리지를 생성한 뒤 PersistentVolume에 연결해야 함 → 이를 **Static Provisioning**이라고 함.

**StorageClass**를 사용하면 PVC 요청 시 자동으로 클라우드 리소스를 생성하는 **Dynamic Provisioning**이 가능함.

### 특징

* PVC(PersistentVolumeClaim)를 만들면 StorageClass가 자동으로 해당 클라우드의 디스크/볼륨을 생성하여 바인딩함
* 프로비저너(`provisioner`)는 클라우드별 드라이버에 따라 다름
* 클라우드 제공자의 특성에 맞는 `parameters`를 설정할 수 있음 (예: SSD/HDD 타입, 리전, IOPS 등)

### 예시

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: google-storage
provisioner: kubernetes.io/gce-pd
```
