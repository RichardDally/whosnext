document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadNext();
    
    // Set default date for release form
    document.getElementById('rel-date').valueAsDate = new Date();

    document.getElementById('form-participant').addEventListener('submit', handleAddParticipant);
    document.getElementById('form-release').addEventListener('submit', handleAddRelease);
});

function initNavigation() {
    const links = document.querySelectorAll('.nav-links a');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = link.getAttribute('data-page');
            
            // Update active link
            links.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Update active page
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`page-${pageId}`).classList.add('active');

            // Load data for specific pages
            if (pageId === 'next') loadNext();
            if (pageId === 'participants') loadParticipants();
            if (pageId === 'create-release') loadDropdownParticipants();
            if (pageId === 'history') loadHistory();
        });
    });
}

function showToast(message, isError = false) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${isError ? 'error' : ''}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

async function loadNext() {
    try {
        const res = await fetch('/api/next');
        if (!res.ok) throw new Error('No participants available');
        const data = await res.json();
        
        document.getElementById('next-name').textContent = `${data.participant.first_name} ${data.participant.last_name}`;
        
        const dateStr = data.last_release_date ? new Date(data.last_release_date).toLocaleDateString('fr-FR') : 'Never';
        document.getElementById('next-stats').innerHTML = `
            <p>Release Count: <strong>${data.release_count}</strong></p>
            <p>Last Release: <strong>${dateStr}</strong></p>
        `;
    } catch (e) {
        document.getElementById('next-name').textContent = 'No one yet!';
        document.getElementById('next-stats').innerHTML = '<p>Add participants to determine who is next.</p>';
    }
}

async function loadParticipants() {
    try {
        const res = await fetch('/api/participants');
        const participants = await res.json();
        const container = document.getElementById('participants-list');
        container.innerHTML = '';
        
        participants.forEach(p => {
            const div = document.createElement('div');
            div.className = 'participant-item' + (!p.active ? ' inactive' : '');
            
            const btnText = p.active ? 'Deactivate' : 'Activate';
            const btnColor = p.active ? 'var(--danger-color)' : 'var(--secondary-color)';
            const statusBadge = p.active ? '<span style="color:var(--secondary-color); font-size:0.8rem; margin-left:5px;">(Active)</span>' : '<span style="color:var(--danger-color); font-size:0.8rem; margin-left:5px;">(Inactive)</span>';

            div.innerHTML = `
                <span>${p.first_name} ${p.last_name} ${statusBadge}</span>
                <div>
                    <span style="color:var(--text-secondary); font-size:0.8rem; margin-right:10px;">Releases: ${p.release_count}</span>
                    <button class="btn secondary" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" onclick="editParticipant(${p.id}, '${p.first_name.replace(/'/g, "\\'")}', '${p.last_name.replace(/'/g, "\\'")}')">Edit</button>
                    <button class="btn" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; background-color: ${btnColor}; color: white; margin-left: 5px;" onclick="toggleParticipant(${p.id}, ${!p.active})">${btnText}</button>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        showToast('Failed to load participants', true);
    }
}

async function loadDropdownParticipants() {
    try {
        const res = await fetch('/api/participants');
        const participants = await res.json();
        const select = document.getElementById('rel-participant');
        select.innerHTML = '<option value="">Select participant...</option>';
        
        participants.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.first_name} ${p.last_name}`;
            select.appendChild(opt);
        });
    } catch (e) {
        showToast('Failed to load participants for dropdown', true);
    }
}

function getQuarter(date) {
    return Math.floor(date.getMonth() / 3) + 1;
}

