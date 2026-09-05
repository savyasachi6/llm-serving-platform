// ==============================================================================
// 🚀 kvcached Interactive Memory Simulator Engine
// ==============================================================================

// State Management
const state = {
  totalVram: 12.0,
  modelPair: 'qwen-default',
  phase: 'triage',
  autoCycle: false,
  autoTimer: null,
  models: {
    'qwen-default': {
      name: 'Qwen 1.5B + 0.5B',
      rw: 1.2,
      aw: 0.5,
      lora: 0.5,
      desc: 'Responder 1.2 GB | Agents 0.5 GB | LoRAs 0.5 GB'
    },
    'llama-family': {
      name: 'Llama 3.2 3B + 1B',
      rw: 2.4,
      aw: 0.9,
      lora: 0.5,
      desc: 'Responder 2.4 GB | Agents 0.9 GB | LoRAs 0.5 GB'
    },
    'enterprise-8b': {
      name: 'Llama-3.1 8B AWQ + Qwen 3B',
      rw: 4.6,
      aw: 2.2,
      lora: 0.5,
      desc: 'Responder 4.6 GB | Agents 2.2 GB | LoRAs 0.5 GB'
    }
  }
};

// Scroll progress bar
window.addEventListener('scroll', () => {
  const e = document.getElementById('pb');
  if (!e) return;
  const m = document.documentElement.scrollHeight - window.innerHeight;
  e.style.width = (m > 0 ? (window.scrollY / m * 100) : 0) + '%';
});

// Intersection observer for fade-in animations
const obs = new IntersectionObserver((es) => {
  es.forEach((e) => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      obs.unobserve(e.target);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.rv,.rg').forEach((el) => obs.observe(el));

// Pipeline tab switcher
function switchTab(id) {
  document.querySelectorAll('.tbt').forEach((b) => b.classList.remove('active'));
  document.querySelectorAll('.tp').forEach((p) => p.classList.remove('active'));
  const btn = document.getElementById('tb' + id);
  const tab = document.getElementById('tab-' + id);
  if (btn) btn.classList.add('active');
  if (tab) tab.classList.add('active');
}

// Initialize Charts
const ctxB = document.getElementById('cB').getContext('2d');
const chartB = new Chart(ctxB, {
  type: 'doughnut',
  data: {
    labels: ['Responder weights', 'Responder KV (LOCKED)', 'Agents weights', 'Agents KV (LOCKED)', 'LoRA adapters', 'Unusable / Idle gap'],
    datasets: [{
      data: [1.2, 5.5, 0.5, 3.7, 0.5, 0.6],
      backgroundColor: ['#4338ca', '#818cf8', '#065f46', '#34d399', '#374151', '#1f2937'],
      borderColor: '#0b1929',
      borderWidth: 3,
      hoverOffset: 6
    }]
  },
  options: {
    cutout: '72%',
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (c) => ` ${c.label}: ${c.parsed.toFixed(1)} GB` } }
    },
    animation: { duration: 600, easing: 'easeInOutQuart' }
  }
});

const ctxA = document.getElementById('cA').getContext('2d');
const chartA = new Chart(ctxA, {
  type: 'doughnut',
  data: {
    labels: ['Responder weights', 'Responder KV (active)', 'Agents weights', 'Agents KV (active)', 'LoRA adapters', 'Free shared dynamic pool'],
    datasets: [{
      data: [1.2, 0.3, 0.5, 6.5, 0.5, 3.0],
      backgroundColor: ['#4338ca', 'rgba(129,140,248,.45)', '#065f46', 'rgba(52,211,153,.85)', '#374151', '#f59e0b'],
      borderColor: '#0b1929',
      borderWidth: 3,
      hoverOffset: 6
    }]
  },
  options: {
    cutout: '72%',
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (c) => ` ${c.label}: ${c.parsed.toFixed(1)} GB` } }
    },
    animation: { duration: 600, easing: 'easeInOutQuart' }
  }
});

