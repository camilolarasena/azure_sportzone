'use strict';
(() => {
  const source = document.getElementById('chart-data');
  if (!source || typeof Chart === 'undefined') return;
  const charts = JSON.parse(source.textContent);
  const format = v => new Intl.NumberFormat('es-CO').format(v);
  const base = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { callback: format } } } };
  const draw = (id, type, labels, values, color) => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    new Chart(canvas, { type, data: { labels, datasets: [{ data: values, backgroundColor: color, borderColor: '#157ee8', borderWidth: 2, borderRadius: 7 }] }, options: type === 'doughnut' ? { responsive:true, maintainAspectRatio:false } : base });
  };
  draw('chart-daily', 'bar', charts.daily.labels, charts.daily.sales, '#76b6f2');
  draw('chart-sport', 'doughnut', charts.sport.labels, charts.sport.values, ['#157ee8', '#20b5a5', '#f8b755']);
  draw('chart-products', 'bar', charts.products.labels, charts.products.revenue, '#20b5a5');
  draw('chart-stock', 'bar', charts.stock.labels, charts.stock.values, '#9f83e6');
})();
