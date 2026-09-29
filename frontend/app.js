// HashBack DApp - Controlador Frontend com Alternância Dinâmica de Perfis (Emissor vs Receptor)

let accounts = [];
let activeAccount = null;
let rewards = [];
let chainData = [];

// Elementos Globais DOM
const accountPillsContainer = document.getElementById('account-pills');
const activeRoleEl = document.getElementById('active-account-role');
const metricsContainer = document.getElementById('metrics-container');

const operationsTitle = document.getElementById('operations-title');
const segmentedTabsContainer = document.getElementById('segmented-tabs');
const tabContentArea = document.getElementById('tab-content-area');

const cellRewards = document.getElementById('cell-rewards');
const cellMerchantSummary = document.getElementById('cell-merchant-summary');
const rewardsContainer = document.getElementById('rewards-container');
const vouchersContainer = document.getElementById('vouchers-container');

const timelineContainer = document.getElementById('blockchain-timeline');
const blocksCountEl = document.getElementById('blocks-count');

const feedbackBox = document.getElementById('contract-feedback-box');
const feedbackBadge = document.getElementById('feedback-badge');
const feedbackMsg = document.getElementById('feedback-msg');

function showFeedback(type, message) {
  feedbackBox.style.display = 'flex';
  feedbackBox.className = `terminal-feedback ${type}`;
  feedbackBadge.textContent = type === 'success' ? 'CONFIRMADO' : 'REJEITADO';
  feedbackMsg.textContent = message;
}

// Carregar Contas
async function loadAccounts() {
  try {
    const res = await fetch('/api/demo-accounts');
    accounts = await res.json();
    renderAccountPills();
  } catch (err) {
    console.error('Erro ao carregar contas:', err);
  }
}

function renderAccountPills() {
  accountPillsContainer.innerHTML = '';
  accounts.forEach((acc, idx) => {
    const btn = document.createElement('button');
    btn.className = `acc-pill ${activeAccount && activeAccount.key === acc.key ? 'active' : ''}`;
    if (!activeAccount && idx === 0) {
      activeAccount = acc;
      btn.classList.add('active');
    }
    btn.textContent = acc.name;
    btn.addEventListener('click', () => {
      activeAccount = acc;
      renderAccountPills();
      renderActiveProfile();
    });
    accountPillsContainer.appendChild(btn);
  });
  renderActiveProfile();
}

