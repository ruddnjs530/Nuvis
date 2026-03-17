# GPU 서버 연동을 위한 Git Sparse-Checkout (부분 복제) 가이드

보안상 SFTP 포트가 막혀있는 웹 환경(Jupyter 등)의 GPU 서버에서 프로젝트 전체(모노레포)를 다운로드 받지 않고, **오직 AI 파트 폴더(`server_ai/`)만 쏙 빼내어 다운로드** 받는 방법입니다.

## 📌 왜 이 방식(Sparse-Checkout)을 사용하나요?
- 프론트엔드, 백엔드 등 불필요한 폴더를 다운받지 않아 공간과 시간을 크게 절약합니다.
- 모노레포 폴더 구조가 꼬이지 않습니다.
- 로컬 환경(VS Code)에서 코딩 후 커밋/푸시(`git push`)를 하고, GPU 서버 터미널에서는 오직 당겨오기(`git pull`)만 실행하여 코드를 최신화한 뒤 테스트하는 구조입니다.

---

## 🚀 설정 방법 (GPU 서버 터미널에 복제/붙여넣기)

GPU 터미널(JupyterHub 터미널 등)을 열고, 작업하실 상위 디렉토리로 이동한 후 아래 커맨드들을 한 줄씩 실행하세요.

### 1단계: 껍데기 저장소 생성 (clone 대신 init)
```bash
# 새로운 폴더를 만들고 깃 저장소 초기화
mkdir my_project && cd my_project
git init

# 원격 모노레포 저장소 주소를 연결 (HTTPS 주소)
git remote add origin "여러분의_레포지토리_주소(예: https://lab.ssafy.com/.../repo.git)"
```

### 2단계: 부분 복제(Sparse-Checkout) 활성화
```bash
# Git 2.25 이상에서 지원하는 Sparse 기능 켜기
git config core.sparseCheckout true

# 다운로드 받을 특정 폴더 경로만 설정 파일에 기록!
echo "server_ai/*" >> .git/info/sparse-checkout
```

### 3단계: 다운로드 시작
```bash
# 설정한 폴더들만 쏙 빼서 다운로드 (보통 main 또는 master 브랜치)
git pull origin develop
```

> **성공 🎉** 이제 `my_project` 폴더 안에는 `server_ai/` 폴더만 들어와 있습니다!

---

## 🎈 일상적인 작업 흐름
1. **[로컬 내 컴퓨터]** VS Code에서 코드를 작성하고 모노레포 저장소에 평소처럼 `git push` 합니다.
2. **[GPU 서버 브라우저]** GPU 터미널 창(JupyterHub)으로 이동하여 아래 명령어를 칩니다.
   ```bash
   git pull origin main
   ```
3. 코드가 1초 만에 최신화되면, 바로 `python main.py`를 실행하여 테스트를 진행합니다.
