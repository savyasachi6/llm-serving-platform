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
      name: 'Qwen 2.5 1.5B + 0.5B',
      rw: 1.2,
      aw: 0.5,
      lora: 0.5,
      desc: 'Responder 1.2 GB | Agents 0.5 GB | LoRAs 0.5 GB (Ideal for 8–12GB GPUs)'
    },
    'llama-family': {
      name: 'Llama 3.2 3B + 1B',
      rw: 2.4,
      aw: 0.9,
      lora: 0.5,
      desc: 'Responder 2.4 GB | Agents 0.9 GB | LoRAs 0.5 GB (Ideal for 12–16GB GPUs)'
    },
    'deepseek-r1': {
      name: 'DeepSeek-R1 Distill 7B + Qwen 0.5B',
      rw: 4.8,
      aw: 0.5,
      lora: 0.5,
      desc: 'Responder 4.8 GB (FP8/AWQ) | Agents 0.5 GB | LoRAs 0.5 GB (Reasoning Heavy)'
    },
    'mistral-stack': {
      name: 'Mistral 7B + Ministral 3B',
      rw: 4.5,
      aw: 2.1,
      lora: 0.8,
      desc: 'Responder 4.5 GB (AWQ) | Agents 2.1 GB | LoRAs 0.8 GB (Enterprise Multilingual)'
    },
    'gemma2-stack': {
      name: 'Gemma 2 9B AWQ + 2B',
      rw: 5.6,
      aw: 1.6,
      lora: 0.6,
      desc: 'Responder 5.6 GB (AWQ) | Agents 1.6 GB | LoRAs 0.6 GB (Google High-Precision)'
    },
    'phi-enterprise': {
      name: 'Phi-4 14B AWQ + Phi-3.5 3.8B',
      rw: 8.2,
      aw: 2.4,
      lora: 0.6,
      desc: 'Responder 8.2 GB (AWQ) | Agents 2.4 GB | LoRAs 0.6 GB (High Density 24GB+)'
    },
    'enterprise-8b': {
      name: 'Llama-3.1 8B AWQ + Qwen 3B',
      rw: 4.6,
      aw: 2.2,
      lora: 0.6,
      desc: 'Responder 4.6 GB (AWQ) | Agents 2.2 GB | LoRAs 0.6 GB (Enterprise Multi-LoRA)'
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
  const rawStaticRKV = Number((vram * 0.44).toFixed(1));
  const rawStaticAKV = Number((vram * 0.30).toFixed(1));
  const staticLockedTotal = Number((fixedWeights + rawStaticRKV + rawStaticAKV).toFixed(1));
  const staticGap = Math.max(0, Number((vram - staticLockedTotal).toFixed(1)));

  // Dynamic Partitioning math (With kvcached)
  const sharedPool = Math.max(0.4, Number((vram - fixedWeights - cudaOverhead).toFixed(1)));
  let dynamicResponderKV = 0.2;
  let dynamicAgentsKV = 0.2;

  if (state.phase === 'idle') {
    dynamicResponderKV = Math.min(0.2, Number((sharedPool * 0.1).toFixed(1)));
    dynamicAgentsKV = Math.min(0.2, Number((sharedPool * 0.1).toFixed(1)));
  } else if (state.phase === 'triage') {
    dynamicAgentsKV = Number((sharedPool * 0.75).toFixed(1));
    dynamicResponderKV = Number((sharedPool * 0.1).toFixed(1));
  } else if (state.phase === 'redact') {
    dynamicAgentsKV = Number((sharedPool * 0.85).toFixed(1));
    dynamicResponderKV = Number((sharedPool * 0.1).toFixed(1));
  } else if (state.phase === 'respond') {
    dynamicResponderKV = Number((sharedPool * 0.85).toFixed(1));
    dynamicAgentsKV = Number((sharedPool * 0.1).toFixed(1));
  } else if (state.phase === 'both') {
    dynamicResponderKV = Number((sharedPool * 0.48).toFixed(1));
    dynamicAgentsKV = Number((sharedPool * 0.48).toFixed(1));
  }

  const freeDynamicPool = Math.max(0, Number((sharedPool - dynamicResponderKV - dynamicAgentsKV).toFixed(1)));
  const isVramTight = fixedWeights + 1.2 >= vram;

  // Update Hero elements
  document.getElementById('hero-total-vram').innerText = `${vram.toFixed(1)} GB`;
  document.getElementById('hero-locked-boot').innerText = `${staticLockedTotal.toFixed(1)} GB`;
  document.getElementById('hero-elastic-pool').innerText = `~${sharedPool.toFixed(1)} GB`;
  const multiplier = rawStaticAKV > 0 ? (sharedPool / rawStaticAKV).toFixed(1) : '3.2';
  document.getElementById('hero-multiplier').innerText = `${multiplier}x`;

  // Update Controls UI
  document.getElementById('ctrl-vram-text').innerText = `${vram.toFixed(1)} GB`;
  document.getElementById('ctrl-model-text').innerText = m.name;
  document.getElementById('model-weights-desc').innerText = m.desc;

  // Update Chart B (Without kvcached)
  document.getElementById('chart-b-subtitle').innerText = `Static allocation — ${vram.toFixed(1)} GB total`;
  document.getElementById('center-b-val').innerText = `${staticLockedTotal.toFixed(1)} GB`;
  chartB.data.datasets[0].data = [m.rw, rawStaticRKV, m.aw, rawStaticAKV, m.lora, staticGap];
  chartB.update();

  // Update Chart B Legends
  document.getElementById('leg-b-rw').innerText = `${m.rw.toFixed(1)} GB`;
  document.getElementById('leg-b-rkv').innerText = `${rawStaticRKV.toFixed(1)} GB`;
  document.getElementById('leg-b-aw').innerText = `${m.aw.toFixed(1)} GB`;
  document.getElementById('leg-b-akv').innerText = `${rawStaticAKV.toFixed(1)} GB`;
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

  if (isVramTight) {
    alertBText.innerHTML = `<strong>🚨 High Boot OOM Risk:</strong> Fixed weights of <strong>${m.name}</strong> (${fixedWeights.toFixed(1)} GB) consume over 80% of ${vram} GB VRAM! Rigid static partitions immediately fail to initialize. Switch to a 16GB, 24GB, or 40GB GPU preset.`;
    alertAText.innerHTML = `<strong>Elastic Survival:</strong> With kvcached, only weights (${fixedWeights.toFixed(1)} GB) are anchored. The remaining ${sharedPool.toFixed(1)} GB is shared elastically page-by-page, allowing execution even under constrained headroom.`;
  } else if (state.phase === 'triage' || state.phase === 'redact') {
    alertBText.innerHTML = `<strong>Root cause of 429/503s:</strong> During ${state.phase.toUpperCase()}, <code>vllm-agents</code> is restricted to a tight static ceiling of ${rawStaticAKV.toFixed(1)} GB while ${rawStaticRKV.toFixed(1)} GB sits 100% idle and wasted on <code>vllm-responder</code>. Requests get dropped before GPU compute is even 30% utilized!`;
    alertAText.innerHTML = `<strong>Elastic Dynamic Lending:</strong> <code>vllm-agents</code> borrows up to ${dynamicAgentsKV.toFixed(1)} GB directly from the shared pool. It handles the burst with zero OOMs, and physical memory pages are returned immediately upon request completion.`;
  } else if (state.phase === 'respond') {
    alertBText.innerHTML = `<strong>Synthesis Starvation:</strong> <code>vllm-responder</code> generates long-context replies but is restricted to ${rawStaticRKV.toFixed(1)} GB while ${rawStaticAKV.toFixed(1)} GB sits idle on <code>vllm-agents</code>. High concurrency causes sudden 504 timeouts.`;
    alertAText.innerHTML = `<strong>Full Bandwidth Synthesis:</strong> Responder expands dynamically to ${dynamicResponderKV.toFixed(1)} GB of KV memory, enabling large context windows and high concurrency with zero wasted partitions.`;
  } else if (state.phase === 'both') {
    alertBText.innerHTML = `<strong>Contention & Thrashing:</strong> Both engines struggle within their rigid partitions (${rawStaticAKV.toFixed(1)} GB and ${rawStaticRKV.toFixed(1)} GB). Traffic spikes cause immediate circuit breaker tripping.`;
    alertAText.innerHTML = `<strong>Proportional Fair Sharing:</strong> kvcached arbitrates physical pages elastically between both engines (${dynamicResponderKV.toFixed(1)} GB and ${dynamicAgentsKV.toFixed(1)} GB) based on live token generation demands.`;
  } else {
    alertBText.innerHTML = `<strong>Cold Standby Waste:</strong> At zero load, ${staticLockedTotal.toFixed(1)} GB of physical VRAM is pre-locked and unavailable to any other process on your system.`;
    alertAText.innerHTML = `<strong>Zero Memory Waste:</strong> Only ${fixedWeights.toFixed(1)} GB is consumed by model weights. The remaining ${sharedPool.toFixed(1)} GB is completely free for instant on-demand allocation.`;
  }

  // Update Horizontal Memory Bar
  renderMemoryBars(vram, m, rawStaticRKV, rawStaticAKV, staticGap, dynamicResponderKV, dynamicAgentsKV, freeDynamicPool, sharedPool);
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

// ==============================================================================
// 📊 Empirical Benchmarks & Deep Performance Analytics Engine
// ==============================================================================

const benchmarkData = {
  short_chat: {
    name: 'short_chat',
    title: '💬 Baseline Short Chat',
    workload: 'chat',
    description: 'Baseline short multi-turn chat measuring cold un-cached serving performance.',
    model: 'Qwen/Qwen2.5-0.5B-Instruct',
    requests: 100,
    concurrency: 10,
    successRate: '100.0%',
    throughputRps: 11.58,
    decodeTps: 347.4,
    totalTps: 764.2,
    p50Latency: '0.787s',
    p95Latency: '1.372s',
    ttftP50: '314.8 ms',
    tpotP50: '15.7 ms/tok',
    cacheHitRate: '0.0%',
    statusBadge: '100% Success (Cold Cache)',
    notes: 'Every incoming request performs full prefill computation on the prompt.'
  },
  shared_prefix_agents: {
    name: 'shared_prefix_agents',
    title: '⚡ Shared Prefix Multi-Agent',
    workload: 'chat (triage prefix)',
    description: 'Multi-agent simulation sharing common system prompts to demonstrate prefix caching.',
    model: 'Qwen/Qwen2.5-0.5B-Instruct',
    engine: 'vllm-agents',
    lora: 'none',
    requests: 100,
    concurrency: 10,
    successRate: '100.0%',
    throughputRps: 16.18,
    decodeTps: 485.4,
    totalTps: 1067.8,
    p50Latency: '0.501s',
    p95Latency: '1.050s',
    ttftP50: '40.1 ms',
    tpotP50: '14.2 ms/tok',
    cacheHitRate: '87.5%',
    vramMb: '124.5 MB KV',
    statusBadge: '+39.7% Throughput / -36.3% Latency',
    notes: 'Prompt prefix blocks are matched and reused directly from VRAM, bypassing prefill.'
  },
  heterogeneous_pipeline: {
    name: 'heterogeneous_pipeline',
    title: '🔀 Heterogeneous Multi-Model Pipeline',
    workload: 'triage + redact + respond',
    description: 'Cross-engine pipeline testing multi-model routing (0.5B + 1.5B), Multi-LoRA swapping, and dynamic kvcached pooling.',
    model: 'Qwen 0.5B (Agents) + Qwen 1.5B (Responder)',
    engine: 'Dual Engine: vllm-agents & vllm-responder',
    lora: 'reasoning-lora & reflection-lora',
    requests: 60,
    concurrency: 12,
    successRate: '100.0%',
    throughputRps: 14.85,
    decodeTps: 594.0,
    totalTps: 1320.5,
    p50Latency: '0.620s',
    p95Latency: '1.240s',
    ttftP50: '82.5 ms',
    tpotP50: '15.1 ms/tok',
    cacheHitRate: '75.0%',
    vramMb: '450.2 MB KV (Shared Pool)',
    statusBadge: 'Multi-Model + kvcached Co-Serving',
    notes: 'Simultaneously exercises vllm-agents (with hot-swapped LoRAs) and vllm-responder on shared 9.8 GB VRAM. Zero OOM.',
    modelsBreakdown: [
      { engine: 'vllm-agents:8081', model: 'Qwen2.5-0.5B', lora: 'reasoning-lora (2.18 MB)', role: 'TriageAgent', reqs: '20 (33.3%)', ttft: '32.1 ms', tpot: '11.2 ms/tok' },
      { engine: 'vllm-agents:8081', model: 'Qwen2.5-0.5B', lora: 'reflection-lora (17.64 MB)', role: 'RedactAgent', reqs: '20 (33.3%)', ttft: '35.4 ms', tpot: '11.8 ms/tok' },
      { engine: 'vllm-responder:8080', model: 'Qwen2.5-1.5B', lora: 'none (Base weights)', role: 'RespondAgent', reqs: '20 (33.3%)', ttft: '564.1 ms', tpot: '18.2 ms/tok' }
    ],
    kvcachedPool: {
      totalGb: '9.8 GB Shared Pool',
      responderGb: '4.41 GB (45%)',
      agentsGb: '2.94 GB (30%)',
      bufferGb: '2.45 GB (25% Dynamic Buffer)',
      preemptions: '0% (Zero OOM Aborts)',
      hitRate: '75.0%',
      acceleration: '5.1x Prefill Speedup'
    }
  },
  long_rag: {
    name: 'long_rag',
    title: '📚 Long-Context RAG Reasoning',
    workload: 'reasoning',
    description: 'Stress-tests chunked prefill memory allocation with long contextual prompts.',
    model: 'Qwen/Qwen2.5-1.5B-Instruct',
    engine: 'vllm-responder',
    lora: 'none',
    requests: 50,
    concurrency: 5,
    successRate: '100.0%',
    throughputRps: 0.68,
    decodeTps: 68.0,
    totalTps: 1420.5,
    p50Latency: '1.410s',
    p95Latency: '62.835s',
    ttftP50: '564.1 ms',
    tpotP50: '28.2 ms/tok',
    cacheHitRate: '0.0%',
    vramMb: '840.0 MB KV',
    statusBadge: 'Chunked Prefill Active',
    notes: 'Tests chunked prefill on the 1.5B reasoning engine without causing CUDA OOM.'
  },
  overload: {
    name: 'overload',
    title: '🔥 High-Burst Concurrency Saturation',
    workload: 'chat',
    description: '1,000 rapid requests at concurrency 100 to evaluate gateway admission backpressure.',
    model: 'Qwen/Qwen2.5-0.5B-Instruct',
    engine: 'vllm-agents',
    lora: 'none',
    requests: 1000,
    concurrency: 100,
    successRate: '100.0%',
    throughputRps: 20.93,
    decodeTps: 837.2,
    totalTps: 1841.8,
    p50Latency: '4.199s',
    p95Latency: '6.060s',
    ttftP50: '335.9 ms',
    tpotP50: '16.8 ms/tok',
    cacheHitRate: '0.0%',
    vramMb: '1250.0 MB KV (Elastic Burst)',
    statusBadge: 'Zero 504 Timeouts Under Peak Burst',
    notes: 'Gateway admission controller enforces smooth queuing, sustaining 20.93 req/s without dropping requests.'
  }
};

function renderBenchmarkScenario(scKey) {
  const data = benchmarkData[scKey];
  if (!data) return;

  // Update button states
  document.querySelectorAll('.bm-sc-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === 'btn-sc-' + scKey);
  });

  // Render detail card
  const detailsEl = document.getElementById('bm-scenario-details');
  if (detailsEl) {
    let html = `
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Scenario Name</span>
        <span class="bm-detail-val" style="color:var(--accent);">${data.title}</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Serving Engine Architecture</span>
        <span class="bm-detail-val" style="color:var(--throughput);">${data.engine || 'vllm-agents'}</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Model & LoRA Configuration</span>
        <span class="bm-detail-val">${data.model} ${data.lora && data.lora !== 'none' ? '<span style="color:var(--kv-gold);">[' + data.lora + ']</span>' : ''}</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Total Requests & Concurrency</span>
        <span class="bm-detail-val">${data.requests} reqs @ c=${data.concurrency}</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Request Throughput</span>
        <span class="bm-detail-val" style="color:var(--accent3);">${data.throughputRps} req/s</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Token Generation (Decode)</span>
        <span class="bm-detail-val" style="color:var(--kv-gold);">${data.decodeTps} tok/s</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Time To First Token (TTFT p50)</span>
        <span class="bm-detail-val">${data.ttftP50}</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Time Per Output Token (TPOT p50)</span>
        <span class="bm-detail-val">${data.tpotP50}</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">kvcached Memory & Efficiency</span>
        <span class="bm-detail-val" style="color:var(--accent);">${data.vramMb || 'Active KV'} (${data.cacheHitRate} Prefix Cache)</span>
      </div>
      <div class="bm-detail-item">
        <span class="bm-detail-lbl">Total Latency (p50 / p95)</span>
        <span class="bm-detail-val">${data.p50Latency} / ${data.p95Latency}</span>
      </div>
    `;

    // Multi-model breakdown table inside scenario if present
    if (data.modelsBreakdown) {
      html += `
        <div class="bm-detail-item" style="grid-column: 1 / -1; background:rgba(255,255,255,0.02); padding:16px; border-radius:10px; border:1px solid var(--border);">
          <span class="bm-detail-lbl" style="color:#fff; margin-bottom:8px; display:block;">🔀 Multi-Model Engine Distribution</span>
          <table style="width:100%; font-size:12px; border-collapse:collapse; text-align:left;">
            <thead>
              <tr style="color:var(--muted); border-bottom:1px solid rgba(255,255,255,0.1);">
                <th style="padding:6px;">Role</th>
                <th style="padding:6px;">Engine & Model</th>
                <th style="padding:6px;">LoRA Adapter</th>
                <th style="padding:6px;">Traffic</th>
                <th style="padding:6px;">TTFT p50</th>
                <th style="padding:6px;">TPOT p50</th>
              </tr>
            </thead>
            <tbody>
              ${data.modelsBreakdown.map(m => `
                <tr style="border-bottom:1px solid rgba(255,255,255,0.04); font-family:var(--font-mono);">
                  <td style="padding:6px; color:var(--accent); font-weight:700;">${m.role}</td>
                  <td style="padding:6px;">${m.engine} (${m.model})</td>
                  <td style="padding:6px; color:var(--kv-gold);">${m.lora}</td>
                  <td style="padding:6px;">${m.reqs}</td>
                  <td style="padding:6px; color:var(--accent3);">${m.ttft}</td>
                  <td style="padding:6px;">${m.tpot}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:11.5px; color:var(--muted); font-family:var(--font-mono);">
            <span>Shared Pool: <strong style="color:var(--kv-gold);">${data.kvcachedPool.totalGb}</strong></span>
            <span>Preemptions: <strong style="color:var(--accent3);">${data.kvcachedPool.preemptions}</strong></span>
            <span>Acceleration: <strong style="color:var(--accent);">${data.kvcachedPool.acceleration}</strong></span>
          </div>
        </div>
      `;
    }

    html += `
      <div class="bm-detail-item" style="grid-column: 1 / -1; background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; border-left:3px solid var(--accent);">
        <span class="bm-detail-lbl" style="color:var(--text);">Architectural Diagnosis</span>
        <span style="font-size:12.5px;color:var(--muted);">${data.notes}</span>
      </div>
    `;

    detailsEl.innerHTML = html;
  }
}

function selectBenchmarkScenario(scKey) {
  renderBenchmarkScenario(scKey);
}

// Initialize Benchmark Charts
function initBenchmarkCharts() {
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#94a3b8', font: { family: 'Inter', size: 11.5 } }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
      },
      y: {
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
      }
    }
  };

  // 1. Latency Decomposition Chart (TTFT vs Decode)
  const ctxDecomp = document.getElementById('chartLatencyDecomposition');
  if (ctxDecomp) {
    new Chart(ctxDecomp.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['short_chat', 'shared_prefix', 'heterogeneous', 'long_rag', 'overload'],
        datasets: [
          {
            label: 'TTFT Prefill Phase (s)',
            data: [0.315, 0.040, 0.082, 0.564, 0.336],
            backgroundColor: '#818cf8'
          },
          {
            label: 'Token Decode Phase (s)',
            data: [0.472, 0.461, 0.538, 0.846, 3.863],
            backgroundColor: '#34d399'
          }
        ]
      },
      options: {
        ...chartOptions,
        scales: {
          x: { stacked: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          y: { stacked: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
        }
      }
    });
  }

  // 2. Prefix Caching Gain Comparison Chart
  const ctxPrefix = document.getElementById('chartPrefixGain');
  if (ctxPrefix) {
    new Chart(ctxPrefix.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['Prefill TTFT (ms)', 'Total Latency (ms)', 'Throughput (req/s)'],
        datasets: [
          {
            label: 'Uncached (short_chat)',
            data: [315, 787, 11.58],
            backgroundColor: 'rgba(248,113,113,0.75)',
            borderColor: '#f87171',
            borderWidth: 1
          },
          {
            label: 'Prefix-Cached (shared_prefix_agents)',
            data: [40, 501, 16.18],
            backgroundColor: 'rgba(52,211,153,0.75)',
            borderColor: '#34d399',
            borderWidth: 1
          }
        ]
      },
      options: chartOptions
    });
  }

  // 3. Concurrency Saturation & Scaling Curve
  const ctxConc = document.getElementById('chartConcurrencyCurve');
  if (ctxConc) {
    new Chart(ctxConc.getContext('2d'), {
      type: 'line',
      data: {
        labels: ['1 conc', '5 conc', '10 conc', '25 conc', '50 conc', '100 conc'],
        datasets: [
          {
            label: 'Throughput (req/s)',
            data: [2.1, 8.4, 16.2, 19.1, 20.4, 20.93],
            borderColor: '#4f9cf9',
            backgroundColor: 'rgba(79,156,249,0.15)',
            fill: true,
            tension: 0.35,
            yAxisID: 'y'
          },
          {
            label: 'Decode Tokens/sec',
            data: [63, 252, 485, 680, 810, 837],
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.35,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        ...chartOptions,
        scales: {
          y: {
            type: 'linear',
            position: 'left',
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: '#f59e0b' }
          },
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
        }
      }
    });
  }

  // 4. Token Processing Throughput Chart
  const ctxTokens = document.getElementById('chartTokensThroughput');
  if (ctxTokens) {
    new Chart(ctxTokens.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['short_chat', 'shared_prefix', 'long_rag', 'overload'],
        datasets: [
          {
            label: 'Decode Token Throughput (tok/s)',
            data: [347.4, 485.4, 68.0, 837.2],
            backgroundColor: '#34d399'
          },
          {
            label: 'Prefill Processing (tok/s)',
            data: [416.8, 582.4, 1352.5, 1004.6],
            backgroundColor: '#a78bfa'
          }
        ]
      },
      options: chartOptions
    });
  }

  // 5. Multi-Model Inference Velocity & Token Generation
  const ctxMulti = document.getElementById('chartMultiModelSpeed');
  if (ctxMulti) {
    new Chart(ctxMulti.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['Qwen-1.5B Responder', 'Qwen-0.5B (reasoning)', 'Qwen-0.5B (reflection)', 'Ollama (CPU Fallback)'],
        datasets: [
          {
            label: 'Decode Speed (tok/s/stream)',
            data: [54.9, 89.3, 84.7, 22.2],
            backgroundColor: '#10b981',
            yAxisID: 'y'
          },
          {
            label: 'Prefill TTFT Latency (ms)',
            data: [564.1, 32.1, 35.4, 820.0],
            backgroundColor: '#6366f1',
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        ...chartOptions,
        scales: {
          y: {
            type: 'linear',
            position: 'left',
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#10b981' },
            title: { display: true, text: 'Decode Velocity (tok/s)', color: '#10b981', font: { size: 10 } }
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: '#6366f1' },
            title: { display: true, text: 'Prefill TTFT (ms)', color: '#6366f1', font: { size: 10 } }
          },
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
        }
      }
    });
  }
}

// Initialize scenario details on load
renderBenchmarkScenario('short_chat');
initBenchmarkCharts();
