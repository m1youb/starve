// App State
let attackRunning = false;
let updateInterval = null;

// DOM Elements
const interfaceSelect = document.getElementById('interfaceSelect');
const dhcpServerInput = document.getElementById('dhcpServer');
const discoverBtn = document.getElementById('discoverBtn');
const attackBtn = document.getElementById('attackBtn');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = statusIndicator.querySelector('.status-text');
const themeToggle = document.getElementById('themeToggle');

// Network Info Elements
const routerIpEl = document.getElementById('routerIp');
const subnetMaskEl = document.getElementById('subnetMask');
const dhcpServerInfoEl = document.getElementById('dhcpServerInfo');
const poolRangeEl = document.getElementById('poolRange');

// Table Elements
const stolenIpsTable = document.getElementById('stolenIpsTable');
const ipCounter = document.getElementById('ipCounter');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadInterfaces();
    initTheme();
    setupEventListeners();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Event Listeners
function setupEventListeners() {
    themeToggle.addEventListener('click', toggleTheme);
    discoverBtn.addEventListener('click', discoverDHCPServer);
    attackBtn.addEventListener('click', toggleAttack);
}

// Load Network Interfaces
async function loadInterfaces() {
    try {
        const response = await fetch('/api/interfaces');
        const interfaces = await response.json();
        
        interfaceSelect.innerHTML = '<option value="">Select an interface...</option>';
        
        interfaces.forEach(iface => {
            const option = document.createElement('option');
            option.value = iface.name;
            option.textContent = `${iface.name} (${iface.ip})`;
            interfaceSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading interfaces:', error);
        showNotification('Failed to load network interfaces', 'error');
    }
}

// Discover DHCP Server
async function discoverDHCPServer() {
    const interface = interfaceSelect.value;
    
    if (!interface) {
        showNotification('Please select a network interface first', 'error');
        return;
    }
    
    // Update status
    updateStatus('discovering', 'Discovering DHCP server...');
    discoverBtn.disabled = true;
    
    try {
        const response = await fetch('/api/discover', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ interface })
        });
        
        if (response.ok) {
            const data = await response.json();
            dhcpServerInput.value = data.server_ip;
            updateNetworkInfo(data.network_info);
            showNotification('DHCP server discovered successfully', 'success');
            updateStatus('idle', 'Ready');
        } else {
            const error = await response.json();
            showNotification(error.error || 'DHCP server not found', 'error');
            updateStatus('idle', 'Idle');
        }
    } catch (error) {
        console.error('Discovery error:', error);
        showNotification('Failed to discover DHCP server', 'error');
        updateStatus('idle', 'Idle');
    } finally {
        discoverBtn.disabled = false;
    }
}

// Update Network Info Display
function updateNetworkInfo(info) {
    if (info.router_ip) {
        routerIpEl.textContent = info.router_ip;
        dhcpServerInfoEl.textContent = info.server_ip;
    }
    if (info.subnet_mask) {
        subnetMaskEl.textContent = info.subnet_mask;
    }
    if (info.dhcp_pool_start) {
        poolRangeEl.textContent = `${info.dhcp_pool_start} - ${info.dhcp_pool_end}`;
    }
}

// Toggle Attack
async function toggleAttack() {
    if (attackRunning) {
        await stopAttack();
    } else {
        await startAttack();
    }
}

// Start Attack
async function startAttack() {
    const interface = interfaceSelect.value;
    const dhcpServer = dhcpServerInput.value.trim();
    
    if (!interface) {
        showNotification('Please select a network interface', 'error');
        return;
    }
    
    if (!dhcpServer) {
        showNotification('Please enter DHCP server IP or use Discover', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/attack/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ interface, dhcp_server: dhcpServer })
        });
        
        if (response.ok) {
            attackRunning = true;
            updateAttackUI(true);
            updateStatus('attacking', 'Attack in progress...');
            startStatusUpdates();
            showNotification('Attack started', 'success');
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to start attack', 'error');
        }
    } catch (error) {
        console.error('Attack start error:', error);
        showNotification('Failed to start attack', 'error');
    }
}

// Stop Attack
async function stopAttack() {
    try {
        const response = await fetch('/api/attack/stop', {
            method: 'POST'
        });
        
        if (response.ok) {
            attackRunning = false;
            updateAttackUI(false);
            updateStatus('idle', 'Attack stopped');
            stopStatusUpdates();
            showNotification('Attack stopped', 'success');
        }
    } catch (error) {
        console.error('Attack stop error:', error);
        showNotification('Failed to stop attack', 'error');
    }
}

// Update UI for Attack State
function updateAttackUI(attacking) {
    if (attacking) {
        attackBtn.classList.add('attacking');
        attackBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
            </svg>
            Stop Attack
        `;
        interfaceSelect.disabled = true;
        dhcpServerInput.disabled = true;
        discoverBtn.disabled = true;
    } else {
        attackBtn.classList.remove('attacking');
        attackBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            Start Attack
        `;
        interfaceSelect.disabled = false;
        dhcpServerInput.disabled = false;
        discoverBtn.disabled = false;
    }
}

// Start Status Updates
function startStatusUpdates() {
    updateInterval = setInterval(updateAttackStatus, 500);
}

// Stop Status Updates
function stopStatusUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// Update Attack Status
async function updateAttackStatus() {
    try {
        const response = await fetch('/api/attack/status');
        const data = await response.json();
        
        if (!data.running && attackRunning) {
            // Attack stopped on server side
            attackRunning = false;
            updateAttackUI(false);
            updateStatus('idle', 'Attack completed');
            stopStatusUpdates();
        }
        
        // Update stolen IPs table
        updateStolenIpsTable(data.stolen_ips);
        
        // Update network info if available
        if (data.network_info && Object.keys(data.network_info).length > 0) {
            updateNetworkInfo(data.network_info);
        }
    } catch (error) {
        console.error('Status update error:', error);
    }
}

// Update Stolen IPs Table
function updateStolenIpsTable(ips) {
    ipCounter.textContent = `${ips.length} IP${ips.length !== 1 ? 's' : ''}`;
    
    if (ips.length === 0) {
        stolenIpsTable.innerHTML = `
            <tr class="empty-state">
                <td colspan="3">No IPs exhausted yet. Start an attack to see results.</td>
            </tr>
        `;
        return;
    }
    
    // Get current IPs in table
    const currentIps = new Set(
        Array.from(stolenIpsTable.querySelectorAll('tr:not(.empty-state)'))
            .map(row => row.cells[0]?.textContent)
    );
    
    // Update table
    const fragment = document.createDocumentFragment();
    
    ips.forEach(ip => {
        if (!currentIps.has(ip.ip)) {
            const row = document.createElement('tr');
            row.classList.add('ip-row-enter');
            row.innerHTML = `
                <td>${ip.ip}</td>
                <td>${ip.mac}</td>
                <td>${ip.time}</td>
            `;
            fragment.appendChild(row);
        }
    });
    
    if (fragment.childNodes.length > 0) {
        if (stolenIpsTable.querySelector('.empty-state')) {
            stolenIpsTable.innerHTML = '';
        }
        stolenIpsTable.appendChild(fragment);
    }
}

// Update Status Indicator
function updateStatus(state, text) {
    statusIndicator.className = `status-indicator status-${state}`;
    statusText.textContent = text;
}

// Show Notification (simple implementation)
function showNotification(message, type) {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Could be enhanced with a toast notification system
}
