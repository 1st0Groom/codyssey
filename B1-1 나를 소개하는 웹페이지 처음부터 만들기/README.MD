# 변승언의 포트폴리오

순수 HTML, CSS, JavaScript로 만든 반응형 개인 포트폴리오 웹사이트입니다.
웹페이지의 기본 구조부터 DOM 조작, 이벤트 처리, 폼 검증, GitHub API 연동까지 직접 구현하는 것을 목표로 합니다.

## 사용 기술

- HTML5 시맨틱 마크업
- CSS3 변수, Flexbox, Grid, 반응형 레이아웃
- Vanilla JavaScript
- GitHub REST API
- GitHub Pages

## 현재 구현 상태

- [x] Hero, About, Skills, Projects, Contact, Footer 섹션
- [x] 시맨틱 HTML 구조와 섹션 이동 링크
- [x] 모바일 퍼스트 반응형 CSS
- [x] Flexbox 네비게이션과 Grid 프로젝트 영역
- [x] 모바일 햄버거 메뉴
- [x] 다크 모드와 `localStorage` 테마 저장
- [x] 스크롤 위치에 따른 네비게이션 스타일 변경
- [x] 맨 위로 이동 버튼
- [x] Contact 폼 필수값·이메일 형식 검증
- [x] GitHub API 요청·프로젝트 카드 렌더링·상태 처리
- [x] Intersection Observer 스크롤 애니메이션
- [ ] GitHub Pages 배포 및 배포 환경 검증
- [ ] 데스크톱·모바일·다크 모드 스크린샷 추가

## 실행 방법

1. 저장소를 내려받습니다.
2. VS Code에서 프로젝트 폴더를 엽니다.
3. Live Server로 `index.html`을 실행합니다.

외부 라이브러리 없이 동작하므로 별도의 설치 명령은 필요하지 않습니다.

## 사용법

- 네비게이션 메뉴를 클릭하면 해당 섹션으로 이동합니다.
- 모바일 화면에서는 햄버거 버튼으로 메뉴를 열고 닫습니다.
- 달 아이콘을 클릭하면 다크 모드가 켜지고, 설정은 새로고침 후에도 유지됩니다.
- Projects 섹션에서는 `1st0Groom`의 GitHub 저장소를 불러옵니다.
- 프로젝트 카드의 GitHub 링크를 클릭하면 저장소 페이지가 새 탭에서 열립니다.
- 이름·이메일·메시지를 입력한 뒤 Contact 폼을 제출하면 입력값을 검증합니다.
- 페이지를 300px 이상 내리면 맨 위로 이동 버튼이 나타납니다.
- 각 섹션은 화면에 들어올 때 순서대로 나타납니다.

이 사이트의 Contact 폼은 프론트엔드 검증만 수행하며, 실제 이메일을 전송하지는 않습니다.

## 주요 동작 기준

- 네비게이션 스타일 변경: `scrollY >= 60px`
- 맨 위로 이동 버튼 표시: `scrollY >= 300px`
- 다크 모드 설정: 브라우저 `localStorage`의 `theme` 키에 저장
- 스크롤 애니메이션: `IntersectionObserver` threshold `0.2`

## GitHub API 연동

Projects 섹션에서 다음 엔드포인트를 호출해 저장소 목록을 표시합니다.

```text
https://api.github.com/users/1st0Groom/repos
```

API 요청 상태는 다음 네 가지로 처리합니다.

- 로딩: 데이터를 요청하는 중
- 성공: 프로젝트 카드 표시
- 에러: 캐시 또는 확인된 공개 저장소 목록과 다시 시도 버튼 표시
- 빈 상태: 표시할 저장소가 없을 때 안내

인증 없이 GitHub API를 호출하므로 짧은 시간에 반복해서 새로고침하면 rate limit으로 오류 상태가 표시될 수 있습니다.

## GitHub Pages 배포 방법

1. 변경 사항을 GitHub 저장소의 `main` 브랜치에 push합니다.
2. GitHub 저장소에서 `Settings`를 엽니다.
3. 왼쪽 메뉴에서 `Pages`를 선택합니다.
4. `Build and deployment`의 Source를 `Deploy from a branch`로 선택합니다.
5. Branch를 `main`, 폴더를 `/ (root)`로 선택하고 `Save`를 누릅니다.
6. 배포가 끝나면 같은 화면에 표시되는 URL로 접속합니다.

이 저장소의 예상 주소 형식은 다음과 같습니다. 실제 접속 가능 여부는 Pages 배포 후 확인해야 합니다.

```text
https://1st0Groom.github.io/codyssey/
```

배포 후 모바일·다크 모드·폼 검증·GitHub API가 실제 URL에서도 동작하는지 확인합니다.

## 스크린샷

배포 후 다음 스크린샷을 추가합니다.

- 데스크톱 화면
- 모바일 화면
- 다크 모드 화면

예시 파일 위치:

```text
images/screenshot-desktop.png
images/screenshot-mobile.png
images/screenshot-dark.png
```

## 배포 URL

GitHub Pages 배포 후 아래에 실제 접속 URL을 기록합니다.

```text
배포 URL: 배포 후 입력
```

## 저장소

<https://github.com/1st0Groom/codyssey>
