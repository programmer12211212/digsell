document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('freelance-search');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', function () {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const params = new URLSearchParams(window.location.search);
                params.set('q', searchInput.value);
                const url = window.location.pathname + '?' + params.toString();
                if (window.htmx) {
                    htmx.ajax('GET', url, { target: '#project-list', swap: 'innerHTML' });
                }
            }, 300);
        });
    }
});
