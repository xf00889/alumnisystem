/* Reconciled donation charts, shared NORSU admin presentation. */
(function () {
  'use strict';
  function setEmpty(kind, text) {
    const empty = document.querySelector('[data-chart-empty="' + kind + '"]');
    const wrap = document.querySelector('[data-chart-wrap="' + kind + '"]');
    if (wrap) wrap.hidden = true;
    if (empty) { empty.hidden = false; if (text) empty.textContent = text; }
  }
  function money(value) { return '₱' + Number(value || 0).toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2}); }
  function build() {
    const node = document.getElementById('donation-chart-data');
    if (!node) return;
    let data;
    try { data = JSON.parse(node.textContent); } catch (_err) {
      ['daily','monthly','payment'].forEach(k => setEmpty(k, 'Chart data could not be read. Refresh to try again.'));
      return;
    }
    if (typeof window.Chart !== 'function') {
      ['daily','monthly','payment'].forEach(k => setEmpty(k, 'Chart library unavailable. Check the network connection and reload.'));
      return;
    }
    const navy = '#293f72', gold = '#bd8d48', green = '#248269';
    const base = { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: navy } }, tooltip: { callbacks: {label: (c) => (c.dataset.label || '') + ': ' + (c.dataset.yAxisID === 'count' ? c.formattedValue : money(c.parsed.y ?? c.parsed))} } },
      scales: { x: { ticks: { maxTicksLimit: 9, color: '#66758b' }, grid: { display: false } }, y: { beginAtZero:true, ticks: { callback: (n) => '₱' + Number(n).toLocaleString('en-PH') }, grid: { color: '#edf0f5' } } } };
    const charts = {};
    const daily = data.daily || {};
    if (daily.labels?.length && daily.amounts?.length) {
      charts.daily = new Chart(document.getElementById('dailyTrendsChart'), {
        type:'line', data:{labels:daily.labels,datasets:[
          {label:'Amount',data:daily.amounts,borderColor:navy,backgroundColor:'rgba(41,63,114,.13)',fill:true,tension:.25,pointRadius:3},
          {label:'Count',data:daily.counts,borderColor:gold,backgroundColor:gold,tension:.25,yAxisID:'count',pointRadius:3}
        ]},options:{...base,scales:{...base.scales,count:{type:'linear',position:'right',beginAtZero:true,ticks:{precision:0},grid:{drawOnChartArea:false}}}}});
    } else setEmpty('daily');
    const monthly = data.monthly || {};
    if (monthly.labels?.length && monthly.amounts?.length) {
      charts.monthly = new Chart(document.getElementById('monthlyTrendsChart'), {
        type:'bar',data:{labels:monthly.labels,datasets:[{label:'Verified funds',data:monthly.amounts,backgroundColor:navy,borderRadius:6,maxBarThickness:54}]},options:base});
    } else setEmpty('monthly');
    const payment = data.payment || {};
    if (payment.amounts?.some(v => Number(v) > 0)) {
      charts.payment = new Chart(document.getElementById('paymentMethodsChart'), {
        type:'doughnut',data:{labels:payment.labels,datasets:[{label:'Confirmed amount',data:payment.amounts,backgroundColor:[navy,gold,green,'#6889bd'],borderWidth:3,borderColor:'#fff'}]},
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:(c)=> c.label + ': ' + money(c.parsed)}}}}});
    } else setEmpty('payment');
    document.querySelectorAll('[data-export-chart]').forEach(button => {
      button.addEventListener('click', function () {
        const canvas = document.getElementById(button.dataset.exportChart);
        if (!canvas || canvas.closest('[hidden]')) return;
        const link = document.createElement('a'); link.download = button.dataset.exportChart + '.png';
        link.href = canvas.toDataURL('image/png'); link.click();
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
