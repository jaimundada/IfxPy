// Dashboard JavaScript
class TradingDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.isTrading = false;
        this.positions = [];
        this.trades = [];
        this.equityCurve = [];
        
        this.init();
    }
    
    init() {
        this.initializeSocketIO();
        this.setupEventListeners();
        this.initializeCharts();
        this.setupNavigation();
        this.loadInitialData();
        
        // Set default dates for backtest
        this.setDefaultDates();
    }
    
    initializeSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.updateConnectionStatus('connected');
            this.showAlert('Connected to trading server', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.updateConnectionStatus('disconnected');
            this.showAlert('Disconnected from trading server', 'warning');
        });
        
        this.socket.on('trade_executed', (data) => {
            this.handleTradeExecution(data);
        });
        
        this.socket.on('position_closed', (data) => {
            this.handlePositionClosed(data);
        });
        
        this.socket.on('trading_error', (data) => {
            this.showAlert(`Trading Error: ${data.error}`, 'danger');
        });
        
        this.socket.on('market_update', (data) => {
            this.handleMarketUpdate(data);
        });
    }
    
    setupEventListeners() {
        // Trading controls
        document.getElementById('start-trading').addEventListener('click', () => {
            this.startTrading();
        });
        
        document.getElementById('stop-trading').addEventListener('click', () => {
            this.stopTrading();
        });
        
        document.getElementById('emergency-stop').addEventListener('click', () => {
            this.emergencyStop();
        });
        
        // Backtest form
        document.getElementById('backtest-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.runBacktest();
        });
        
        // Settings
        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(e.target.getAttribute('href'));
            });
        });
    }
    
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active class from all links
                navLinks.forEach(l => l.classList.remove('active'));
                
                // Add active class to clicked link
                link.classList.add('active');
                
                // Handle section display
                const section = link.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
    }
    
    showSection(section) {
        // Hide all sections first
        document.getElementById('backtest-section').style.display = 'none';
        
        switch(section) {
            case 'backtest':
                document.getElementById('backtest-section').style.display = 'block';
                break;
            case 'settings':
                const settingsModal = new bootstrap.Modal(document.getElementById('settings-modal'));
                settingsModal.show();
                break;
            default:
                // Dashboard is always visible
                break;
        }
    }
    
    initializeCharts() {
        // Equity curve chart
        const equityCtx = document.getElementById('equity-chart').getContext('2d');
        this.charts.equity = new Chart(equityCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Portfolio: ₹' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        // Strategy performance chart
        const strategyCtx = document.getElementById('strategy-chart').getContext('2d');
        this.charts.strategy = new Chart(strategyCtx, {
            type: 'doughnut',
            data: {
                labels: ['Momentum', 'Mean Reversion', 'Volatility', 'Options'],
                datasets: [{
                    data: [25, 30, 20, 25],
                    backgroundColor: [
                        '#0d6efd',
                        '#6f42c1',
                        '#fd7e14',
                        '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    setDefaultDates() {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setMonth(startDate.getMonth() - 1);
        
        document.getElementById('backtest-start-date').value = startDate.toISOString().split('T')[0];
        document.getElementById('backtest-end-date').value = endDate.toISOString().split('T')[0];
    }
    
    async startTrading() {
        try {
            const symbols = Array.from(document.getElementById('trading-symbols').selectedOptions)
                .map(option => option.value);
            
            const strategies = {
                momentum: document.getElementById('momentum-strategy').checked,
                mean_reversion: document.getElementById('mean-reversion-strategy').checked,
                volatility: document.getElementById('volatility-strategy').checked,
                options_selling: document.getElementById('options-selling-strategy').checked,
                options_buying: document.getElementById('options-buying-strategy').checked
            };
            
            const response = await fetch('/api/start_trading', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    symbols: symbols,
                    strategies: strategies
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.isTrading = true;
                this.updateTradingControls();
                this.showAlert('Trading started successfully', 'success');
            } else {
                this.showAlert(`Failed to start trading: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error starting trading: ${error.message}`, 'danger');
        }
    }
    
    async stopTrading() {
        try {
            const response = await fetch('/api/stop_trading', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.isTrading = false;
                this.updateTradingControls();
                this.showAlert('Trading stopped', 'info');
            } else {
                this.showAlert(`Failed to stop trading: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error stopping trading: ${error.message}`, 'danger');
        }
    }
    
    emergencyStop() {
        if (confirm('Are you sure you want to trigger emergency stop? This will close all positions immediately.')) {
            this.stopTrading();
            this.showAlert('Emergency stop triggered!', 'warning');
        }
    }
    
    updateTradingControls() {
        const startBtn = document.getElementById('start-trading');
        const stopBtn = document.getElementById('stop-trading');
        
        if (this.isTrading) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Trading Active';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Start Trading';
        }
    }
    
    async runBacktest() {
        try {
            const submitBtn = document.querySelector('#backtest-form button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Running...';
            submitBtn.disabled = true;
            
            const config = {
                symbol: document.getElementById('backtest-symbol').value,
                start_date: document.getElementById('backtest-start-date').value,
                end_date: document.getElementById('backtest-end-date').value,
                initial_capital: parseInt(document.getElementById('backtest-capital').value),
                strategy: document.getElementById('backtest-strategy').value
            };
            
            const response = await fetch('/api/backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.displayBacktestResults(result.results);
                this.showAlert('Backtest completed successfully', 'success');
            } else {
                this.showAlert(`Backtest failed: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error running backtest: ${error.message}`, 'danger');
        } finally {
            const submitBtn = document.querySelector('#backtest-form button[type="submit"]');
            submitBtn.innerHTML = '<i class="fas fa-play"></i> Run Backtest';
            submitBtn.disabled = false;
        }
    }
    
    displayBacktestResults(results) {
        const container = document.getElementById('backtest-results');
        
        const html = `
            <div class="row">
                <div class="col-md-3">
                    <div class="backtest-metric ${results.total_return >= 0 ? 'positive' : 'negative'}">
                        <h6>Total Return</h6>
                        <div class="value">${results.total_return.toFixed(2)}%</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="backtest-metric">
                        <h6>Sharpe Ratio</h6>
                        <div class="value">${results.sharpe_ratio.toFixed(2)}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="backtest-metric">
                        <h6>Max Drawdown</h6>
                        <div class="value negative">${results.max_drawdown.toFixed(2)}%</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="backtest-metric">
                        <h6>Win Rate</h6>
                        <div class="value">${results.win_rate.toFixed(1)}%</div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-4">
                    <div class="backtest-metric">
                        <h6>Total Trades</h6>
                        <div class="value">${results.total_trades}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="backtest-metric">
                        <h6>Profit Factor</h6>
                        <div class="value">${results.profit_factor.toFixed(2)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="backtest-metric">
                        <h6>Final Value</h6>
                        <div class="value">₹${results.final_portfolio_value.toLocaleString()}</div>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <h6>Equity Curve</h6>
                <canvas id="backtest-equity-chart" width="400" height="200"></canvas>
            </div>
        `;
        
        container.innerHTML = html;
        
        // Create equity curve chart for backtest
        const ctx = document.getElementById('backtest-equity-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: results.equity_curve.map(point => new Date(point.timestamp).toLocaleDateString()),
                datasets: [{
                    label: 'Portfolio Value',
                    data: results.equity_curve.map(point => point.total_value),
                    borderColor: results.total_return >= 0 ? '#28a745' : '#dc3545',
                    backgroundColor: results.total_return >= 0 ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    async loadInitialData() {
        await this.refreshPositions();
        await this.loadPortfolioData();
    }
    
    async refreshPositions() {
        try {
            const response = await fetch('/api/positions');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.positions = result.positions;
                this.updatePositionsTable();
            }
        } catch (error) {
            console.error('Error loading positions:', error);
        }
    }
    
    async loadPortfolioData() {
        // This would load portfolio summary data
        // For now, we'll use dummy data
        this.updatePortfolioCards({
            portfolio_value: 150000,
            daily_pnl: 2500,
            active_positions: 3,
            win_rate: 65.5,
            risk_exposure: 15.2
        });
    }
    
    updatePortfolioCards(data) {
        document.getElementById('portfolio-value').textContent = `₹${data.portfolio_value.toLocaleString()}`;
        
        const dailyPnlElement = document.getElementById('daily-pnl');
        dailyPnlElement.textContent = `₹${data.daily_pnl.toLocaleString()}`;
        dailyPnlElement.className = data.daily_pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
        
        document.getElementById('active-positions').textContent = data.active_positions;
        document.getElementById('win-rate').textContent = `${data.win_rate}%`;
        document.getElementById('risk-exposure').textContent = `${data.risk_exposure}%`;
    }
    
    updatePositionsTable() {
        const tbody = document.querySelector('#positions-table tbody');
        
        if (this.positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No active positions</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.positions.map(position => {
            const pnl = this.calculatePositionPnL(position);
            const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            
            return `
                <tr>
                    <td>${position.symbol}</td>
                    <td><span class="strategy-${position.strategy}">${position.strategy}</span></td>
                    <td><span class="position-${position.type.toLowerCase()}">${position.type}</span></td>
                    <td>${position.quantity}</td>
                    <td>₹${position.entry_price.toFixed(2)}</td>
                    <td>₹${position.current_price.toFixed(2)}</td>
                    <td class="${pnlClass}">₹${pnl.toFixed(2)}</td>
                    <td class="${pnlClass}">${position.pnl_percent.toFixed(2)}%</td>
                    <td>₹${position.target_price.toFixed(2)}</td>
                    <td>₹${position.stop_loss_price.toFixed(2)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" onclick="dashboard.closePosition('${position.id}')">
                            Close
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    calculatePositionPnL(position) {
        // This would calculate real P&L based on current price
        // For now, return a dummy calculation
        return (position.current_price - position.entry_price) * position.quantity;
    }
    
    async closePosition(positionId) {
        if (confirm('Are you sure you want to close this position?')) {
            try {
                // Implementation for closing position
                this.showAlert('Position close request sent', 'info');
            } catch (error) {
                this.showAlert(`Error closing position: ${error.message}`, 'danger');
            }
        }
    }
    
    handleTradeExecution(data) {
        this.showAlert(`Trade executed: ${data.signal.type} ${data.signal.symbol}`, 'success');
        this.refreshPositions();
        this.addTradeToHistory(data);
    }
    
    handlePositionClosed(data) {
        this.showAlert(`Position closed: ${data.signal.symbol}`, 'info');
        this.refreshPositions();
    }
    
    handleMarketUpdate(data) {
        // Update real-time market data
        this.updatePositionsTable();
    }
    
    addTradeToHistory(tradeData) {
        const tbody = document.querySelector('#trades-table tbody');
        
        // If table is empty, clear the "no trades" message
        if (tbody.children.length === 1 && tbody.children[0].children.length === 1) {
            tbody.innerHTML = '';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(tradeData.timestamp).toLocaleTimeString()}</td>
            <td>${tradeData.signal.symbol}</td>
            <td><span class="strategy-${tradeData.signal.strategy}">${tradeData.signal.strategy}</span></td>
            <td><span class="position-${tradeData.signal.type.toLowerCase()}">${tradeData.signal.type}</span></td>
            <td>${tradeData.signal.quantity || 'N/A'}</td>
            <td>₹${tradeData.signal.price || 'Market'}</td>
            <td class="pnl-neutral">-</td>
            <td><span class="badge bg-success">Executed</span></td>
        `;
        
        tbody.insertBefore(row, tbody.firstChild);
        
        // Keep only last 20 trades
        while (tbody.children.length > 20) {
            tbody.removeChild(tbody.lastChild);
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        
        switch (status) {
            case 'connected':
                statusElement.className = 'badge status-connected';
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected';
                break;
            case 'disconnected':
                statusElement.className = 'badge status-disconnected';
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
                break;
            default:
                statusElement.className = 'badge bg-secondary';
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Connecting...';
        }
    }
    
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show slide-in`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    saveSettings() {
        const settings = {
            maxRiskPerTrade: document.getElementById('max-risk-per-trade').value,
            maxPortfolioRisk: document.getElementById('max-portfolio-risk').value,
            defaultStopLoss: document.getElementById('default-stop-loss').value,
            defaultTarget: document.getElementById('default-target').value,
            activeBroker: document.getElementById('active-broker').value,
            dataSource: document.getElementById('data-source').value,
            paperTrading: document.getElementById('paper-trading').checked,
            autoTrading: document.getElementById('auto-trading').checked
        };
        
        // Save settings (this would typically make an API call)
        localStorage.setItem('tradingSettings', JSON.stringify(settings));
        
        this.showAlert('Settings saved successfully', 'success');
        
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('settings-modal'));
        modal.hide();
    }
    
    loadSettings() {
        const saved = localStorage.getItem('tradingSettings');
        if (saved) {
            const settings = JSON.parse(saved);
            
            document.getElementById('max-risk-per-trade').value = settings.maxRiskPerTrade || 2;
            document.getElementById('max-portfolio-risk').value = settings.maxPortfolioRisk || 6;
            document.getElementById('default-stop-loss').value = settings.defaultStopLoss || 2;
            document.getElementById('default-target').value = settings.defaultTarget || 4;
            document.getElementById('active-broker').value = settings.activeBroker || 'angel_one';
            document.getElementById('data-source').value = settings.dataSource || 'auto';
            document.getElementById('paper-trading').checked = settings.paperTrading !== false;
            document.getElementById('auto-trading').checked = settings.autoTrading || false;
        }
    }
}

// Global functions
function refreshPositions() {
    dashboard.refreshPositions();
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new TradingDashboard();
    dashboard.loadSettings();
});