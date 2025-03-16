document.addEventListener('DOMContentLoaded', function() {
    // Registration Growth Trend Chart
    const registrationCtx = document.getElementById('registrationChart');
    if (registrationCtx) {
        const registrationData = JSON.parse(registrationCtx.dataset.trend || '[]');
        new Chart(registrationCtx, {
            type: 'line',
            data: {
                labels: registrationData.map(item => item.month),
                datasets: [{
                    label: 'New Registrations',
                    data: registrationData.map(item => item.count),
                    borderColor: getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim(),
                    backgroundColor: 'rgba(43, 60, 107, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    // Industry Distribution Chart
    const industryCtx = document.getElementById('industryChart');
    if (industryCtx) {
        const industryData = JSON.parse(industryCtx.dataset.distribution || '[]');
        new Chart(industryCtx, {
            type: 'doughnut',
            data: {
                labels: industryData.map(item => item.industry),
                datasets: [{
                    data: industryData.map(item => item.percentage),
                    backgroundColor: [
                        '#2b3c6b', '#50c878', '#f5a623', '#9013fe', '#d0021b',
                        '#7ed321', '#bd10e0', '#4a4a4a', '#b8e986', '#9b9b9b'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }

    // Graduation Year Distribution Chart
    const graduationCtx = document.getElementById('graduationChart');
    if (graduationCtx) {
        const graduationData = JSON.parse(graduationCtx.dataset.distribution || '[]');
        new Chart(graduationCtx, {
            type: 'bar',
            data: {
                labels: graduationData.map(item => item.name),
                datasets: [{
                    label: 'Alumni',
                    data: graduationData.map(item => item.percentage),
                    backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--secondary-color').trim(),
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // Location Distribution Chart
    const locationChartEl = document.getElementById('locationChart');
    if (locationChartEl) {
        try {
            const locationData = JSON.parse(locationChartEl.dataset.distribution || '[]');
            if (!locationData || locationData.length === 0) {
                console.warn('No location distribution data available');
                return;
            }

            new Chart(locationChartEl.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: locationData.map(item => item.location),
                    datasets: [{
                        data: locationData.map(item => item.percentage),
                        backgroundColor: [
                            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
                            '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.5,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                font: {
                                    size: 11
                                },
                                padding: 15
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.raw.toFixed(1)}%`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error initializing location chart:', error);
        }
    }

    // Employment Status Chart
    const employmentChartEl = document.getElementById('employmentChart');
    if (employmentChartEl) {
        try {
            const statusData = JSON.parse(employmentChartEl.dataset.status || '[]');
            if (!statusData || statusData.length === 0) {
                console.warn('No employment status data available');
                return;
            }

            new Chart(employmentChartEl.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: statusData.map(item => item.status),
                    datasets: [{
                        data: statusData.map(item => item.percentage),
                        backgroundColor: [
                            '#1cc88a', // Employed Full-Time
                            '#4e73df', // Employed Part-Time
                            '#36b9cc', // Self-Employed
                            '#f6c23e', // Student
                            '#e74a3b', // Unemployed
                            '#858796', // Retired
                            '#5a5c69'  // Internship/OJT
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.5,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                font: {
                                    size: 11
                                },
                                padding: 15
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.raw.toFixed(1)}%`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error initializing employment chart:', error);
        }
    }
}); 