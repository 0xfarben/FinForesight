// FinForesight Chart Functions

/**
 * Create a strategy comparison chart between a strategy and buy-and-hold
 */
function createStrategyChart(canvasId, signalData, strategyName) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Extract data from signal data
    const labels = signalData.map(d => new Date(d.timestamp).toLocaleDateString());
    const prices = signalData.map(d => d.close);
    const shortMA = signalData.map(d => d.short_ma);
    const longMA = signalData.map(d => d.long_ma);
    
    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Price',
                data: prices,
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.2
            },
            {
                label: 'Short MA',
                data: shortMA,
                borderColor: '#28a745',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.2
            },
            {
                label: 'Long MA',
                data: longMA,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.2
            }
        ]
    };
    
    // Highlight buy/sell signals
    const buySignals = [];
    const sellSignals = [];
    
    for (let i = 1; i < signalData.length; i++) {
        if (signalData[i].position === 1) {
            buySignals.push({
                x: labels[i],
                y: prices[i]
            });
        } else if (signalData[i].position === -1) {
            sellSignals.push({
                x: labels[i],
                y: prices[i]
            });
        }
    }
    
    if (buySignals.length > 0) {
        data.datasets.push({
            label: 'Buy Signals',
            data: buySignals,
            backgroundColor: '#28a745',
            borderColor: '#28a745',
            pointRadius: 5,
            pointStyle: 'triangle',
            showLine: false
        });
    }
    
    if (sellSignals.length > 0) {
        data.datasets.push({
            label: 'Sell Signals',
            data: sellSignals,
            backgroundColor: '#dc3545',
            borderColor: '#dc3545',
            pointRadius: 5,
            pointStyle: 'triangle',
            rotation: 180,
            showLine: false
        });
    }
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#a0a0a0'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                title: {
                    display: true,
                    text: strategyName + ' Strategy Performance',
                    color: '#e0e0e0'
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            }
        }
    });
}

/**
 * Create an RSI chart
 */
function createRSIChart(canvasId, signalData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Extract data
    const labels = signalData.map(d => new Date(d.timestamp).toLocaleDateString());
    const prices = signalData.map(d => d.close);
    const rsiValues = signalData.map(d => d.rsi);
    
    // Create a dual axis chart for price and RSI
    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Price',
                data: prices,
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.2,
                yAxisID: 'y'
            },
            {
                label: 'RSI',
                data: rsiValues,
                borderColor: '#f39c12',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.2,
                yAxisID: 'y1'
            },
            {
                label: 'Overbought (70)',
                data: Array(labels.length).fill(70),
                borderColor: 'rgba(220, 53, 69, 0.5)',
                borderDash: [5, 5],
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 1,
                pointRadius: 0,
                yAxisID: 'y1'
            },
            {
                label: 'Oversold (30)',
                data: Array(labels.length).fill(30),
                borderColor: 'rgba(40, 167, 69, 0.5)',
                borderDash: [5, 5],
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 1,
                pointRadius: 0,
                yAxisID: 'y1'
            }
        ]
    };
    
    // Highlight buy/sell signals
    const buySignals = [];
    const sellSignals = [];
    
    for (let i = 0; i < signalData.length; i++) {
        if (signalData[i].signal === 1) {
            buySignals.push({
                x: labels[i],
                y: prices[i]
            });
        } else if (signalData[i].signal === -1) {
            sellSignals.push({
                x: labels[i],
                y: prices[i]
            });
        }
    }
    
    if (buySignals.length > 0) {
        data.datasets.push({
            label: 'Buy Signals',
            data: buySignals,
            backgroundColor: '#28a745',
            borderColor: '#28a745',
            pointRadius: 5,
            pointStyle: 'triangle',
            showLine: false,
            yAxisID: 'y'
        });
    }
    
    if (sellSignals.length > 0) {
        data.datasets.push({
            label: 'Sell Signals',
            data: sellSignals,
            backgroundColor: '#dc3545',
            borderColor: '#dc3545',
            pointRadius: 5,
            pointStyle: 'triangle',
            rotation: 180,
            showLine: false,
            yAxisID: 'y'
        });
    }
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#a0a0a0'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                title: {
                    display: true,
                    text: 'RSI Strategy Performance',
                    color: '#e0e0e0'
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    position: 'left',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                },
                y1: {
                    display: true,
                    position: 'right',
                    min: 0,
                    max: 100,
                    grid: {
                        drawOnChartArea: false,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            }
        }
    });
}

/**
 * Create a technical indicator chart
 */
function createIndicatorChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Extract data
    const labels = chartData.map(d => new Date(d.timestamp).toLocaleDateString());
    const values = chartData.map(d => d.value);
    
    const data = {
        labels: labels,
        datasets: [{
            label: 'Indicator Value',
            data: values,
            borderColor: '#7764e4',
            backgroundColor: 'rgba(119, 100, 228, 0.1)',
            fill: true,
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.3
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#a0a0a0'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            }
        }
    });
}

/**
 * Create a volatility and drawdown chart for risk assessment
 */
function createVolatilityChart(canvasId, volatilityData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Extract data
    const labels = volatilityData.map(d => d.date);
    const volatility = volatilityData.map(d => d.volatility * 100); // Convert to percentage
    
    const data = {
        labels: labels,
        datasets: [{
            label: 'Volatility (%)',
            data: volatility,
            borderColor: '#f39c12',
            backgroundColor: 'rgba(243, 156, 18, 0.1)',
            fill: true,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.3
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#a0a0a0'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                title: {
                    display: true,
                    text: 'Historical Volatility',
                    color: '#e0e0e0'
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a dual chart for comparative analysis
 */
function createDualComparisonChart(canvasId, tickerData, benchmarkData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Extract data
    const labels = tickerData.map(d => d.date);
    const tickerPrices = tickerData.map(d => d.price);
    const benchmarkPrices = benchmarkData.map(d => d.price);
    
    // Normalize prices to start at 100 for better comparison
    const tickerNormalized = normalize(tickerPrices);
    const benchmarkNormalized = normalize(benchmarkPrices);
    
    const data = {
        labels: labels,
        datasets: [
            {
                label: tickerData[0].ticker,
                data: tickerNormalized,
                borderColor: '#7764e4',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.3
            },
            {
                label: benchmarkData[0].ticker || 'Benchmark',
                data: benchmarkNormalized,
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(0, 0, 0, 0)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.3,
                borderDash: [5, 5]
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#a0a0a0'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(2);
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Relative Performance (Normalized to 100)',
                    color: '#e0e0e0'
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            }
        }
    });
}

/**
 * Normalize an array of values to start at 100
 */
function normalize(values) {
    const startValue = values[0];
    return values.map(value => (value / startValue) * 100);
}
