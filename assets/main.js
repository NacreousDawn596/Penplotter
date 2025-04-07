document.querySelectorAll('.copy-icon').forEach(icon => {
    icon.addEventListener('click', (e) => {
        const code = e.target.parentElement.querySelector('code').innerText;
        navigator.clipboard.writeText(code);
        icon.classList.replace('fa-copy', 'fa-check');
        setTimeout(() => {
            icon.classList.replace('fa-check', 'fa-copy');
        }, 2000);
    });
});