// Renderiza a Interface com base no Perfil (EMISSOR vs RECEPTOR)
function renderActiveProfile() {
  if (!activeAccount) return;

  const isMerchant = activeAccount.is_merchant;

  // 1. Atualizar Título e Métricas do Topo
  if (isMerchant) {
    activeRoleEl.textContent = 'Loja Parceira (Canal Emissor)';
    metricsContainer.innerHTML = `
      <div class="metric-plate">
        <span class="plate-label">Total de Pontos Emitidos</span>
        <div class="plate-balance">
          <span>${activeAccount.total_issued.toLocaleString('pt-BR')}</span>
          <span class="token-ticker">HBC</span>
        </div>
      </div>
      <div class="metric-plate">
        <span class="plate-label">Clientes Beneficiados</span>
        <div class="plate-balance" style="font-size:1.4rem;">
          <span>${activeAccount.clients_count}</span>
          <span class="token-ticker" style="color:var(--text-tertiary); font-size:0.75rem;">CLIENTES</span>
        </div>
      </div>
      <div class="metric-plate address-plate">
        <span class="plate-label">Endereço Público (0x)</span>
        <div class="plate-mono">${activeAccount.address}</div>
      </div>
    `;

    // Loja NÃO resgata pontos -> Esconder Catálogo e Mostrar Resumo do Emissor
    cellRewards.style.display = 'none';
    cellMerchantSummary.style.display = 'block';

    // Renderizar Abas da Loja
    operationsTitle.textContent = 'Painel da Loja Parceira';
    segmentedTabsContainer.innerHTML = `
      <button class="seg-btn active" data-tab="tab-mint">Emitir Pontos</button>
      <button class="seg-btn" data-tab="tab-tests">Testes de Auditoria</button>
    `;

    // Renderizar Formulário de Emissão (Apenas para Clientes)
    const clientOptions = accounts
      .filter(a => !a.is_merchant)
      .map(a => `<option value="${a.address}">${a.name} (${a.address.substring(0, 10)}...)</option>`)
      .join('');

    tabContentArea.innerHTML = `
      <!-- Aba Emissão -->
      <div class="tab-pane active" id="tab-mint">
        <form id="form-mint" class="haptic-form">
          <div class="input-bezel">
            <label for="mint-recipient">Cliente Destinatário</label>
            <select id="mint-recipient" class="haptic-select">${clientOptions}</select>
          </div>
          <div class="input-bezel">
            <label for="mint-amount">Quantidade de Pontos (HBC)</label>
            <input type="number" id="mint-amount" class="haptic-input" value="150" min="1" required>
          </div>
          <button type="submit" class="island-cta">
            <span>Emitir Pontos & Criar Bloco</span>
            <span class="cta-icon-bezel">→</span>
          </button>
        </form>
      </div>

      <!-- Aba Testes de Rejeição da Loja -->
      <div class="tab-pane" id="tab-tests">
        <div class="sandbox-actions">
          <div class="sandbox-card">
            <div class="sandbox-desc">
              <strong>Simular Resgate de Recompensa pela Loja</strong>
              <span>Comprova que o contrato impede a loja de resgatar prêmios do catálogo.</span>
            </div>
            <button class="island-btn island-btn-danger" id="btn-test-merchant-redeem">Executar Teste</button>
          </div>
        </div>
      </div>
    `;

    setupMintForm();
    setupMerchantTest();

  } else {
    // PERFIL: CLIENTE (Alice / Bob)
    activeRoleEl.textContent = `Cliente (${activeAccount.name})`;
    metricsContainer.innerHTML = `
      <div class="metric-plate">
        <span class="plate-label">Saldo de Pontos</span>
        <div class="plate-balance">
          <span>${activeAccount.balance.toLocaleString('pt-BR')}</span>
          <span class="token-ticker">HBC</span>
        </div>
      </div>
      <div class="metric-plate address-plate">
        <span class="plate-label">Endereço Público (0x)</span>
        <div class="plate-mono">${activeAccount.address}</div>
      </div>
      <div class="metric-plate nonce-plate">
        <span class="plate-label">Nonce (Tx)</span>
        <div class="plate-mono">${activeAccount.nonce}</div>
      </div>
    `;

    // Cliente PODE resgatar recompensas -> Mostrar Catálogo e Esconder Painel da Loja
    cellRewards.style.display = 'block';
    cellMerchantSummary.style.display = 'none';

    // Renderizar Abas do Cliente (Cliente NÃO EMITE pontos)
    operationsTitle.textContent = 'Painel do Cliente';
    segmentedTabsContainer.innerHTML = `
      <button class="seg-btn active" data-tab="tab-transfer">Transferir Pontos</button>
      <button class="seg-btn" data-tab="tab-tests">Testes de Rejeição</button>
    `;

    // Destinatários: Apenas outros clientes (Lojas NÃO podem receber)
    const peerOptions = accounts
      .filter(a => !a.is_merchant && a.key !== activeAccount.key)
      .map(a => `<option value="${a.address}">${a.name} (${a.address.substring(0, 10)}...)</option>`)
      .join('');

    tabContentArea.innerHTML = `
      <!-- Aba Transferência -->
      <div class="tab-pane active" id="tab-transfer">
        <form id="form-transfer" class="haptic-form">
          <div class="input-bezel">
            <label for="transfer-recipient">Outro Cliente</label>
            <select id="transfer-recipient" class="haptic-select">${peerOptions}</select>
          </div>
          <div class="input-bezel">
            <label for="transfer-amount">Quantidade de Pontos (HBC)</label>
            <input type="number" id="transfer-amount" class="haptic-input" value="50" min="1" required>
          </div>
          <button type="submit" class="island-cta">
            <span>Transferir Pontos</span>
            <span class="cta-icon-bezel">→</span>
          </button>
        </form>
      </div>

      <!-- Aba Testes de Rejeição do Cliente -->
      <div class="tab-pane" id="tab-tests">
        <div class="sandbox-actions">
          <div class="sandbox-card">
            <div class="sandbox-desc">
              <strong>1. Simular Gasto Duplo</strong>
              <span>Tenta transferir valor acima do saldo disponível da conta.</span>
            </div>
            <button class="island-btn island-btn-danger" id="btn-test-doublespend">Executar</button>
          </div>
          <div class="sandbox-card">
            <div class="sandbox-desc">
              <strong>2. Simular Emissão Não Autorizada</strong>
              <span>Cliente tenta emitir novos pontos para si mesmo.</span>
            </div>
            <button class="island-btn island-btn-danger" id="btn-test-unauthorized">Executar</button>
          </div>
          <div class="sandbox-card">
            <div class="sandbox-desc">
              <strong>3. Tentar Enviar Pontos para a Loja</strong>
              <span>Comprova que o contrato rejeita transferências para a Loja Parceira.</span>
            </div>
            <button class="island-btn island-btn-danger" id="btn-test-send-merchant">Executar</button>
          </div>
        </div>
      </div>
    `;

    setupTransferForm();
    setupCustomerTests();
    renderVouchers();
  }

  setupSegmentedTabs();
}

