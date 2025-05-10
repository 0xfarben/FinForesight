// FinForesight main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Fetch stock data for dashboard
    if (document.getElementById('stockGrid')) {
        fetchDashboardStocks();
    }
    
    // Initialize datetime inputs with current values
    initDateInputs();
    
    // Handle form submission and agent execution
    const analyzeForm = document.getElementById('analyzeForm');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            // Form is submitted normally, handled by Flask
        });
    }
    
    // Handle agent execution on results page
    if (document.getElementById('agentContainer')) {
        // Start the autonomous agent workflow
        startAgentWorkflow();
    }

    // Technical indicators form
    const indicatorsForm = document.getElementById('technicalIndicatorsForm');
    if (indicatorsForm) {
        indicatorsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Handle form submission via AJAX
            submitIndicatorsForm(new FormData(indicatorsForm));
        });
    }

    // Initialize Bootstrap tabs
    var triggerTabList = [].slice.call(document.querySelectorAll('#financialTabs a'))
    triggerTabList.forEach(function(triggerEl) {
        var tabTrigger = new bootstrap.Tab(triggerEl)
        triggerEl.addEventListener('click', function(event) {
            event.preventDefault()
            tabTrigger.show()
        })
    })
});

/**
 * Initialize date inputs with default values
 */
function initDateInputs() {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        endDateInput.valueAsDate = today;
        startDateInput.valueAsDate = oneYearAgo;
    }
}

/**
 * Fetch stock data for dashboard display
 */
function fetchDashboardStocks() {
    const stockGrid = document.getElementById('stockGrid');
    const loadingEl = document.getElementById('loadingStocks');
    
    if (!stockGrid) return;
    
    loadingEl.style.display = 'block';
    
    fetch('/get_stock_data')
        .then(response => response.json())
        .then(data => {
            console.log('Received stock data:', data); // Debug log
            loadingEl.style.display = 'none';
            console.log('Data got from server:', data);
            populateStockGrid(data);
        })
        .catch(error => {
            console.error('Error fetching stock data:', error);
            loadingEl.style.display = 'none';
            stockGrid.innerHTML = `
                <div class="col-12 text-center">
                    <div class="alert alert-danger">
                        Failed to load stock data. Please try again later.
                    </div>
                </div>
            `;
        });
}


/**
 * Populate the stock grid with fetched data
 */
function populateStockGrid(stockData) {
    const stockGrid = document.getElementById('stockGrid');
    if (!stockGrid) return;
    
    let htmlContent = '';
    
    // Check if we have any stock data
    if (!stockData || Object.keys(stockData).length === 0) {
        stockGrid.innerHTML = `
            <div class="col-12 text-center">
                <div class="alert alert-warning">
                    No stock data available at the moment.
                </div>
            </div>
        `;
        return;
    }
    
    // Generate HTML for each stock
    Object.entries(stockData).forEach(([ticker, data]) => {
        // Log data structure for debugging
        console.log('Processing stock:', ticker, data);
        
        // Calculate percentage change
        const currentPrice = data.close || 0;
        const previousPrice = data.previous_close || 0;
        const percentChange = data.percent_change || ((currentPrice - previousPrice) / previousPrice * 100);
        
        const changeClass = percentChange >= 0 ? 'positive' : 'negative';
        const changeIcon = percentChange >= 0 ? 'fa-caret-up' : 'fa-caret-down';
        
        htmlContent += `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card stock-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div>
                                <h5 class="card-title mb-0">${ticker}</h5>
                                <small class="text-muted">${data.company_name || ''}</small>
                        </div>
                            <span class="sector badge bg-primary">${data.sector || 'N/A'}</span>
                        </div>
                        
                        <div class="price-section mb-3">
                            <div class="current-price">$${currentPrice.toFixed(2)}</div>
                            <div class="price-change ${changeClass}">
                            <i class="fas ${changeIcon}"></i> 
                                ${Math.abs(percentChange).toFixed(2)}%
                        </div>
                        </div>
                        
                        <div class="d-flex justify-content-between mb-3">
                            <div>
                                <small class="text-muted d-block">Market Cap</small>
                                <span>${formatMarketCap(data.market_cap)}</span>
                            </div>
                            <div class="text-end">
                                <small class="text-muted d-block">P/E Ratio</small>
                                <span>${data.pe_ratio ? data.pe_ratio.toFixed(2) : 'N/A'}</span>
                            </div>
                        </div>
                        
                        <div class="chart-container">
                            <canvas id="chart-${ticker}"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    stockGrid.innerHTML = htmlContent;
    
    // Initialize charts
    Object.keys(stockData).forEach(ticker => {
        createMiniChart(ticker, stockData[ticker]);
    });
}

/**
 * Create a small price chart for a stock card
 */
function createMiniChart(ticker, stockData) {
    const ctx = document.getElementById(`chart-${ticker}`);
    if (!ctx) return;
    
    const prices = stockData.recent_prices || [];
    const labels = prices.map((_, index) => index);
    const data = prices.map(p => p.close || p.price);
    
    const lastPrice = data[data.length - 1];
    const firstPrice = data[0];
    const priceChange = lastPrice - firstPrice;
    const chartColor = priceChange >= 0 ? '#00ff88' : '#ff4d4d';
    
    new Chart(ctx, {
        type: 'line',
        data: {
        labels: labels,
        datasets: [{
                data: data,
                borderColor: chartColor,
                backgroundColor: `${chartColor}20`,
                borderWidth: 2,
            tension: 0.4,
            pointRadius: 0,
            fill: true
        }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false,
                    grid: {
                        display: false
                    }
                },
                y: {
                    display: false,
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Handle autonomous agent workflow
 */
function startAgentWorkflow() {
    // Start with the first agent (data analyst)
    runNextAgent('data_analyst');
}

/**
 * Run the next agent in the workflow
 */
function runNextAgent(agentName) {
    if (!agentName) return;
    
    // Update UI to show current agent
    updateAgentStatus(agentName, 'processing');
    
    // Show loading spinner for current agent
    const loadingSpinner = document.getElementById(`${agentName}Loading`);
    if (loadingSpinner) {
        loadingSpinner.style.display = 'block';
    }
    
    // Clear previous results
    const resultContainer = document.getElementById(`${agentName}Results`);
    if (resultContainer) {
        resultContainer.innerHTML = '';
        resultContainer.style.display = 'none';
    }
    
    // Make API call to run the agent
    fetch(`/run_agent/${agentName}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
        if (data.status === 'success') {
            // Get agent results
            const agentResults = data.results[agentName];
            
            // Update agent status based on results
            updateAgentStatus(agentName, agentResults.status || 'completed');
            updateProgressTracker();
            
            // Display agent results
            displayAgentResults(agentName, agentResults);
            
            // Get the next agent from the response
            const nextAgent = data.results.current_agent;
            
            // Run the next agent if workflow is not complete
            if (nextAgent && nextAgent !== 'completed' && nextAgent !== 'failed') {
                setTimeout(() => {
                    runNextAgent(nextAgent);
                }, 1000);
            } else if (nextAgent === 'completed') {
                updateWorkflowStatus('completed');
            } else if (nextAgent === 'failed') {
                updateWorkflowStatus('error');
                // Set all remaining agents to error
                const agents = ['data_analyst', 'trade_strategy', 'trade_advisor', 'risk_advisor'];
                agents.forEach(agent => {
                    const statusBadge = document.getElementById(`${agent}Status`);
                    if (statusBadge && statusBadge.textContent === 'Pending') {
                        updateAgentStatus(agent, 'error');
                    }
                });
                updateProgressTracker();
            }
        } else {
            // Handle error
            console.error(`Error running ${agentName}:`, data.message);
            updateAgentStatus(agentName, 'error');
            
            // Display error message
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${data.message || 'An unexpected error occurred'}
                    </div>
                `;
                resultContainer.style.display = 'block';
            }
            
            // Update workflow status
            updateWorkflowStatus('error');
        }
    })
    .catch(error => {
        console.error(`Error running ${agentName}:`, error);
        
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
        // Update status
        updateAgentStatus(agentName, 'error');
        
        // Display error message
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> Failed to communicate with the server. Please try again.
                </div>
            `;
            resultContainer.style.display = 'block';
        }
        
        // Update workflow status
        updateWorkflowStatus('error');
    });
}

