// html 에서 오브젝트..? 갖고오기
// 햄버거 버튼
const hamburgerBtn = document.querySelector('.hamburger');
// 햄버거 버튼 눌렀을 때 메뉴
const navMenu = document.querySelector('.nav-menu');
// 네비게이션 바
const navEl = document.querySelector('nav');
// 스크롤 탑 버튼
const scrollTopBtn = document.querySelector('.scroll-top-btn');
// 다크모드 버튼
const darkModeBtn = document.querySelector('.dark-mode-btn');
// 로컬 스토리지에서 테마 저장된 값 가져오기
const savedTheme = localStorage.getItem('theme');

// 햄버거 메뉴 토글
hamburgerBtn.addEventListener('click', () => {
    navMenu.classList.toggle('active');
});

// 페이지가 스크롤될 때마다 실행한다.
window.addEventListener('scroll', () => {
    // 현재 페이지가 위에서부터 얼마나 내려갔는지 픽셀 단위로 알려준다.
    if (window.scrollY >= 300) {
        // 버튼에 visible 클래스를 추가해서 보이게 한다.
        scrollTopBtn.classList.add('visible');
    } else {
        // 버튼을 다시 숨긴다.
        scrollTopBtn.classList.remove('visible');
    }
    navEl.classList.toggle('scrolled', window.scrollY >= 60);
});

// 페이지 최상단으로 부드럽게 이동한다.
scrollTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// 다크모드 로컬 스토리지에 저장된 값이 dark이면 다크모드 적용
if (savedTheme === 'dark') {
    document.documentElement.dataset.theme = 'dark';
    darkModeBtn.classList.add('active');
}

darkModeBtn.addEventListener('click', () => {
    // 현재 테마가 다크모드인지 확인한다.
    const isDark = document.documentElement.dataset.theme === 'dark';
    const nextTheme = isDark ? 'light' : 'dark';

    document.documentElement.dataset.theme = nextTheme;
    darkModeBtn.classList.toggle('active', nextTheme === 'dark');
    localStorage.setItem('theme', nextTheme);
});

// 예외처리..? 뭐 비슷한 폼 검증이라고 합니다
const contactForm = document.querySelector('#contact-form');
const nameInput = document.querySelector('#name');
const emailInput = document.querySelector('#email');
const messageInput = document.querySelector('#message');

const nameError = document.querySelector('#name-error');
const emailError = document.querySelector('#email-error');
const messageError = document.querySelector('#message-error');
const formSuccess = document.querySelector('#form-success');

contactForm.addEventListener('submit', (event) => {
    event.preventDefault();

    nameError.textContent = '';
    emailError.textContent = '';
    messageError.textContent = '';
    formSuccess.textContent = '';

    //  입력값이 올바른지 기록하는 변수 (valid : 유효한, is : ~인가?)
    let isValid = true;

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const message = messageInput.value.trim();

    if (name === '') {
        nameError.textContent = '이름을 입력해주세요.';
        isValid = false;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (email === '') {
        emailError.textContent = '이메일을 입력해주세요.';
        isValid = false;
    } else if (!emailPattern.test(email)) {
        emailError.textContent = '올바른 이메일 형식이 아닙니다.';
        isValid = false;
    }

    if (message === '') {
        messageError.textContent = '메시지를 입력해주세요.';
        isValid = false;
    }

    if (!isValid) {
        return;
    }

    formSuccess.textContent = '문의가 정상적으로 제출되었습니다.';
    contactForm.reset();
});

[nameInput, emailInput, messageInput].forEach((input) => {
    input.addEventListener('input', () => {
        const error = document.querySelector(`#${input.id}-error`);
        error.textContent = '';
        formSuccess.textContent = '';
    });
});

//github api 연동
const projectsStatus = document.querySelector('#projects-status');
const projectsList = document.querySelector('#projects-list');
const projectsRetry = document.querySelector('#projects-retry');
const githubApiUrl = 'https://api.github.com/users/1st0Groom/repos';
const projectsCacheKey = 'github-projects';
// ponytail: 이 목록은 저장소 변경 시 낡을 수 있다. 자주 바뀌면 빌드 시 JSON으로 생성한다.
const fallbackProjects = [
    'Salon-Manager-pro',
    'aws-cloud-bootcamp',
    'codyssey',
    'university'
].map((name) => ({
    name,
    description: 'GitHub 저장소에서 자세히 보기',
    html_url: `https://github.com/1st0Groom/${name}`
}));

const renderProjects = (repos) => {
    projectsList.innerHTML = repos.map((repo) => `
        <article class="project-card">
            <h3>${repo.name}</h3>
            <p>${repo.description ?? '설명이 없습니다.'}</p>
            ${Number.isInteger(repo.stargazers_count) ? `<p>⭐ ${repo.stargazers_count}</p>` : ''}
            <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer">
                GitHub에서 보기
            </a>
        </article>
    `).join('');
};

const loadProjects = async () => {
    projectsStatus.textContent = '로딩 중...';
    projectsList.innerHTML = '';
    projectsRetry.hidden = true;

    try {
        const response = await fetch(githubApiUrl);

        if (!response.ok) {
            throw new Error('GitHub API 요청 실패');
        }

        const repos = await response.json();

        if (repos.length === 0) {
            projectsStatus.textContent = '표시할 프로젝트가 없습니다.';
            return;
        }

        localStorage.setItem(projectsCacheKey, JSON.stringify(repos));
        projectsStatus.textContent = '';
        renderProjects(repos);
    } catch (error) {
        console.warn(error.message);
        let cachedProjects = [];

        try {
            cachedProjects = JSON.parse(localStorage.getItem(projectsCacheKey) ?? '[]');
        } catch {
            localStorage.removeItem(projectsCacheKey);
        }

        renderProjects(cachedProjects.length > 0 ? cachedProjects : fallbackProjects);
        projectsStatus.textContent = '실시간 API 연결에 실패해 저장된 프로젝트 목록을 표시합니다.';
        projectsRetry.hidden = false;
    }
};

projectsRetry.addEventListener('click', loadProjects);

loadProjects();

// 화면에 들어온 섹션을 보여주는 스크롤 애니메이션
const revealItems = document.querySelectorAll('main > section');

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('show');
            revealObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.2
});

revealItems.forEach((section) => {
    section.classList.add('reveal');
    revealObserver.observe(section);
});
