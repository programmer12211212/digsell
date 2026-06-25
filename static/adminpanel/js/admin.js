document.addEventListener('DOMContentLoaded', function () {
  const table = document.getElementById('adminDataTable');
  if (table && $.fn.DataTable) {
    $(table).DataTable({
      pageLength: 25,
      order: [[5, 'desc']],
      dom: 'Bfrtip',
      buttons: ['excel', 'pdf', 'csv'],
      language: {
        search: 'Qidirish:',
        lengthMenu: '_MENU_ ta ko\'rsatish',
        info: '_TOTAL_ dan _START_-_END_',
        paginate: { next: '→', previous: '←' },
      },
    });
  }

  window.adminPost = function (url, data) {
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const body = data instanceof FormData ? data : new URLSearchParams(data);
    if (!(data instanceof FormData) && !body.has('csrfmiddlewaretoken')) {
      body.append('csrfmiddlewaretoken', csrf);
    }
    return fetch(url, {
      method: 'POST',
      headers: data instanceof FormData ? { 'X-CSRFToken': csrf } : {
        'X-CSRFToken': csrf,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    }).then((r) => r.json());
  };

  window.bulkAction = function (formId, url) {
    const form = document.getElementById(formId);
    if (!form) return;
    const ids = [...form.querySelectorAll('input[name="ids"]:checked')].map((i) => i.value);
    if (!ids.length) return alert('Hech narsa tanlanmadi');
    const fd = new FormData();
    ids.forEach((id) => fd.append('ids', id));
    fd.append('action', form.querySelector('[name="action"]')?.value || 'approve');
    adminPost(url, fd).then(() => location.reload());
  };
});
