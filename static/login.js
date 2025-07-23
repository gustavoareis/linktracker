// Lógica JavaScript para alternar a visibilidade da senha na tela de login
const toggleBtn = document.getElementById('toggle-password');
if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
        const passwordField = document.getElementById('password');
        const toggleIcon = document.getElementById('toggle-icon');

        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            toggleIcon.className = 'bi bi-eye-slash';
        } else {
            passwordField.type = 'password';
            toggleIcon.className = 'bi bi-eye';
        }
    });
}
