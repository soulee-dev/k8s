# Kubernetes (k8s)

언젠가는 쿠버네티스를 제대로 공부해봐야겠다고 생각했는데,
2023년 군대 가기 전에 사둔 강의조차 아직 끝내지 못했다.

그래서 이번엔 아예 처음부터 다시,
강의를 정리하면서 중간중간 직접 hands-on으로 클러스터를 구축해보려고 한다.

## 타임라인
- 2025.08.17 - 학습 시작

## 잡소리
Udemy 강의 Progress를 초기화 하는 방법이 없나 찾아봤는데, [Reddit](https://www.reddit.com/r/Udemy/comments/k1iiqg/reset_course_progress/)에서 좋은 방법을 알려줬다.

Course에 있는 모든 탭을 열고, 아래 코드를 개발자 콘솔에서 실행하면 된다.

```js
document.querySelectorAll('li input[type=checkbox]:checked').forEach((box, i) => setTimeout(() => box.click(), i * 50));
```