async function loadHistory() {
    try {
        const res = await fetch('/api/releases');
        const releases = await res.json();
        const tbody = document.getElementById('history-body');
        tbody.innerHTML = '';
        
        const grouped = {};
        releases.forEach(r => {
            const d = new Date(r.date);
            const year = d.getFullYear();
            const quarter = getQuarter(d);
            const key = `${year} - Q${quarter}`;
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(r);
        });
        
        const sortedKeys = Object.keys(grouped).sort((a, b) => b.localeCompare(a));
        
        const today = new Date();
        const currentKey = `${today.getFullYear()} - Q${getQuarter(today)}`;
        
        sortedKeys.forEach(key => {
            const isCurrent = key === currentKey;
            
            const headerRow = document.createElement('tr');
            headerRow.style.cursor = 'pointer';
            headerRow.innerHTML = `<td colspan="4" style="background: rgba(139,92,246,0.2); text-align: center; font-weight: 600; color: #fff; padding: 0.75rem; user-select: none;">
                ${key} <span class="toggle-icon" style="font-size: 0.8em; opacity: 0.8; margin-left: 8px;">${isCurrent ? '▼' : '▶'}</span>
            </td>`;
            tbody.appendChild(headerRow);
            
            const contentRows = [];
            
            grouped[key].forEach(r => {
                const tr = document.createElement('tr');

                const tdDate = document.createElement('td');
                tdDate.textContent = new Date(r.date).toLocaleDateString('fr-FR');

                const tdVersion = document.createElement('td');
                tdVersion.textContent = r.version;

                const tdParticipant = document.createElement('td');
                tdParticipant.textContent = `${r.participant.first_name} ${r.participant.last_name}`;

                const tdActions = document.createElement('td');
                const dropBtn = document.createElement('button');
                dropBtn.className = 'btn danger';
                dropBtn.style.cssText = 'padding: 0.25rem 0.6rem; font-size: 0.8rem;';
                dropBtn.textContent = 'Drop';
                dropBtn.addEventListener('click', () => confirmDeleteRelease(r.id, r.version));
                tdActions.appendChild(dropBtn);

                tr.append(tdDate, tdVersion, tdParticipant, tdActions);

                tr.style.display = isCurrent ? '' : 'none';
                tbody.appendChild(tr);
                contentRows.push(tr);
            });
            
            headerRow.addEventListener('click', () => {
                if (contentRows.length === 0) return;
                const isHidden = contentRows[0].style.display === 'none';
                contentRows.forEach(row => {
                    row.style.display = isHidden ? '' : 'none';
                });
                headerRow.querySelector('.toggle-icon').textContent = isHidden ? '▼' : '▶';
            });
        });
    } catch (e) {
        showToast('Failed to load history', true);
    }
}

async function handleAddParticipant(e) {
    e.preventDefault();
    const firstName = document.getElementById('part-first-name').value;
    const lastName = document.getElementById('part-last-name').value;
    
    try {
        const res = await fetch('/api/participants', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ first_name: firstName, last_name: lastName })
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Failed to add participant');
        }
        
        showToast('Participant added successfully!');
        document.getElementById('form-participant').reset();
        loadParticipants();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function editParticipant(id, currentFirstName, currentLastName) {
    const newFirstName = prompt("Enter new First Name:", currentFirstName);
    if (newFirstName === null) return; // cancelled
    
    const newLastName = prompt("Enter new Last Name:", currentLastName);
    if (newLastName === null) return; // cancelled
    
    if (newFirstName.trim() === '' || newLastName.trim() === '') {
        showToast('Names cannot be empty', true);
        return;
    }
    
    if (newFirstName === currentFirstName && newLastName === currentLastName) return;
    
    try {
        const res = await fetch(`/api/participants/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ first_name: newFirstName, last_name: newLastName })
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Failed to edit participant');
        }
        
        showToast('Participant updated successfully!');
        loadParticipants();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function toggleParticipant(id, newState) {
    try {
        const res = await fetch(`/api/participants/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: newState })
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Failed to update participant status');
        }
        
        showToast(`Participant ${newState ? 'activated' : 'deactivated'} successfully!`);
        loadParticipants();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function handleAddRelease(e) {
    e.preventDefault();
    const participantId = document.getElementById('rel-participant').value;
    const dateStr = document.getElementById('rel-date').value;
    const version = document.getElementById('rel-version').value;
    
    const dateObj = new Date(dateStr);
    
    try {
        const res = await fetch('/api/releases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                participant_id: parseInt(participantId),
                date: dateObj.toISOString(),
                version: version
            })
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Failed to record release');
        }
        
        showToast('Release recorded successfully!');
        document.getElementById('form-release').reset();
        document.getElementById('rel-date').valueAsDate = new Date(); // reset default date
    } catch (err) {
        showToast(err.message, true);
    }
}

let pendingDeleteId = null;

function confirmDeleteRelease(releaseId, version) {
    pendingDeleteId = releaseId;
    document.getElementById('confirm-modal-message').textContent = `Are you sure you want to drop release ${version}? This action cannot be undone.`;
    const modal = document.getElementById('confirm-modal');
    modal.hidden = false;
    modal.classList.add('active');
}

function closeConfirmModal() {
    const modal = document.getElementById('confirm-modal');
    modal.classList.remove('active');
    modal.hidden = true;
    pendingDeleteId = null;
}

async function deleteRelease(releaseId) {
    try {
        const res = await fetch(`/api/releases/${releaseId}`, { method: 'DELETE' });
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Failed to delete release');
        }
        showToast('Release dropped successfully!');
        loadHistory();
    } catch (err) {
        showToast(err.message, true);
    }
}

document.getElementById('confirm-modal-cancel').addEventListener('click', closeConfirmModal);
document.getElementById('confirm-modal-confirm').addEventListener('click', () => {
    if (pendingDeleteId !== null) {
        deleteRelease(pendingDeleteId);
    }
    closeConfirmModal();
});
document.getElementById('confirm-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeConfirmModal();
});
