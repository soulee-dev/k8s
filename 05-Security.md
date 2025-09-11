# Security
## Authentication

### Accounts

* **User Accounts**: 실제 사용자 (Admin, Developer 등)
* **Service Accounts**: 클러스터 내 애플리케이션/Pod에서 사용하는 계정 (Bot 등)

> Kubernetes 자체적으로 User를 직접 생성할 수는 없음
> ServiceAccount는 Kubernetes 리소스로 생성 가능
> User 접근은 **kube-apiserver**에서 관리됨

### 인증 메커니즘

* **Static Password File**
* **Static Token File**
* **Client Certificates**
* **외부 Identity Service** (예: LDAP, OIDC 등)

### Basic Authentication

1. **Static Password File**

   * `--basic-auth-file` 옵션 사용
   * CSV 포맷: `password,username,userid`
   * 예시:

     ```sh
     curl -v -k https://<apiserver> -u "user:password"
     ```

2. **Static Token File**

   * `--token-auth-file` 옵션 사용
   * Authorization 헤더에 Bearer 토큰 추가
   * 예시:

     ```sh
     curl -v -k https://<apiserver> \
       --header "Authorization: Bearer <token>"
     ```
