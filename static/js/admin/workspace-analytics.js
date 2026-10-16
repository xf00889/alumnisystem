/* HR and coordinator analytics. JSON-script payloads are rendered by Django and read as data. */
(() => {
  'use strict';
  const definitions = [
    ['hrApplicationChart', 'hr-applications-data', 'line'],
    ['hrJobSourcesChart', 'hr-sources-data', 'doughnut'],
    ['hrApplicationStatusChart', 'hr-status-data', 'doughnut'],
    ['hrTopPositionsChart', 'hr-positions-data', 'bar-horizontal'],
    ['hrJobTypesChart', 'hr-types-data', 'bar'],
    ['coordinatorCampusChart', 'coordinator-campus-data', 'bar'],
    ['coordinatorActivityChart', 'coordinator-activity-data', 'doughnut'],
    ['coordinatorCollegeChart', 'coordinator-college-data', 'bar-horizontal'],
    ['coordinatorBatchChart', 'coordinator-batch-data', 'bar'],
    ['coordinatorRegistrationChart', 'coordinator-registration-data', 'line'],
    ['coordinatorEmploymentChart', 'coordinator-employment-data', 'bar-horizontal'],
  ];
  const colors = ['#2b3c6b', '#c3a16c', '#14999f', '#6a86b1', '#a9765c', '#7f7cae', '#61768d', '#aa8e8f', '#75a0a0'];
  const parse = id => {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      const parsed = JSON.parse(el.textContent);
      if (!Array.isArray(parsed.labels) || !Array.isArray(parsed.values) || parsed.labels.length !== parsed.values.length) return null;
      return parsed;
    } catch { return null; }
  };
  const make = (tag, className, parent, text) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text != null) el.textContent = text;
    parent.appendChild(el);
    return el;
  };
  const appendDataTable = (frame, data) => {
    const details = make('details', 'workspace-chart-data', frame);
    make('summary', '', details, 'View chart data');
    const wrap = make('div', 'workspace-chart-table-wrap', details);
    const table = make('table', '', wrap);
    const head = make('thead', '', table);
    const row = make('tr', '', head);
    make('th', '', row, 'Category');
    make('th', '', row, 'Total');
    const body = make('tbody', '', table);
    data.labels.forEach((label, index) => {
      const tr = make('tr', '', body);
      make('td', '', tr, String(label));
      make('td', '', tr, String(data.values[index]));
    });
  };
  definitions.forEach(([canvasId, dataId, style]) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const frame = canvas.parentElement;
    const data = parse(dataId);
    if (!data) {
      canvas.hidden = true;
      make('p', 'workspace-chart-notice', frame, 'Chart data unavailable.');
      return;
    }
    appendDataTable(frame.parentElement, data);
    if (!data.values.some(value => Number(value) > 0)) {
      canvas.hidden = true;
      make('p', 'workspace-chart-notice', frame, 'No records available yet.');
      return;
    }
    if (typeof Chart === 'undefined') {
      canvas.hidden = true;
      make('p', 'workspace-chart-notice', frame, 'Chart cannot load. Use “View chart data” below.');
      return;
    }
    const isLine = style === 'line';
    const isDoughnut = style === 'doughnut';
    const horizontal = style === 'bar-horizontal';
    const chartType = isLine ? 'line' : isDoughnut ? 'doughnut' : 'bar';
    const dataset = {
      label: 'Total', data: data.values,
      backgroundColor: isLine ? 'rgba(43,60,107,.12)' : data.values.map((_, i) => colors[i % colors.length]),
      borderColor: isLine ? colors[0] : '#fff',
      borderWidth: isLine ? 2.5 : (isDoughnut ? 2 : 0),
    };
    if (isLine) {
      Object.assign(dataset, {fill: true, tension: .3, pointRadius: 4, pointBackgroundColor: colors[0]});
    } else if (!isDoughnut) {
      Object.assign(dataset, {borderRadius: 4, maxBarThickness: 32});
    }
    const options = {
      responsive: true, maintainAspectRatio: false,
      indexAxis: horizontal ? 'y' : 'x',
      plugins: {
        legend: {display: isDoughnut, position: 'bottom', labels: {boxWidth: 12, padding: 14, font: {size: 11}}},
        tooltip: {callbacks: {label: ctx => `${ctx.label || 'Total'}: ${ctx.parsed && typeof ctx.parsed === 'object' ? (horizontal ? ctx.parsed.x : ctx.parsed.y) : ctx.parsed}`}},
      },
      scales: isDoughnut ? {} : {
        x: {ticks: {autoSkip: !horizontal, maxRotation: 35, color: '#65728a', font: {size: 10}, precision: horizontal ? 0 : undefined}, grid: {display: horizontal}},
        y: {beginAtZero: !horizontal, ticks: {precision: horizontal ? undefined : 0, autoSkip: !horizontal, color: '#65728a', font: {size: 10}}, grid: {color: '#edf1f6'}},
      },
    };
    try { new Chart(canvas, {type: chartType, data: {labels: data.labels, datasets: [dataset]}, options}); }
    catch {
      canvas.hidden = true;
      make('p', 'workspace-chart-notice', frame, 'Chart cannot load. Use “View chart data” below.');
    }
  });
})();