/**
 * Update the UI to reflect agent status
 */
function updateAgentStatus(agentName, status, message = '') {
    const agentCard = document.querySelector(`#${agentName}Card`);
    const statusBadge = document.querySelector(`#${agentName}Status`);
    const resultContainer = document.getElementById(`${agentName}Results`);
    
    if (!agentCard || !statusBadge) return;

    // Remove all existing status classes
    agentCard.classList.remove('pending', 'processing', 'completed', 'error');
        statusBadge.classList.remove('status-pending', 'status-processing', 'status-completed', 'status-error');
        
    // Add new status classes
    agentCard.classList.add(status);
        statusBadge.classList.add(`status-${status}`);
    
    // Update status text
    statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    // Show error message if present
    if (status === 'error' && message) {
        if (!resultContainer.querySelector('.alert-danger')) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
            resultContainer.insertBefore(alertDiv, resultContainer.firstChild);
        }
    }
}

/**
 * Update the progress tracker UI
 */
function updateProgressTracker() {
    const agents = ['data_analyst', 'trade_strategy', 'trade_advisor', 'risk_advisor'];
    let completedCount = 0;
    let activeAgent = null;
    
    // Count completed agents and find active agent
    agents.forEach(agent => {
        const statusBadge = document.getElementById(`${agent}Status`);
        if (statusBadge) {
            if (statusBadge.textContent === 'Completed') {
                completedCount++;
            } else if (statusBadge.textContent === 'Processing') {
                activeAgent = agent;
            }
        }
    });
    
    // Update progress bar
    const progressBar = document.getElementById('analysisProgress');
    if (progressBar) {
        const percent = (completedCount / agents.length) * 100;
        progressBar.style.width = `${percent}%`;
        if (percent === 100) {
            progressBar.style.background = 'linear-gradient(90deg, #00ff88, #7764e4)';
        } else if (percent >= 50) {
            progressBar.style.background = 'linear-gradient(90deg, #7764e4, #00ff88)';
        } else {
            progressBar.style.background = '#e0e0e0';
        }
    }
    
    // Update progress steps (dot and label coloring)
    agents.forEach(agent => {
        const stepEl = document.getElementById(`${agent}Step`);
        if (stepEl) {
            // Remove all status classes
            stepEl.classList.remove('active', 'completed');
            const dot = stepEl.querySelector('.progress-step-dot');
            const label = stepEl.querySelector('.progress-step-label');
            if (dot) {
                dot.classList.remove('dot-completed', 'dot-active', 'dot-pending');
            }
            if (label) {
                label.classList.remove('label-completed', 'label-active', 'label-pending');
            }
            const statusBadge = document.getElementById(`${agent}Status`);
            if (statusBadge && statusBadge.textContent === 'Completed') {
                stepEl.classList.add('completed');
                if (dot) dot.classList.add('dot-completed');
                if (label) label.classList.add('label-completed');
            } else if (agent === activeAgent) {
                stepEl.classList.add('active');
                if (dot) dot.classList.add('dot-active');
                if (label) label.classList.add('label-active');
            } else {
                if (dot) dot.classList.add('dot-pending');
                if (label) label.classList.add('label-pending');
            }
        }
    });
}

/**
 * Update overall workflow status
 */
function updateWorkflowStatus(status) {
    const workflowStatus = document.getElementById('workflowStatus');
    if (workflowStatus) {
        if (status === 'completed') {
            workflowStatus.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle" style="text-align: center; align-items: center;"></i> Analysis workflow completed successfully!
                </div>
            `;
        } else if (status === 'error') {
            workflowStatus.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle" style="text-align: center; align-items: center;"></i> Analysis workflow encountered an error.
                </div>
            `;
        }
    }
}

