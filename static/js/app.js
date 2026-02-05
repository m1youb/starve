// App State
let attackRunning = false;
let updateInterval = null;

// DOM Elements
const interfaceSelect = document.getElementById('interfaceSelect');
const dhcpServerInput = document.getElementById('dhcpServer');
const discoverBtn = document.getElementById('discoverBtn');
const attackBtn = document.getElementById('attackBtn');
const releaseAllBtn = document.getElementById('releaseAllBtn');
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
    releaseAllBtn.addEventListener('click', releaseAllIPs);
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

    // Show/hide Release All button
    if (ips.length > 0) {
        releaseAllBtn.style.display = 'flex';
    } else {
        releaseAllBtn.style.display = 'none';
    }

    if (ips.length === 0) {
        stolenIpsTable.innerHTML = `
            <tr class="empty-state">
                <td colspan="4">No IPs exhausted yet. Start an attack to see results.</td>
            </tr>
        `;
        return;
    }

    // Get current IPs in table for comparison
    const currentIps = new Map();
    Array.from(stolenIpsTable.querySelectorAll('tr:not(.empty-state)')).forEach(row => {
        const ipAddress = row.cells[0]?.textContent;
        if (ipAddress) {
            currentIps.set(ipAddress, row);
        }
    });

    // Get IPs from backend
    const backendIps = new Set(ips.map(ip => ip.ip));

    // Remove rows that no longer exist in backend (were released)
    currentIps.forEach((row, ipAddress) => {
        if (!backendIps.has(ipAddress)) {
            row.classList.add('ip-row-exit');
            setTimeout(() => row.remove(), 300);
        }
    });

    // Add new IPs that aren't in the table yet
    const fragment = document.createDocumentFragment();

    ips.forEach(ip => {
        if (!currentIps.has(ip.ip)) {
            const row = document.createElement('tr');
            row.classList.add('ip-row-enter');
            row.setAttribute('data-ip', ip.ip);
            row.innerHTML = `
                <td>${ip.ip}</td>
                <td>${ip.mac}</td>
                <td>${ip.time}</td>
                <td>
                    <button class="btn-release-single" onclick="releaseSingleIP('${ip.ip}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Release
                    </button>
                </td>
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

// Release Single IP
async function releaseSingleIP(ipAddress) {
    const interface = interfaceSelect.value;
    const dhcpServer = dhcpServerInput.value.trim();

    if (!interface || !dhcpServer) {
        showNotification('Missing interface or DHCP server information', 'error');
        return;
    }

    // Disable the button
    const row = stolenIpsTable.querySelector(`tr[data-ip="${ipAddress}"]`);
    if (row) {
        const btn = row.querySelector('.btn-release-single');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Releasing...';
        }
    }

    try {
        const response = await fetch('/api/attack/release', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ip: ipAddress,
                interface: interface,
                dhcp_server: dhcpServer
            })
        });

        if (response.ok) {
            const data = await response.json();
            showNotification(`IP ${ipAddress} released successfully`, 'success');

            // Remove the row from table
            if (row) {
                row.classList.add('ip-row-exit');
                setTimeout(() => row.remove(), 300);
            }

            // Update counter
            ipCounter.textContent = `${data.remaining} IP${data.remaining !== 1 ? 's' : ''}`;

            // Hide Release All button if no IPs left
            if (data.remaining === 0) {
                releaseAllBtn.style.display = 'none';
                stolenIpsTable.innerHTML = `
                    <tr class="empty-state">
                        <td colspan="4">No IPs exhausted yet. Start an attack to see results.</td>
                    </tr>
                `;
            }
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to release IP', 'error');

            // Re-enable button
            if (row) {
                const btn = row.querySelector('.btn-release-single');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Release
                    `;
                }
            }
        }
    } catch (error) {
        console.error('Release error:', error);
        showNotification('Failed to release IP', 'error');
    }
}

// Release All IPs
async function releaseAllIPs() {
    const interface = interfaceSelect.value;
    const dhcpServer = dhcpServerInput.value.trim();

    if (!interface || !dhcpServer) {
        showNotification('Missing interface or DHCP server information', 'error');
        return;
    }

    // Confirm action
    if (!confirm('Are you sure you want to release all stolen IP addresses?')) {
        return;
    }

    // Disable button and update text
    releaseAllBtn.disabled = true;
    const originalHTML = releaseAllBtn.innerHTML;
    releaseAllBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
        Releasing...
    `;

    try {
        const response = await fetch('/api/attack/release-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                interface: interface,
                dhcp_server: dhcpServer
            })
        });

        if (response.ok) {
            const data = await response.json();
            showNotification(`Released ${data.released} IP(s) successfully`, 'success');

            // Clear table
            stolenIpsTable.innerHTML = `
                <tr class="empty-state">
                    <td colspan="4">No IPs exhausted yet. Start an attack to see results.</td>
                </tr>
            `;

            // Update counter and hide button
            ipCounter.textContent = '0 IPs';
            releaseAllBtn.style.display = 'none';
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to release IPs', 'error');
        }
    } catch (error) {
        console.error('Release all error:', error);
        showNotification('Failed to release all IPs', 'error');
    } finally {
        releaseAllBtn.disabled = false;
        releaseAllBtn.innerHTML = originalHTML;
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