// Calculate metrics and update all visuals
function updateSimulation() {
  const vram = state.totalVram;
  const m = state.models[state.modelPair];
  const fixedWeights = m.rw + m.aw + m.lora;
  const cudaOverhead = Math.min(0.8, vram * 0.06);
  const usableVram = Math.max(0.5, vram - cudaOverhead);

  // Static Partitioning math (Without kvcached)
  // vLLM splits static allocation: Responder gets ~45% VRAM, Agents gets ~30% VRAM
  const staticResponderKV = Math.max(0.5, Number((vram * 0.44).toFixed(1)));
  const staticAgentsKV = Math.max(0.4, Number((vram * 0.30).toFixed(1)));
  const staticLockedTotal = Number((fixedWeights + staticResponderKV + staticAgentsKV).toFixed(1));
  const staticGap = Math.max(0.1, Number((vram - staticLockedTotal).toFixed(1)));

  // Dynamic Partitioning math (With kvcached)
  const sharedPool = Math.max(1.0, Number((vram - fixedWeights - cudaOverhead).toFixed(1)));
  let dynamicResponderKV = 0.2;
  let dynamicAgentsKV = 0.2;

  if (state.phase === 'idle') {
    dynamicResponderKV = 0.2;
    dynamicAgentsKV = 0.2;
  } else if (state.phase === 'triage') {
    dynamicAgentsKV = Number((sharedPool * 0.75).toFixed(1));
    dynamicResponderKV = 0.2;
  } else if (state.phase === 'redact') {
    dynamicAgentsKV = Number((sharedPool * 0.85).toFixed(1));
    dynamicResponderKV = 0.2;
  } else if (state.phase === 'respond') {
    dynamicResponderKV = Number((sharedPool * 0.85).toFixed(1));
    dynamicAgentsKV = 0.2;
  } else if (state.phase === 'both') {
    dynamicResponderKV = Number((sharedPool * 0.48).toFixed(1));
    dynamicAgentsKV = Number((sharedPool * 0.48).toFixed(1));
  }

  const freeDynamicPool = Math.max(0, Number((sharedPool - dynamicResponderKV - dynamicAgentsKV).toFixed(1)));

  // Update Hero elements
  document.getElementById('hero-total-vram').innerText = `${vram.toFixed(1)} GB`;
  document.getElementById('hero-locked-boot').innerText = `${staticLockedTotal.toFixed(1)} GB`;
  document.getElementById('hero-elastic-pool').innerText = `~${sharedPool.toFixed(1)} GB`;
  const multiplier = (sharedPool / staticAgentsKV).toFixed(1);
  document.getElementById('hero-multiplier').innerText = `${multiplier}x`;

  // Update Controls UI
  document.getElementById('ctrl-vram-text').innerText = `${vram.toFixed(1)} GB`;
  document.getElementById('ctrl-model-text').innerText = m.name;
  document.getElementById('model-weights-desc').innerText = m.desc;

  // Update Chart B (Without kvcached)
  document.getElementById('chart-b-subtitle').innerText = `Static allocation — ${vram.toFixed(1)} GB total`;
  document.getElementById('center-b-val').innerText = `${staticLockedTotal.toFixed(1)} GB`;
  chartB.data.datasets[0].data = [m.rw, staticResponderKV, m.aw, staticAgentsKV, m.lora, staticGap];
  chartB.update();

  // Update Chart B Legends
  document.getElementById('leg-b-rw').innerText = `${m.rw.toFixed(1)} GB`;
  document.getElementById('leg-b-rkv').innerText = `${staticResponderKV.toFixed(1)} GB`;
  document.getElementById('leg-b-aw').innerText = `${m.aw.toFixed(1)} GB`;
  document.getElementById('leg-b-akv').innerText = `${staticAgentsKV.toFixed(1)} GB`;
  document.getElementById('leg-b-lora').innerText = `${m.lora.toFixed(1)} GB`;
  document.getElementById('leg-b-gap').innerText = `${staticGap.toFixed(1)} GB`;

  // Update Chart A (With kvcached)
  document.getElementById('chart-a-subtitle').innerText = `Elastic allocation — ${sharedPool.toFixed(1)} GB shared pool`;
  document.getElementById('center-a-val').innerText = `~${sharedPool.toFixed(1)} GB`;
  chartA.data.datasets[0].data = [m.rw, dynamicResponderKV, m.aw, dynamicAgentsKV, m.lora, freeDynamicPool];
  chartA.update();

  // Update Chart A Legends
  document.getElementById('leg-a-rw').innerText = `${m.rw.toFixed(1)} GB`;
  document.getElementById('leg-a-rkv').innerText = `${dynamicResponderKV.toFixed(1)} GB (active)`;
  document.getElementById('leg-a-aw').innerText = `${m.aw.toFixed(1)} GB`;
  document.getElementById('leg-a-akv').innerText = `${dynamicAgentsKV.toFixed(1)} GB (active)`;
  document.getElementById('leg-a-lora').innerText = `${m.lora.toFixed(1)} GB`;
  document.getElementById('leg-a-pool').innerText = `${sharedPool.toFixed(1)} GB pool`;

  // Update Dynamic Alerts
  const alertBText = document.getElementById('dynamic-alert-b-text');
  const alertAText = document.getElementById('dynamic-alert-a-text');

  if (state.phase === 'triage' || state.phase === 'redact') {
    alertBText.innerHTML = `<strong>Root cause of 429/503s:</strong> During ${state.phase.toUpperCase()}, <code>vllm-agents</code> is restricted to a tight static ceiling of ${staticAgentsKV.toFixed(1)} GB while ${staticResponderKV.toFixed(1)} GB sits 100% idle and wasted on <code>vllm-responder</code>. Requests get dropped before GPU compute is even 30% utilized!`;
    alertAText.innerHTML = `<strong>Elastic Dynamic Lending:</strong> <code>vllm-agents</code> borrows up to ${dynamicAgentsKV.toFixed(1)} GB directly from the shared pool. It handles the burst with zero OOMs, and physical memory pages are returned immediately upon request completion.`;
  } else if (state.phase === 'respond') {
    alertBText.innerHTML = `<strong>Synthesis Starvation:</strong> <code>vllm-responder</code> generates long-context replies but is restricted to ${staticResponderKV.toFixed(1)} GB while ${staticAgentsKV.toFixed(1)} GB sits idle on <code>vllm-agents</code>. High concurrency causes sudden 504 timeouts.`;
    alertAText.innerHTML = `<strong>Full Bandwidth Synthesis:</strong> Responder expands dynamically to ${dynamicResponderKV.toFixed(1)} GB of KV memory, enabling large context windows and high concurrency with zero wasted partitions.`;
  } else if (state.phase === 'both') {
    alertBText.innerHTML = `<strong>Contention & Thrashing:</strong> Both engines struggle within their rigid partitions (${staticAgentsKV.toFixed(1)} GB and ${staticResponderKV.toFixed(1)} GB). Traffic spikes cause immediate circuit breaker tripping.`;
    alertAText.innerHTML = `<strong>Proportional Fair Sharing:</strong> kvcached arbitrates physical pages elastically between both engines (${dynamicResponderKV.toFixed(1)} GB and ${dynamicAgentsKV.toFixed(1)} GB) based on live token generation demands.`;
  } else {
    alertBText.innerHTML = `<strong>Cold Standby Waste:</strong> At zero load, ${staticLockedTotal.toFixed(1)} GB of physical VRAM is pre-locked and unavailable to any other process on your system.`;
    alertAText.innerHTML = `<strong>Zero Memory Waste:</strong> Only ${fixedWeights.toFixed(1)} GB is consumed by model weights. The remaining ${sharedPool.toFixed(1)} GB is completely free for instant on-demand allocation.`;
  }

  // Update Horizontal Memory Bar
  renderMemoryBars(vram, m, staticResponderKV, staticAgentsKV, staticGap, dynamicResponderKV, dynamicAgentsKV, freeDynamicPool, sharedPool);
}

