const API_URL = "/api/nodes";
const nodesGrid = document.getElementById('nodes-grid');
const template = document.getElementById('node-template');

async function fetchNodes() {
    try {
        const response = await fetch(API_URL);
        const nodes = await response.json();
        renderNodes(nodes);
    } catch (error) {
        console.error("Error fetching nodes:", error);
    }
}

function renderNodes(nodes) {
    nodesGrid.innerHTML = ''; // Limpiar grid

    nodes.forEach(node => {
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.node-card');

        // Data binding
        clone.querySelector('.node-id').textContent = node.id;
        clone.querySelector('.status-text').textContent = node.status;
        clone.querySelector('.node-port').textContent = node.port;

        // Estado visual
        card.setAttribute('data-status', node.status);
        card.setAttribute('data-id', node.id); // Para buscarlo fácilmente

        // Botones
        const btnStart = clone.querySelector('.btn-start');
        const btnStop = clone.querySelector('.btn-stop');

        // Lógica simple de UI para deshabilitar botones
        if (node.status === 'running') {
            btnStart.disabled = true;
            btnStart.style.opacity = '0.5';
            btnStart.style.cursor = 'not-allowed';
        } else {
            btnStop.disabled = true;
            btnStop.style.opacity = '0.5';
            btnStop.style.cursor = 'not-allowed';
        }

        nodesGrid.appendChild(clone);
    });
}

async function controlNode(btn, action) {
    const card = btn.closest('.node-card');
    const nodeId = card.getAttribute('data-id');
    const originalText = btn.innerHTML;

    // Feedback visual inmediato
    btn.innerHTML = '<i class="ph ph-spinner ph-spin"></i>';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/nodes/${nodeId}/${action}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Error en la acción');
        }

        // Recargar datos para ver el cambio real
        setTimeout(fetchNodes, 1000); // Pequeño delay para dar tiempo a Docker

    } catch (error) {
        console.error(`Error ${action} node ${nodeId}:`, error);
        alert(`Error: no se pudo ejecutar ${action} en ${nodeId}`);
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Polling cada 3 segundos
setInterval(fetchNodes, 3000);

// Carga inicial
fetchNodes();
async function executeQuery() {
    const query = document.getElementById('sql-query').value;
    const btn = document.querySelector('.query-console .btn-primary');
    const resultsContainer = document.getElementById('query-results');
    const statusContainer = document.getElementById('node-status-bar');
    const tableHead = document.querySelector('#results-table thead');
    const tableBody = document.querySelector('#results-table tbody');

    // UI Loading state
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="ph ph-spinner ph-spin"></i> Executing...';
    btn.disabled = true;
    resultsContainer.style.display = 'none';

    try {
        const response = await fetch('/api/execute-query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

        // Render Node Status
        statusContainer.innerHTML = '';
        data.nodos_estado.forEach(node => {
            const badge = document.createElement('div');
            badge.className = `status-badge ${node.estado.toLowerCase()}`;
            badge.innerHTML = `
                <i class="ph ${node.estado === 'UP' ? 'ph-check-circle' : 'ph-x-circle'}"></i>
                ${node.nodo}: ${node.estado}
                ${node.error ? `(${node.error})` : ''}
            `;
            statusContainer.appendChild(badge);
        });

        // Render Results Table
        tableHead.innerHTML = '';
        tableBody.innerHTML = '';

        if (data.resultados && data.resultados.length > 0) {
            // Headers
            const columns = Object.keys(data.resultados[0]);
            const headerRow = document.createElement('tr');
            columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                headerRow.appendChild(th);
            });
            tableHead.appendChild(headerRow);

            // Rows
            data.resultados.forEach(row => {
                const tr = document.createElement('tr');
                columns.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = row[col];
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });
        } else {
            tableBody.innerHTML = '<tr><td colspan="100%">No results found (or all nodes are down)</td></tr>';
        }

        resultsContainer.style.display = 'block';

    } catch (error) {
        console.error("Query Error:", error);
        alert("Error executing query: " + error.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
