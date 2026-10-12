/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--tracer-study-report-html") && !executed["tracer_study/report.html"]) {
executed["tracer_study/report.html"] = true;
/* BEGIN: tracer_study/report.html */

document.addEventListener('DOMContentLoaded', function () {
    const payloadEl = document.getElementById('tracer-chart-payload');
    if (!payloadEl || typeof Chart === 'undefined') {
        return;
    }

    const charts = JSON.parse(payloadEl.textContent || '[]');
    const truncate = function (label, maxLength) {
        if (!label) return '';
        return label.length > maxLength ? label.slice(0, maxLength - 1) + '...' : label;
    };

    charts.forEach(function (item) {
        const canvas = document.getElementById(item.id);
        if (!canvas) return;

        const isDoughnut = item.type === 'doughnut';
        const config = {
            type: item.type,
            data: {
                labels: item.labels,
                datasets: [{
                    data: item.values,
                    backgroundColor: item.colors,
                    borderColor: '#ffffff',
                    borderWidth: isDoughnut ? 2 : 0,
                    borderRadius: isDoughnut ? 0 : 5,
                    maxBarThickness: 28
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: isDoughnut ? 'x' : 'y',
                plugins: {
                    legend: {
                        display: isDoughnut,
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            color: '#4a5568',
                            font: { size: 11 },
                            generateLabels: function (chart) {
                                return Chart.defaults.plugins.legend.labels.generateLabels(chart).map(function (label) {
                                    label.text = truncate(label.text, 28);
                                    return label;
                                });
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.parsed.x ?? context.parsed ?? 0;
                                return context.label + ': ' + value;
                            }
                        }
                    }
                },
                scales: isDoughnut ? {} : {
                    x: {
                        beginAtZero: true,
                        ticks: { precision: 0, color: '#718096' },
                        grid: { color: 'rgba(113, 128, 150, 0.18)' }
                    },
                    y: {
                        ticks: {
                            color: '#4a5568',
                            callback: function (value) {
                                return truncate(this.getLabelForValue(value), 24);
                            }
                        },
                        grid: { display: false }
                    }
                },
                cutout: isDoughnut ? '62%' : undefined
            }
        };

        new Chart(canvas, config);
    });
});

/* END: tracer_study/report.html */
}
})();