// Render the segmented horizontal memory bars
function renderMemoryBars(vram, m, sRKV, sAKV, sGap, dRKV, dAKV, dFree, pool) {
  const staticTrack = document.getElementById('static-mem-bar');
  const elasticTrack = document.getElementById('elastic-mem-bar');

  // Static Track Segments
  const pct = (val) => ((val / vram) * 100).toFixed(1) + '%';
  staticTrack.innerHTML = `
    <div class="mem-bar-segment" style="width:${pct(m.rw)};background:#4338ca;" title="Responder Weights: ${m.rw}GB">R-W</div>
    <div class="mem-bar-segment" style="width:${pct(sRKV)};background:#818cf8;" title="Responder KV (Locked): ${sRKV}GB">R-KV (Locked)</div>
    <div class="mem-bar-segment" style="width:${pct(m.aw)};background:#065f46;" title="Agents Weights: ${m.aw}GB">A-W</div>
    <div class="mem-bar-segment" style="width:${pct(sAKV)};background:#34d399;" title="Agents KV (Locked): ${sAKV}GB">A-KV (Locked)</div>
    <div class="mem-bar-segment" style="width:${pct(m.lora)};background:#374151;" title="LoRA: ${m.lora}GB">LoRA</div>
    <div class="mem-bar-segment" style="width:${pct(sGap)};background:#1f2937;color:#94a3b8;" title="Unusable Gap: ${sGap}GB">Gap</div>
  `;

  // Elastic Track Segments
  elasticTrack.innerHTML = `
    <div class="mem-bar-segment" style="width:${pct(m.rw)};background:#4338ca;" title="Responder Weights: ${m.rw}GB">R-W</div>
    <div class="mem-bar-segment" style="width:${pct(m.aw)};background:#065f46;" title="Agents Weights: ${m.aw}GB">A-W</div>
    <div class="mem-bar-segment" style="width:${pct(m.lora)};background:#374151;" title="LoRA: ${m.lora}GB">LoRA</div>
    <div class="mem-bar-segment" style="width:${pct(dRKV)};background:rgba(129,140,248,.85);" title="Active Responder KV: ${dRKV}GB">R-KV</div>
    <div class="mem-bar-segment" style="width:${pct(dAKV)};background:rgba(52,211,153,.85);" title="Active Agents KV: ${dAKV}GB">A-KV</div>
    <div class="mem-bar-segment" style="width:${pct(dFree)};background:#f59e0b;color:#000;" title="Free Shared Pool: ${dFree}GB">Free Pool (${dFree}GB)</div>
  `;

  document.getElementById('static-bar-summary').innerText = `${(m.rw + sRKV + m.aw + sAKV + m.lora).toFixed(1)} GB Locked | ${sGap} GB Idle Gap`;
  document.getElementById('elastic-bar-summary').innerText = `${(m.rw + m.aw + m.lora).toFixed(1)} GB Fixed Weights | ${pool} GB Shared Pool`;
}

