// Top Stocks JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Check if top stocks container exists on the page
    const topStocksContainer = document.getElementById('top-stocks-container');
    if (!topStocksContainer) return;

    // Fetch top stocks data
    fetchTopStocks();
});

async function fetchTopStocks() {
    const container = document.getElementById('top-stocks-container');
    
    try {
        const response = await fetch('/api/top_stocks');
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Clear loading message
        container.innerHTML = '';
        
        // Create the stock grid
        const stockGrid = document.createElement('div');
        stockGrid.className = 'row';
        container.appendChild(stockGrid);
        
        // API now directly returns an array of stock objects
        // Render each stock card
        data.forEach(stock => renderStockCard(stock, stockGrid));
        
    } catch (error) {
        console.error('Error fetching top stocks:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error loading stock data: ${error.message}
            </div>
        `;
    }
}

function renderStockCard(stock, container) {
    // Calculate if price change is positive or negative
    const isPositive = stock.percent_change >= 0;
    const changeClass = isPositive ? 'text-success' : 'text-danger';
    const changeIcon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
    
    // Format numbers
    const formattedPrice = formatCurrency(stock.close);
    const formattedChange = Math.abs(stock.percent_change).toFixed(2) + '%';
    const formattedMarketCap = formatMarketCap(stock.market_cap);
    
    // Get last 7 days of price data for the mini chart
    const priceData = stock.recent_prices ? stock.recent_prices.slice(-7) : [];
    
    // Create column div
    const colDiv = document.createElement('div');
    colDiv.className = 'col-md-6 col-lg-4 mb-4';
    
    // Create card HTML
    colDiv.innerHTML = `
        <div class="card stock-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h5 class="card-title mb-0">${stock.ticker}</h5>
                        <p class="card-text text-muted small mb-0">${stock.company_name}</p>
                        <span class="badge bg-secondary mt-1">${stock.sector || 'N/A'}</span>
                    </div>
                    <div class="text-end">
                        <div class="price">${formattedPrice}</div>
                        <div class="change ${changeClass}">
                            <i class="fas ${changeIcon}"></i> ${formattedChange}
                        </div>
                    </div>
                </div>
                
                <div class="stock-chart-container">
                    <canvas class="stock-chart" id="chart-${stock.ticker}"></canvas>
                </div>
                
                <div class="row mt-3">
                    <div class="col-6">
                        <div class="d-flex flex-column">
                            <span class="text-muted small">Market Cap</span>
                            <span class="fw-bold">${formattedMarketCap}</span>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="d-flex flex-column">
                            <span class="text-muted small">P/E Ratio</span>
                            <span class="fw-bold">${stock.pe_ratio ? stock.pe_ratio.toFixed(2) : 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="text-center mt-3">
                    <a href="/analyze?ticker=${stock.ticker}" class="btn btn-primary btn-sm">
                        <i class="fas fa-chart-bar me-1"></i> Analyze
                    </a>
                </div>
            </div>
        </div>
    `;
    
    // Add the card to the container
    container.appendChild(colDiv);
    
    // Initialize chart if price data is available
    if (priceData.length > 0) {
        initializeChart(stock.ticker, priceData, isPositive);
    }
}

function initializeChart(ticker, priceData, isPositive) {
    const chartId = `chart-${ticker}`;
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // Get just the values for the chart
    const prices = priceData.map(p => p.close);
    const labels = priceData.map(p => {
        const date = new Date(p.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    // Determine chart color based on price trend
    const chartColor = isPositive ? 'rgba(40, 167, 69, 0.8)' : 'rgba(220, 53, 69, 0.8)';
    const chartBg = isPositive ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)';
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${ticker} Price`,
                data: prices,
                borderColor: chartColor,
                backgroundColor: chartBg,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 3,
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
                    callbacks: {
                        label: function(context) {
                            return `$${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            }
        }
    });
}

function formatCurrency(value) {
    if (value === undefined || value === null) return 'N/A';
    return '$' + parseFloat(value).toFixed(2);
}

function formatMarketCap(value) {
    if (!value) return 'N/A';
    
    // Convert to billions or trillions for readability
    if (value >= 1e12) {
        return '$' + (value / 1e12).toFixed(2) + 'T';
    } else if (value >= 1e9) {
        return '$' + (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return '$' + (value / 1e6).toFixed(2) + 'M';
    } else {
        return '$' + value.toLocaleString();
    }
}