/**
 * Display the results from an agent
 */
function displayAgentResults(agentName, results) {
    const resultContainer = document.getElementById(`${agentName}Results`);
    const loadingSpinner = document.getElementById(`${agentName}Loading`);
    
    if (!resultContainer) return;
    
    // Hide loading spinner if it exists
    if (loadingSpinner) {
        loadingSpinner.style.display = 'none';
    }
    
    // Handle different result states
    if (!results) {
        resultContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i> No results available
            </div>
        `;
        resultContainer.style.display = 'block';
        return;
    }

    // Check for error state
    if (results.status === 'error' || results.message || (results.data && results.data.error)) {
        const errorMessage = results.message || results.data?.error || 'An unexpected error occurred';
        resultContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i> ${errorMessage}
            </div>
        `;
        
        // If we have partial data, still try to display it
        if (results.data && Object.keys(results.data).length > 0) {
            displayPartialResults(agentName, results.data);
        }
        
        resultContainer.style.display = 'block';
        return;
    }
    
    // Display different results based on the agent
    switch (agentName) {
        case 'data_analyst':
            if (results.status === 'processing') {
                resultContainer.innerHTML = `
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Collecting data...</p>
                    </div>
                `;
            } else if (results.data) {
            displayDataAnalystResults(resultContainer, results);
            } else {
                resultContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i> No data available
                    </div>
                `;
            }
            break;
        case 'trade_strategy':
            displayTradeStrategyResults(resultContainer, results);
            break;
        case 'trade_advisor':
            displayTradeAdvisorResults(resultContainer, results);
            break;
        case 'risk_advisor':
            displayRiskAdvisorResults(resultContainer, results);
            break;
    }
    
    // Show the results container
    resultContainer.style.display = 'block';
}

// Helper function to display partial results when there's an error
function displayPartialResults(agentName, data) {
    const resultContainer = document.getElementById(`${agentName}Results`);
    if (!resultContainer) return;

    // Display basic company info if available
    if (data.company_info) {
        resultContainer.innerHTML += `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Company Information</h5>
                </div>
                <div class="card-body">
                    <table class="table table-sm">
                        <tbody>
                            <tr>
                                <th>Ticker</th>
                                <td>${data.company_info.ticker || 'N/A'}</td>
                            </tr>
                            <tr>
                                <th>Company Name</th>
                                <td>${data.company_info.name || 'N/A'}</td>
                            </tr>
                            <tr>
                                <th>Sector</th>
                                <td>${data.company_info.sector || 'N/A'}</td>
                            </tr>
                            <tr>
                                <th>Industry</th>
                                <td>${data.company_info.industry || 'N/A'}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

/**
 * Format large numbers into human readable format with B, M, K suffixes
 */
function formatFinancialNumber(num, isCurrency = true) {
    // Handle null/undefined/NaN/"N/A" cases
    if (num === null || num === undefined || num === "N/A" || isNaN(num)) {
        return "N/A";
    }

    const absNum = Math.abs(num);
    const prefix = num < 0 ? "-" : "";
    const symbol = isCurrency ? "$" : "";

    // Special handling for EPS/small decimals
    if (absNum < 1 && absNum > 0) {
        return `${prefix}${symbol}${num.toFixed(2)}`;
    }

    // Billions with 2 decimal places
    if (absNum >= 1.0e9) {
        return `${prefix}${symbol}${(absNum / 1.0e9).toFixed(2)}B`;
    }
    // Millions with 2 decimal places
    else if (absNum >= 1.0e6) {
        return `${prefix}${symbol}${(absNum / 1.0e6).toFixed(2)}M`;
    }
    // Thousands with 1 decimal place
    else if (absNum >= 1.0e3) {
        return `${prefix}${symbol}${(absNum / 1.0e3).toFixed(1)}K`;
    }
    // Regular numbers with 2 decimal places
    else {
        return `${prefix}${symbol}${absNum.toFixed(2)}`;
    }
}


/**
 * Format market cap in trillions (T) or billions (B)
 */
function formatMarketCap(value) {
    if (!value) return 'N/A';
    
    const trillion = 1000000000000;
    const billion = 1000000000;
    
    if (value >= trillion) {
        return `$${(value / trillion).toFixed(2)}T`;
    } else if (value >= billion) {
        return `$${(value / billion).toFixed(2)}B`;
    } else {
        return `$${value.toLocaleString()}`;
    }
}
/**
 * Display Data Analyst results
 */
function displayDataAnalystResults(container, results) {
    if (!results || !results.data) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i>
                No data available for analysis
            </div>`;
        return;
    }
    
    const stockData = results.data;
    
    // Extract nested data
    const overview = stockData.overview || {};
    const company_info = stockData.company_info || {};
    const financial_ratios = stockData.financial_ratios || {};
    const financial_statements = stockData.financial_statements || {};
    const news = stockData.news_sentiment || {};

    // Format market cap and volume
    const formattedMarketCap = formatFinancialNumber(overview.market_cap);
    const formattedVolume = overview.volume ? overview.volume.toLocaleString() : 'N/A';

    // Create HTML for the results
    let html = `
        <div class="row">
            <!-- Company Overview -->
            <div class="col-md-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0">Company Overview</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tbody>
                                <tr>
                                    <th class="stock-label">Company Name</th>
                                    <td class="stock-value">${company_info.name || overview.company_name || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="stock-label">Ticker</th>
                                    <td class="stock-value">${company_info.ticker || overview.ticker || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="stock-label">Sector</th>
                                    <td class="stock-value">${company_info.sector || overview.sector || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="stock-label">Industry</th>
                                    <td class="stock-value">${company_info.industry || overview.industry || 'N/A'}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Stock Overview -->
            <div class="col-md-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0">Stock Overview</h5>
                    </div>
                    <div class="card-body">
                        <div class="current-price-large mb-3">
                            <h2 class="stock-value">$${overview.current_price?.toFixed(2) || 'N/A'}</h2>
                            <span class="stock-overview-value ${overview.price_change >= 0 ? 'text-success' : 'text-danger'}">
                                ${overview.price_change >= 0 ? '+' : ''}${overview.price_change?.toFixed(2) || '0'}%
                            </span>
                        </div>
                        <table class="table table-sm">
                            <tbody>
                                
                                <tr>
                                    <th class="stock-label">Volume</th>
                                    <td class="stock-value">${formattedVolume}</td>
                                </tr>
                                <tr>
                                    <th class="stock-label">Market Cap</th>
                                    <td class="stock-value">${formattedMarketCap}</td>
                                </tr>
                                <tr>
                                    <th class="stock-label">52-Week Range</th>
                                    <td class="stock-value">${overview['52_week_range'] || 'N/A'}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Price Chart -->
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Price History</h5>
                    </div>
                    <div class="card-body">
                        <div class="tradingview-widget-container" id="tradingview_${company_info.ticker || overview.ticker}">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Financial Metrics Row -->
            <div class="row">
                <!-- Financial Ratios -->
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="mb-0">Financial Ratios</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-sm table-dark">
                                   <thead>
                                    <tr>
                                        <th style="color: #00f7ff; text-shadow: 0 0 2pxrgb(15, 134, 138), 0 0 2pxrgb(28, 72, 73);">Metric</th>
                                        <th class="text-end" style="color:rgb(243, 7, 243); text-shadow: 0 0 8pxrgb(99, 38, 99), 0 0 16pxrgb(105, 38, 105);">Value</th>
                                    </tr>
                                </thead>
                                    <tbody>
                                        <tr>
                                            <td>P/E Ratio</td>
                                            <td class="text-end">${financial_ratios.pe_ratio || overview.pe_ratio || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Current Ratio</td>
                                            <td class="text-end">${financial_ratios.current_ratio || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Debt to Equity</td>
                                            <td class="text-end">${financial_ratios.debt_to_equity || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Return on Assets</td>
                                            <td class="text-end">${financial_ratios.return_on_assets || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Return on Equity</td>
                                            <td class="text-end">${financial_ratios.return_on_equity || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Price to Book</td>
                                            <td class="text-end">${financial_ratios.price_to_book || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Profit Margin</td>
                                            <td class="text-end">${financial_ratios.profit_margin ? financial_ratios.profit_margin + '%' : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>EPS</td>
                                            <td class="text-end">$${financial_ratios.eps || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td>Dividend Yield</td>
                                            <td class="text-end">${financial_ratios.dividend_yield ? (financial_ratios.dividend_yield * 100).toFixed(2) + '%' : '0.00%'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Financial Statements -->
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="mb-0">Financial Statements</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-sm table-dark">
                                    <thead>
                                    <tr>
                                        <th style="color: #00f7ff; text-shadow: 0 0 2pxrgb(15, 134, 138), 0 0 2pxrgb(28, 72, 73);">Metric</th>
                                        <th class="text-end" style="color:rgb(243, 7, 243); text-shadow: 0 0 8pxrgb(99, 38, 99), 0 0 16pxrgb(105, 38, 105);">Value</th>
                                    </tr>
                                </thead>
                                    <tbody>
                                        <!-- Income Statement Data -->
                                        <tr>
                                            <td>Total Revenue</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.income_statement?.total_revenue)}</td>
                                        </tr>
                                        <tr>
                                            <td>Net Income</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.income_statement?.net_income)}</td>
                                        </tr>
                                        <tr>
                                            <td>EBITDA</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.income_statement?.ebitda)}</td>
                                        </tr>
                                        <tr>
                                            <td>EPS (Diluted)</td>
                                            <td class="text-end">${financial_statements.income_statement?.eps_diluted || 'N/A'}</td>
                                        </tr>
                                        
                                        <!-- Balance Sheet Data -->
                                        <tr>
                                            <td>Total Assets</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.balance_sheet?.total_assets)}</td>
                                        </tr>
                                        <tr>
                                            <td>Total Liabilities</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.balance_sheet?.total_liabilities)}</td>
                                        </tr>
                                        <tr>
                                            <td>Total Equity</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.balance_sheet?.total_equity)}</td>
                                        </tr>
                                        
                                        <!-- Cash Flow Data -->
                                        <tr>
                                            <td>Operating Cash Flow</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.cash_flow?.operating_cash_flow)}</td>
                                        </tr>
                                        <tr>
                                            <td>Capital Expenditure</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.cash_flow?.capital_expenditure)}</td>
                                        </tr>
                                        <tr>
                                            <td>Free Cash Flow</td>
                                            <td class="text-end">${formatFinancialNumber(financial_statements.cash_flow?.free_cash_flow)}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- News & Sentiment -->
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">News & Sentiment</h5>
                    </div>
                    <div class="card-body">
                        <!-- Sentiment Overview -->
                        <div class="mb-4">
                            <h6 class="text-muted mb-3">Sentiment Overview</h6>
                            <div class="d-flex align-items-center">
                                <span class="text-danger me-3">Bearish</span>
                                <div class="flex-grow-1 bg-secondary rounded-pill" style="height: 4px;">
                                    <div class="bg-primary rounded-pill" style="width: ${(news.sentiment_score || 0) * 100}%; height: 100%;"></div>
                                </div>
                                <span class="text-success ms-3">Bullish</span>
                                <span class="badge bg-secondary ms-3">${news.sentiment_score || '0.00'}</span>
                            </div>
                        </div>

                        <!-- Recent News -->
                        <div>
                            <h6 class="text-muted mb-3">Recent News</h6>
                            <div class="news-list" style="max-height: 400px; overflow-y: auto;">
                                ${news.news && news.news.length > 0 ? news.news.map(item => {
                                    // Debug logging for date values
                                    console.log('News item time_published:', item.time_published, typeof item.time_published);
                                    
                                    // Try to parse the date
                                    let formattedDate = 'N/A';
                                    if (item.time_published) {
                                        try {
                                            // Parse the specific format YYYYMMDDTHHMMSS
                                            const match = item.time_published.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})$/);
                                            if (match) {
                                                const [_, year, month, day, hour, minute, second] = match;
                                                const date = new Date(year, month - 1, day, hour, minute, second);
                                                formattedDate = date.toLocaleDateString('en-US', {
                                                    year: 'numeric',
                                                    month: 'long',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                });
                                            }
                                        } catch (error) {
                                            console.error('Error formatting date:', item.time_published, error);
                                        }
                                    }
                                    
                                    return `
                                    <div class="news-item mb-3">
                                        <div class="d-flex justify-content-between align-items-start">
                                            <h6 class="mb-2">${item.title}</h6>
                                            <span class="badge ${getSentimentBadgeClass(item.sentiment_score)}">${item.sentiment_score || '0.00'}</span>
                                        </div>
                                        <p class="text-muted mb-2">${item.summary || ''}</p>
                                        <div class="d-flex justify-content-between align-items-center">
                                            <small class="text-muted">${formattedDate}</small>
                                            <a href="${item.url}" target="_blank" class="btn btn-sm btn-outline-primary">Read More</a>
                                        </div>
                                    </div>
                                `}).join('') : `
                                    <div class="text-muted text-center">
                                        <p>No news articles available</p>
                                    </div>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add helper functions for news display
    function getSentimentBadgeClass(score) {
        if (!score) return 'bg-secondary';
        score = parseFloat(score);
        if (score >= 0.6) return 'bg-success';
        if (score <= 0.4) return 'bg-danger';
        return 'bg-secondary';
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        // Try parsing the date string directly
        let date = new Date(dateString);
        
        // If direct parsing fails, try parsing ISO format
        if (isNaN(date.getTime()) && typeof dateString === 'string') {
            // Try to parse ISO format (YYYY-MM-DD)
            const parts = dateString.split('-');
            if (parts.length === 3) {
                date = new Date(parts[0], parts[1] - 1, parts[2]);
            }
            
            // If still invalid, try parsing other common formats
            if (isNaN(date.getTime())) {
                // Try parsing Unix timestamp (seconds or milliseconds)
                const timestamp = parseInt(dateString);
                if (!isNaN(timestamp)) {
                    date = new Date(timestamp < 20000000000 ? timestamp * 1000 : timestamp);
                }
            }
        }
        
        // If all parsing attempts fail, return N/A
        if (isNaN(date.getTime())) {
            console.warn('Unable to parse date:', dateString);
            return 'N/A';
        }
        
        // Format the valid date
        try {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        } catch (error) {
            console.error('Error formatting date:', error);
            return 'N/A';
        }
    }

    // Update the container with the results
    container.innerHTML = html;

    // Initialize TradingView widget if we have a ticker
    const tickerSymbol = company_info.ticker || overview.ticker;
    if (tickerSymbol) {
        new TradingView.widget({
            "width": "100%",
            "height": 400,
            "symbol": tickerSymbol,
            "interval": "D",
            "timezone": "exchange",
            "theme": "dark",
            "style": "1",
            "toolbar_bg": "#1a1a1a",
            "enable_publishing": false,
            "hide_legend": true,
            "save_image": false,
            "container_id": `tradingview_${tickerSymbol}`
        });
    }

    // Initialize Bootstrap tabs after content is loaded
    const tabElements = container.querySelectorAll('[data-bs-toggle="tab"]');
    tabElements.forEach(tabElement => {
        const tab = new bootstrap.Tab(tabElement);
        
        // Add click handler to ensure proper tab switching
        tabElement.addEventListener('click', function(event) {
            event.preventDefault();
            tab.show();
            
            // Force opacity update for the tab content
            const targetId = this.getAttribute('data-bs-target');
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.remove('fade');
                void targetPane.offsetWidth; // Trigger reflow
                targetPane.classList.add('fade', 'show');
            }
        });
    });

    // Manually activate the first tab
    const firstTab = container.querySelector('[data-bs-toggle="tab"]');
    if (firstTab) {
        const tab = new bootstrap.Tab(firstTab);
        tab.show();
    }
}

/**
 * Display Trade Strategy results
 */
function displayTradeStrategyResults(container, results) {
    // Add debug logging
    console.log('Trade Strategy Results:', results);
    
    // Check for error state in results
    if (!results) {
        console.error('No results object received');
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i>
                No results received from the server
            </div>`;
        return;
    }
    
    // Check if we have data in the expected format
    if (!results.data) {
        console.error('No data property in results:', results);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i>
                ${results.error || 'No strategy data available'}
            </div>`;
        return;
    }

    const strategies = results.data;
    console.log('Strategy data:', strategies);
    
    // Check for missing or invalid strategy data
    if (!strategies.ma_strategy || !strategies.rsi_strategy || 
        strategies.ma_strategy.error || strategies.rsi_strategy.error) {
        console.error('Invalid strategy data:', {
            ma_strategy: strategies.ma_strategy,
            rsi_strategy: strategies.rsi_strategy
        });
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                Strategy data is incomplete or invalid
            </div>
            <div class="text-muted mt-3">
                <p>The strategy development process encountered issues:</p>
                <ul>
                    <li>Moving Average Strategy: ${strategies.ma_strategy?.error || 'Missing'}</li>
                    <li>RSI Strategy: ${strategies.rsi_strategy?.error || 'Missing'}</li>
                </ul>
                <p>Please try refreshing the page or adjusting your analysis parameters.</p>
            </div>`;
        return;
    }

    // Create HTML for the results
    let html = `
        <div class="row">
            <!-- Moving Average Crossover Strategy -->
            <div class="col-12 mb-4">
                <div class="card">
                <div class="card-header">
                        <h5 class="mb-0">Moving Average Crossover Strategy</h5>
                </div>
                <div class="card-body">
                        <div class="row">
                            <!-- Strategy Metrics -->
                            <div class="col-md-4">
                                <div class="metrics-grid">
                                    <div class="metric-card">
                                        <h3>${(strategies.ma_strategy.performance.win_rate * 100).toFixed(1)}%</h3>
                                        <p>Win Rate</p>
                        </div>
                                    <div class="metric-card">
                                        <h3>${strategies.ma_strategy.performance.total_trades}</h3>
                                        <p>Total Trades</p>
                        </div>
                                    <div class="metric-card">
                                        <h3>${strategies.ma_strategy.performance.cumulative_return.toFixed(2)}x</h3>
                                        <p>Return</p>
                        </div>
                                    <div class="metric-card">
                                        <h3>${strategies.ma_strategy.performance.sharpe_ratio.toFixed(2)}</h3>
                                        <p>Sharpe Ratio</p>
                        </div>
                    </div>
                                <div class="mt-4">
                                    <h6 class="text-muted mb-3">Current Status</h6>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span>Signal:</span>
                                        <span class="badge bg-${strategies.ma_strategy.performance.current_signal === 'BUY' ? 'success' : 'danger'}">
                                            ${strategies.ma_strategy.performance.current_signal}
                                        </span>
                    </div>
                                </div>
                            </div>
                            
                            <!-- Strategy Chart -->
                            <div class="col-md-8">
                                <div class="chart-container" style="height: 400px;">
                        <canvas id="maStrategyChart"></canvas>
                    </div>
                    </div>
                </div>
            </div>
                </div>
            </div>

            <!-- RSI Strategy -->
            <div class="col-12 mb-4">
                <div class="card">
                <div class="card-header">
                        <h5 class="mb-0">RSI Strategy</h5>
                </div>
                <div class="card-body">
                        <div class="row">
                            <!-- Strategy Metrics -->
                            <div class="col-md-4">
                                <div class="metrics-grid">
                                    <div class="metric-card">
                                        <h3>${(strategies.rsi_strategy.performance.win_rate * 100).toFixed(1)}%</h3>
                                        <p>Win Rate</p>
                        </div>
                                    <div class="metric-card">
                                        <h3>${strategies.rsi_strategy.performance.total_trades}</h3>
                                        <p>Total Trades</p>
                        </div>
                                    <div class="metric-card">
                                        <h3>${strategies.rsi_strategy.performance.cumulative_return.toFixed(2)}x</h3>
                                        <p>Return</p>
                        </div>
                                    <div class="metric-card">
                                        <h3>${strategies.rsi_strategy.performance.sharpe_ratio.toFixed(2)}</h3>
                                        <p>Sharpe Ratio</p>
                        </div>
                    </div>
                                <div class="mt-4">
                                    <h6 class="text-muted mb-3">Current Status</h6>
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span>RSI Value:</span>
                                        <span>${strategies.rsi_strategy.performance.current_rsi.toFixed(2)}</span>
                    </div>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span>Signal:</span>
                                        <span class="badge bg-${strategies.rsi_strategy.performance.current_signal === 'BUY' ? 'success' : 'danger'}">
                                            ${strategies.rsi_strategy.performance.current_signal}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Strategy Chart -->
                            <div class="col-md-8">
                                <div class="chart-container" style="height: 400px;">
                        <canvas id="rsiStrategyChart"></canvas>
                    </div>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>
            </div>
        `;
        
    // Update the container with the results
    container.innerHTML = html;

    // Initialize MA Strategy Chart
    const maCtx = document.getElementById('maStrategyChart').getContext('2d');
    new Chart(maCtx, {
        type: 'line',
        data: {
            labels: strategies.ma_strategy.signals.map(d => d.date),
            datasets: [{
                label: 'Price',
                data: strategies.ma_strategy.signals.map(d => d.price),
                borderColor: '#fff',
                tension: 0.1
            }, {
                label: 'Short MA',
                data: strategies.ma_strategy.signals.map(d => d.short_ma),
                borderColor: '#00ff88',
                tension: 0.1
            }, {
                label: 'Long MA',
                data: strategies.ma_strategy.signals.map(d => d.long_ma),
                borderColor: '#ff4d4d',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });

    // Initialize RSI Strategy Chart
    const rsiCtx = document.getElementById('rsiStrategyChart').getContext('2d');
    new Chart(rsiCtx, {
        type: 'line',
        data: {
            labels: strategies.rsi_strategy.signals.map(d => d.date),
            datasets: [{
                label: 'RSI',
                data: strategies.rsi_strategy.signals.map(d => d.rsi),
                borderColor: '#00ff88',
                tension: 0.1
            }, {
                label: 'Price',
                data: strategies.rsi_strategy.signals.map(d => d.price),
                borderColor: '#fff',
                tension: 0.1,
                yAxisID: 'price'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    min: 0,
                    max: 100
                },
                price: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}


function displayTradeAdvisorResults(container, results) {
    if (results.status !== 'completed') {
        container.innerHTML = `<div class="alert alert-warning">Trading recommendations not yet completed</div>`;
        return;
    }
    
    const recommendation = results.recommendation;
    
    if (!recommendation || recommendation.error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i> Error: ${recommendation.error || 'Failed to generate trading recommendation'}
            </div>
        `;
        return;
    }
    
    // Set color based on signal
    let signalColor = '';
    let signalIcon = '';
    
    if (recommendation.signal === 'bullish') {
        signalColor = 'success';
        signalIcon = 'fa-arrow-up';
    } else if (recommendation.signal === 'bearish') {
        signalColor = 'danger';
        signalIcon = 'fa-arrow-down';
    } else {
        signalColor = 'secondary';
        signalIcon = 'fa-minus';
    }
    
    // Create recommendation display
    container.innerHTML = `
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">Trading Recommendation for ${recommendation.ticker}</h5>
            </div>
            <div class="card-body">
                <div class="d-flex align-items-center mb-4">
                    <div class="p-3 rounded-circle bg-${signalColor} bg-opacity-25 me-3">
                        <i class="fas ${signalIcon} text-${signalColor} fa-2x"></i>
                    </div>
                    <div>
                        <h3 class="mb-0 text-${signalColor} text-capitalize">${recommendation.signal}</h3>
                        <div class="text-muted">Confidence: ${recommendation.confidence}%</div>
                    </div>
                </div>
                
                <div class="recommendation-box">
                    <p class="recommendation-text">${recommendation.recommendation_text}</p>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Technical Analysis</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-dark">
                                    <tbody>
                                        <tr>
                                            <td>Current Price</td>
                                            <td class="text-end">$${recommendation.technical_analysis.current_price}</td>
                                        </tr>
                                        <tr>
                                            <td>RSI (14)</td>
                                            <td class="text-end">${recommendation.technical_analysis.RSI}</td>
                                        </tr>
                                        ${recommendation.technical_analysis.MA20 ? `
                                        <tr>
                                            <td>MA20</td>
                                            <td class="text-end">$${recommendation.technical_analysis.MA20}</td>
                                        </tr>` : ''}
                                        ${recommendation.technical_analysis.MA50 ? `
                                        <tr>
                                            <td>MA50</td>
                                            <td class="text-end">$${recommendation.technical_analysis.MA50}</td>
                                        </tr>` : ''}
                                        ${recommendation.technical_analysis.MA200 ? `
                                        <tr>
                                            <td>MA200</td>
                                            <td class="text-end">$${recommendation.technical_analysis.MA200}</td>
                                        </tr>` : ''}
                                        <tr>
                                            <td>Overall Signal</td>
                                            <td class="text-end text-capitalize">${recommendation.technical_analysis.overall_signal}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Sentiment Analysis</h6>
                            </div>
                            <div class="card-body">
                                ${recommendation.sentiment_analysis.error ? `
                                <div class="alert alert-warning">
                                    ${recommendation.sentiment_analysis.error}
                                </div>` : `
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <span>Market Sentiment:</span>
                                    <span class="badge bg-${recommendation.sentiment_analysis.sentiment === 'bullish' ? 'success' : (recommendation.sentiment_analysis.sentiment === 'bearish' ? 'danger' : 'secondary')} text-capitalize">
                                        ${recommendation.sentiment_analysis.sentiment}
                                    </span>
                                </div>
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <span>Sentiment Score:</span>
                                    <span>${recommendation.sentiment_analysis.sentiment_score}</span>
                                </div>
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <span>Articles Analyzed:</span>
                                    <span>${recommendation.sentiment_analysis.articles_count}</span>
                                </div>
                                ${recommendation.sentiment_analysis.recent_articles && recommendation.sentiment_analysis.recent_articles.length > 0 ? `
                                <div class="mt-3">
                                    <small class="text-muted">Recent Headlines:</small>
                                    <ul class="list-unstyled mt-1">
                                        ${recommendation.sentiment_analysis.recent_articles.slice(0, 3).map(article => `
                                            <li class="small text-truncate">${article.title}</li>
                                        `).join('')}
                                    </ul>
                                </div>` : ''}
                                `}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Price Momentum</h6>
                            </div>
                            <div class="card-body">
                                ${recommendation.price_momentum.error ? `
                                <div class="alert alert-warning">
                                    ${recommendation.price_momentum.error}
                                </div>` : `
                                <table class="table table-sm table-dark">
                                    <tbody>
                                        ${Object.entries(recommendation.price_momentum)
                                            .filter(([key]) => key.includes('momentum') || key.includes('roc'))
                                            .map(([key, value]) => `
                                                <tr>
                                                    <td>${key.replace(/_/g, ' ').replace('day', '-Day')}</td>
                                                    <td class="text-end ${parseFloat(value) >= 0 ? 'text-success' : 'text-danger'}">
                                                        ${parseFloat(value) >= 0 ? '+' : ''}${value}%
                                                    </td>
                                                </tr>
                                            `).join('')}
                                    </tbody>
                                </table>
                                `}
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Earnings Analysis</h6>
                            </div>
                            <div class="card-body">
                                ${recommendation.earnings_analysis.error ? `
                                <div class="alert alert-warning">
                                    ${recommendation.earnings_analysis.error}
                                </div>` : `
                                <div class="mb-3">
                                    <small class="text-muted">Quarter:</small>
                                    <div>${recommendation.earnings_analysis.quarter || 'N/A'} ${recommendation.earnings_analysis.year || ''}</div>
                                </div>
                                
                                ${recommendation.earnings_analysis.insights && Object.keys(recommendation.earnings_analysis.insights).length > 0 ? `
                                <div class="mb-3">
                                    <small class="text-muted">Key Insights:</small>
                                    <ul class="mt-1">
                                        ${Object.entries(recommendation.earnings_analysis.insights)
                                            .map(([key, value]) => `<li>${key}: ${Array.isArray(value) && value.length > 0 ? value[0].join(' ') : 'N/A'}</li>`)
                                            .join('')}
                                    </ul>
                                </div>` : ''}
                                
                                <div>
                                    <small class="text-muted">Summary:</small>
                                    <p class="small mt-1">${recommendation.earnings_analysis.summary || 'No summary available'}</p>
                                </div>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Display Risk Advisor results
 */
function displayRiskAdvisorResults(container, results) {
    if (results.status !== 'completed') {
        container.innerHTML = `<div class="alert alert-warning">Risk assessment not yet completed</div>`;
        return;
    }
    
    const assessment = results.risk_assessment;
    
    if (!assessment || assessment.error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i> Error: ${assessment.error || 'Failed to generate risk assessment'}
            </div>
        `;
        return;
    }
    
    // Create risk assessment display
    container.innerHTML = `
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">Risk Assessment for ${assessment.ticker}</h5>
            </div>
            <div class="card-body">
                <div class="d-flex align-items-center mb-4">
                    <div class="risk-level ${assessment.risk_summary.risk_level.toLowerCase()}">${assessment.risk_summary.risk_level} Risk</div>
                    <div class="ms-3">
                        <div class="text-muted">Risk Score: ${assessment.risk_summary.risk_score}/100</div>
                    </div>
                </div>
                
                ${assessment.risk_summary.key_risk_factors.length > 0 ? `
                <div class="mb-4">
                    <h6>Key Risk Factors:</h6>
                    ${assessment.risk_summary.key_risk_factors.map(factor => `
                        <div class="risk-factor">${factor}</div>
                    `).join('')}
                </div>` : ''}
                
                <div class="mb-4">
                    <h6>Recommendations:</h6>
                    ${assessment.risk_summary.recommendations.map(recommendation => `
                        <div class="recommendation-item">${recommendation}</div>
                    `).join('')}
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Volatility</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-dark">
                                    <tbody>
                                        <tr>
                                            <td>Recent Volatility</td>
                                            <td class="text-end">${assessment.detailed_metrics.volatility.recent_volatility}%</td>
                                        </tr>
                                        <tr>
                                            <td>Average Volatility</td>
                                            <td class="text-end">${assessment.detailed_metrics.volatility.average_volatility}%</td>
                                        </tr>
                                        <tr>
                                            <td>Volatility Level</td>
                                            <td class="text-end text-capitalize">${assessment.detailed_metrics.volatility.volatility_level}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Drawdown Analysis</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-dark">
                                    <tbody>
                                        <tr>
                                            <td>Maximum Drawdown</td>
                                            <td class="text-end text-danger">${assessment.detailed_metrics.maximum_drawdown.max_drawdown}%</td>
                                        </tr>
                                        <tr>
                                            <td>Current Drawdown</td>
                                            <td class="text-end ${parseFloat(assessment.detailed_metrics.maximum_drawdown.current_drawdown) < 0 ? 'text-danger' : 'text-success'}">${assessment.detailed_metrics.maximum_drawdown.current_drawdown}%</td>
                                        </tr>
                                        <tr>
                                            <td>Drawdown Risk</td>
                                            <td class="text-end text-capitalize">${assessment.detailed_metrics.maximum_drawdown.drawdown_risk}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Value at Risk (VaR)</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-dark">
                                    <tbody>
                                        <tr>
                                            <td>Confidence Level</td>
                                            <td class="text-end">${assessment.detailed_metrics.value_at_risk.confidence_level}%</td>
                                        </tr>
                                        <tr>
                                            <td>Time Horizon</td>
                                            <td class="text-end">${assessment.detailed_metrics.value_at_risk.time_horizon} day(s)</td>
                                        </tr>
                                        <tr>
                                            <td>VaR (Percentage)</td>
                                            <td class="text-end text-danger">${Math.abs(assessment.detailed_metrics.value_at_risk.var_percentage)}%</td>
                                        </tr>
                                        <tr>
                                            <td>VaR ($10,000 investment)</td>
                                            <td class="text-end text-danger">$${Math.abs(assessment.detailed_metrics.value_at_risk.dollar_var)}</td>
                                        </tr>
                                    </tbody>
                                </table>
                                <div class="mt-2 small text-muted">
                                    ${assessment.detailed_metrics.value_at_risk.interpretation}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Market Risk (Beta)</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-dark">
                                    <tbody>
                                        <tr>
                                            <td>Beta</td>
                                            <td class="text-end">${assessment.detailed_metrics.beta.beta}</td>
                                        </tr>
                                        <tr>
                                            <td>Market Index</td>
                                            <td class="text-end">${assessment.detailed_metrics.beta.market_index}</td>
                                        </tr>
                                        <tr>
                                            <td>Interpretation</td>
                                            <td class="text-end">${assessment.detailed_metrics.beta.interpretation}</td>
                                        </tr>
                                    </tbody>
                                </table>
                                <div class="mt-3">
                                    <div class="d-flex align-items-center">
                                        <div class="flex-grow-1 bg-secondary rounded-pill" style="height: 6px;">
                                            <div class="bg-primary rounded-pill" style="width: ${Math.min(assessment.detailed_metrics.beta.beta * 50, 100)}%; height: 6px;"></div>
                                        </div>
                                        <div class="ms-2 small">β = ${assessment.detailed_metrics.beta.beta}</div>
                                    </div>
                                    <div class="d-flex justify-content-between mt-1">
                                        <small class="text-muted">Lower Risk</small>
                                        <small class="text-muted">Higher Risk</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Submit the technical indicators form
 */
function submitIndicatorsForm(formData) {
    const resultsContainer = document.getElementById('indicatorResults');
    const loadingSpinner = document.getElementById('indicatorLoading');
    
    if (!resultsContainer || !loadingSpinner) return;
    
    // Show loading spinner
    loadingSpinner.style.display = 'block';
    resultsContainer.innerHTML = '';
    
    // Make API request
    fetch('/technical_indicators', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner
        loadingSpinner.style.display = 'none';
        
        // Display results
        if (data.error) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> ${data.error}
                </div>
            `;
        } else if (data.results) {
            displayIndicatorResults(resultsContainer, data.results);
        } else {
            resultsContainer.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i> No results returned
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        loadingSpinner.style.display = 'none';
        resultsContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i> An error occurred while processing the request
            </div>
        `;
    });
}

/**
 * Display technical indicator results
 */
function displayIndicatorResults(container, results) {
    const timestamps = Object.keys(results).sort();
    
    if (timestamps.length === 0) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> No data available for the selected parameters
            </div>
        `;
        return;
    }
    
    // Prepare data for chart
    const chartData = timestamps.map(timestamp => {
        return {
            timestamp: timestamp,
            value: Object.values(results[timestamp])[0]
        };
    });
    
    container.innerHTML = `
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">Indicator Results</h5>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="indicatorChart"></canvas>
                </div>
                
                <div class="table-responsive mt-4">
                    <table class="table table-sm table-dark">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${timestamps.slice(0, 10).map(timestamp => `
                                <tr>
                                    <td>${new Date(timestamp).toLocaleDateString()}</td>
                                    <td>${Object.values(results[timestamp])[0]}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // Create chart
    createIndicatorChart('indicatorChart', chartData);
}