// User Interaction Handlers
function setGpuPreset(vram) {
  state.totalVram = Number(vram);
  document.getElementById('vram-slider').value = vram;
  document.querySelectorAll('.pill-btn').forEach((b) => {
    b.classList.toggle('active', b.innerText.includes(`${vram} GB`));
  });
  updateSimulation();
}

function onSliderChange(val) {
  state.totalVram = Number(val);
  document.querySelectorAll('.pill-btn').forEach((b) => {
    b.classList.toggle('active', b.innerText === `${val} GB`);
  });
  updateSimulation();
}

function onModelChange(val) {
  state.modelPair = val;
  updateSimulation();
}

function setTrafficPhase(phase) {
  state.phase = phase;
  document.querySelectorAll('.traffic-btn:not(.auto-btn)').forEach((b) => {
    b.classList.toggle('active', b.id === 'phase-' + phase);
  });
  const phaseNames = {
    'idle': '⏸️ Idle (0 in-flight)',
    'triage': '🏷️ Phase 1: Triage Burst',
    'redact': '🛡️ Phase 2: Redact Burst',
    'respond': '✍️ Phase 3: Respond Burst',
    'both': '⚡ Heavy Concurrency'
  };
  document.getElementById('ctrl-phase-text').innerText = phaseNames[phase];
  updateSimulation();
}

function toggleAutoPlay() {
  state.autoCycle = !state.autoCycle;
  const btn = document.getElementById('phase-auto');
  btn.classList.toggle('active', state.autoCycle);
  btn.innerText = state.autoCycle ? '⏹️ Stop Auto-Cycle' : '▶️ Auto-Cycle Workflow';

  if (state.autoCycle) {
    const phases = ['triage', 'redact', 'respond', 'both', 'idle'];
    let idx = 0;
    state.autoTimer = setInterval(() => {
      idx = (idx + 1) % phases.length;
      setTrafficPhase(phases[idx]);
    }, 2800);
  } else {
    clearInterval(state.autoTimer);
  }
}

// Initial Run
updateSimulation();
if (window.anime) {
  anime({ targets: '.hst > div', opacity: [0, 1], translateY: [20, 0], delay: anime.stagger(100, { start: 400 }), duration: 800, easing: 'easeOutExpo' });
}
if (window.Prism) Prism.highlightAll();