function setupSegmentedTabs() {
  const tabButtons = segmentedTabsContainer.querySelectorAll('.seg-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabContentArea.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetPane = tabContentArea.querySelector(`#${btn.getAttribute('data-tab')}`);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

function setupMintForm() {
  const form = document.getElementById('form-mint');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const recipient = document.getElementById('mint-recipient').value;
    const amount = parseInt(document.getElementById('mint-amount').value, 10);

    try {
      const res = await fetch('/api/quick-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_key: activeAccount.key,
          action_type: 'MINT',
          recipient: recipient,
          amount: amount
        })
      });
      const data = await res.json();
      if (!res.ok) {
        showFeedback('error', data.detail || 'Falha ao emitir pontos');
      } else {
        showFeedback('success', `Sucesso! Bloco #${data.block.index} criado. ${amount} HBC emitidos.`);
        await refreshAll();
      }
    } catch (err) {
      showFeedback('error', `Erro: ${err.message}`);
    }
  });
}

function setupTransferForm() {
  const form = document.getElementById('form-transfer');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const recipient = document.getElementById('transfer-recipient').value;
    const amount = parseInt(document.getElementById('transfer-amount').value, 10);

    try {
      const res = await fetch('/api/quick-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_key: activeAccount.key,
          action_type: 'TRANSFER',
          recipient: recipient,
          amount: amount
        })
      });
      const data = await res.json();
      if (!res.ok) {
        showFeedback('error', data.detail || 'Falha na transferência');
      } else {
        showFeedback('success', `Transferência realizada! Confirmada no Bloco #${data.block.index}.`);
        await refreshAll();
      }
    } catch (err) {
      showFeedback('error', `Erro: ${err.message}`);
    }
  });
}

function setupMerchantTest() {
  const btn = document.getElementById('btn-test-merchant-redeem');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/quick-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_key: 'merchant',
          action_type: 'MERCHANT_REDEEM_ATTACK'
        })
      });
      const data = await res.json();
      if (!res.ok) {
        showFeedback('error', data.detail);
      } else {
        showFeedback('success', data.message);
      }
    } catch (err) {
      showFeedback('error', err.message);
    }
  });
}

function setupCustomerTests() {
  const btnDoubleSpend = document.getElementById('btn-test-doublespend');
  const btnUnauthorized = document.getElementById('btn-test-unauthorized');
  const btnSendMerchant = document.getElementById('btn-test-send-merchant');

  if (btnDoubleSpend) {
    btnDoubleSpend.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/quick-action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_key: activeAccount.key,
            action_type: 'DOUBLE_SPEND_ATTACK'
          })
        });
        const data = await res.json();
        showFeedback(!res.ok ? 'error' : 'success', !res.ok ? data.detail : data.message);
      } catch (err) {
        showFeedback('error', err.message);
      }
    });
  }

  if (btnUnauthorized) {
    btnUnauthorized.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/quick-action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_key: activeAccount.key,
            action_type: 'UNAUTHORIZED_MINT'
          })
        });
        const data = await res.json();
        showFeedback(!res.ok ? 'error' : 'success', !res.ok ? data.detail : data.message);
      } catch (err) {
        showFeedback('error', err.message);
      }
    });
  }

  if (btnSendMerchant) {
    btnSendMerchant.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/quick-action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_key: activeAccount.key,
            action_type: 'TRANSFER_TO_MERCHANT_ATTACK'
          })
        });
        const data = await res.json();
        showFeedback(!res.ok ? 'error' : 'success', !res.ok ? data.detail : data.message);
      } catch (err) {
        showFeedback('error', err.message);
      }
    });
  }
}

// Carregar Recompensas e Vouchers
async function loadRewardsAndState() {
  try {
    const res = await fetch('/api/state');
    const state = await res.json();
    rewards = state.rewards || [];
    renderRewards();
    renderVouchers(state.vouchers || []);
  } catch (err) {
    console.error('Erro ao carregar recompensas:', err);
  }
}

function renderRewards() {
  rewardsContainer.innerHTML = '';
  rewards.forEach(r => {
    const card = document.createElement('div');
    card.className = 'vault-card';
    card.innerHTML = `
      <div class="vault-info">
        <h4>${r.name}</h4>
        <p>${r.description}</p>
      </div>
      <div class="vault-right">
        <div class="vault-cost">${r.points} <small>pts</small></div>
        <button class="island-btn" onclick="redeemReward('${r.id}')">
          <span>Resgatar</span>
          <span class="btn-icon-wrapper">→</span>
        </button>
      </div>
    `;
    rewardsContainer.appendChild(card);
  });
}

