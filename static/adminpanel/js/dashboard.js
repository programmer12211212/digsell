document.addEventListener('DOMContentLoaded', function () {
  const ctx = document.getElementById('mainChart');
  if (!ctx) return;

  const parseJson = (id, fallback) => {
    const el = document.getElementById(id);
    if (!el) return fallback;
    try { return JSON.parse(el.textContent); } catch (e) { return fallback; }
  };

  const labels = parseJson('chartLabels', ['Jan', 'Feb', 'Mar']);
  let chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Foydalanuvchilar',
          data: parseJson('chartUsers', []),
          borderColor: '#00FF84',
          backgroundColor: 'rgba(0,255,132,0.08)',
          tension: 0.4,
          fill: true,
          pointRadius: 0,
        },
        {
          label: "E'lonlar",
          data: parseJson('chartListings', []),
          borderColor: '#00D9FF',
          backgroundColor: 'rgba(0,217,255,0.06)',
          tension: 0.4,
          fill: true,
          pointRadius: 0,
        },
        {
          label: "To'lovlar",
          data: parseJson('chartPayments', []),
          borderColor: '#FFB800',
          tension: 0.4,
          pointRadius: 0,
        },
        {
          label: 'Buyurtmalar',
          data: parseJson('chartOrders', []),
          borderColor: '#FF4D4D',
          tension: 0.4,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      animation: { duration: 800, easing: 'easeOutQuart' },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { color: 'rgba(255,255,255,0.7)', usePointStyle: true },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.5)' } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: 'rgba(255,255,255,0.5)' } },
      },
    },
  });

  document.querySelectorAll('#chartRangeTabs .tab-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      document.querySelectorAll('#chartRangeTabs .tab-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const range = btn.dataset.range;
      try {
        const res = await fetch(`/admin-console/api/analytics/?range=${range}`);
        const data = await res.json();
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.users;
        chart.data.datasets[1].data = data.listings;
        chart.data.datasets[2].data = data.payments;
        chart.data.datasets[3].data = data.orders;
        chart.update('active');
      } catch (e) {
        console.warn('Analytics fetch failed', e);
      }
    });
  });

  const stream = document.getElementById('activityStream');
  if (stream) {
    window.addEventListener('activity-update', (e) => {
      stream.innerHTML = e.detail.map((a) => `
        <div class="activity-item">
          <span class="activity-icon">${a.icon}</span>
          <div><div>${a.text}</div><div class="activity-time">${(a.time || '').slice(0, 16)}</div></div>
        </div>
      `).join('');
    });
    window.addEventListener('activity-item', (e) => {
      const a = e.detail;
      const div = document.createElement('div');
      div.className = 'activity-item';
      div.innerHTML = `<span class="activity-icon">${a.icon || '🔔'}</span><div><div>${a.text}</div></div>`;
      stream.prepend(div);
    });
  }
});
