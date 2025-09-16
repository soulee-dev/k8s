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
