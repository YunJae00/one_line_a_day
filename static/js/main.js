// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function () {
    // 메시지 자동 닫힘 및 애니메이션
    const messages = document.querySelectorAll('.messages .alert');

    messages.forEach(message => {
        // 닫기 버튼 이미 HTML에 추가됨
        const closeButton = message.querySelector('.btn-close');

        if (closeButton) {
            // 닫기 버튼 클릭 시 메시지 제거
            closeButton.addEventListener('click', function () {
                message.style.animation = 'fadeOut 0.5s ease-out forwards';
                setTimeout(() => {
                    message.remove();
                }, 500);
            });
        }

        // 자동 제거
        setTimeout(() => {
            if (message) {
                message.style.animation = 'fadeOut 0.5s ease-out forwards';
                setTimeout(() => {
                    message.remove();
                }, 500);
            }
        }, 3500);
    });

    // 구독 버튼에 애니메이션 효과 추가
    const subscribeBtn = document.querySelector('.btn-primary.btn-lg');
    if (subscribeBtn) {
        subscribeBtn.classList.add('fade-in');
    }
});

// 폼 유효성 검사 함수
function validateForm(formId) {
    const form = document.getElementById(formId);

    if (!form) return true;

    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;

    inputs.forEach(function (input) {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });

    return isValid;
}