async function renderVouchers(vouchersList = null) {
  if (!vouchersList) {
    const res = await fetch('/api/state');
    const state = await res.json();
    vouchersList = state.vouchers || [];
  }

  vouchersContainer.innerHTML = '';
  const myVouchers = activeAccount ? vouchersList.filter(v => v.customer.toLowerCase() === activeAccount.address.toLowerCase()) : vouchersList;

  if (myVouchers.length === 0) {
    vouchersContainer.innerHTML = '<p class="empty-plate">Nenhum voucher resgatado por esta conta.</p>';
    return;
  }

  myVouchers.forEach(v => {
    const plate = document.createElement('div');
    plate.className = 'voucher-plate';
    plate.innerHTML = `
      <div>
        <div class="voucher-hash">${v.voucher_code}</div>
        <div class="voucher-sub">${v.reward_name} • ${v.points_spent} HBC Queimados</div>
      </div>
      <span class="bezel-pill" style="font-size:0.7rem; color:var(--accent-purple-light); border-color:rgba(139,92,246,0.3)">Válido no Contrato</span>
    `;
    vouchersContainer.appendChild(plate);
  });
}

// Resgate de Recompensas
window.redeemReward = async function(rewardId) {
  if (!activeAccount || activeAccount.is_merchant) return;

  try {
    const res = await fetch('/api/quick-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account_key: activeAccount.key,
        action_type: 'REDEEM',
        reward_id: rewardId
      })
    });

    const data = await res.json();
    if (!res.ok) {
      showFeedback('error', data.detail || 'Resgate rejeitado');
    } else {
      showFeedback('success', `Pontos queimados e voucher gerado no Bloco #${data.block.index}.`);
      await refreshAll();
    }
  } catch (err) {
    showFeedback('error', `Erro: ${err.message}`);
  }
};

// Carregar Blockchain
async function loadBlockchain() {
  try {
    const res = await fetch('/api/chain');
    const data = await res.json();
    chainData = data.chain || [];
    blocksCountEl.textContent = chainData.length;
    renderBlockchain();
  } catch (err) {
    console.error('Erro ao buscar blockchain:', err);
  }
}

function renderBlockchain() {
  timelineContainer.innerHTML = '';
  chainData.forEach(block => {
    const card = document.createElement('div');
    card.className = 'stream-card';

    const txsHtml = block.transactions.length === 0 
      ? '<div class="plate-mono" style="font-size:0.72rem; color:var(--text-tertiary);">Bloco Gênesis (Sem transações)</div>'
      : block.transactions.map(tx => `
          <div class="stream-tx">
            <div>
              <span class="badge-tx ${tx.type}">${tx.type}</span>
              <strong>${tx.amount} HBC</strong>
            </div>
            <div class="plate-mono" style="margin-top:3px;">De: ${tx.sender.substring(0, 10)}...</div>
            <div class="plate-mono">Para: ${tx.recipient.substring(0, 10)}...</div>
          </div>
        `).join('');

    const formattedTime = new Date(block.timestamp * 1000).toLocaleTimeString('pt-BR');

    card.innerHTML = `
      <div class="stream-header">
        <span class="stream-index">Bloco #${block.index}</span>
        <span class="stream-time">${formattedTime}</span>
      </div>
      <div class="hash-row">
        <span class="hash-label">Hash Atual</span>
        <div class="hash-val">${block.current_hash}</div>
        <span class="hash-label" style="margin-top:2px;">Hash Anterior</span>
        <div class="hash-val">${block.previous_hash}</div>
      </div>
      <div class="stream-tx-list">
        <span class="hash-label">Transações (${block.transactions.length})</span>
        ${txsHtml}
      </div>
    `;
    timelineContainer.appendChild(card);
  });

  timelineContainer.scrollLeft = timelineContainer.scrollWidth;
}

// Resetar Cadeia
document.getElementById('btn-reset-chain').addEventListener('click', async () => {
  if (!confirm('Deseja resetar a blockchain para o Bloco Gênesis?')) return;
  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    showFeedback('success', data.message);
    await refreshAll();
  } catch (err) {
    showFeedback('error', `Erro: ${err.message}`);
  }
});

async function refreshAll() {
  const currentKey = activeAccount ? activeAccount.key : null;
  const res = await fetch('/api/demo-accounts');
  accounts = await res.json();
  if (currentKey) {
    activeAccount = accounts.find(a => a.key === currentKey) || accounts[0];
  }
  renderAccountPills();
  await loadRewardsAndState();
  await loadBlockchain();
}

// Inicialização
refreshAll();
