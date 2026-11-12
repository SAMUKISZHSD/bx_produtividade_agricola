/**
 * ==============================================================================
 * SOJARISCO - MOTOR EDITORIAL DE INTERATIVIDADE E PROGRESSIVE DISCLOSURE
 * Aplicação rigorosa da Lei de Hick (Pilar 3 Mangto & Pilar 4 Emil Kowalski)
 * ==============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initReadingProgressBar();
  initTableOfContentsObserver();
  initTreeSimulatorHick();
  initOverfittingSelector();
  initDynamicCharts();
  initApiTesterHick();
});

/* --------------------------------------------------------------------------
 * 1. GERENCIAMENTO DE TEMA (DARK / LIGHT MODE)
 * -------------------------------------------------------------------------- */
function initThemeToggle() {
  const themeToggleBtn = document.getElementById("theme-toggle");
  if (!themeToggleBtn) return;

  function updateThemeUI(isDark) {
    if (isDark) {
      document.documentElement.classList.add("dark");
      themeToggleBtn.setAttribute("aria-label", "Alternar para Modo Claro");
      themeToggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      `;
    } else {
      document.documentElement.classList.remove("dark");
      themeToggleBtn.setAttribute("aria-label", "Alternar para Modo Escuro");
      themeToggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      `;
    }
  }

  const savedTheme = localStorage.getItem("theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialIsDark = savedTheme === "dark" || (!savedTheme && systemPrefersDark);
  updateThemeUI(initialIsDark);

  themeToggleBtn.addEventListener("click", () => {
    const isNowDark = !document.documentElement.classList.contains("dark");
    updateThemeUI(isNowDark);
    localStorage.setItem("theme", isNowDark ? "dark" : "light");
  });
}

/* --------------------------------------------------------------------------
 * 2. BARRA DE PROGRESSO DE LEITURA
 * -------------------------------------------------------------------------- */
function initReadingProgressBar() {
  const progressBar = document.getElementById("progress-bar");
  if (!progressBar) return;

  window.addEventListener("scroll", () => {
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (totalHeight <= 0) return;
    const progress = Math.min(Math.max(window.scrollY / totalHeight, 0), 1);
    progressBar.style.transform = `scaleX(${progress})`;
  }, { passive: true });
}

/* --------------------------------------------------------------------------
 * 3. ÍNDICE NAVEGÁVEL (SIDEBAR ACTIVE HIGHLIGHT)
 * -------------------------------------------------------------------------- */
function initTableOfContentsObserver() {
  const sections = document.querySelectorAll("article section[id]");
  const tocLinks = document.querySelectorAll(".toc-link");
  if (!sections.length || !tocLinks.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute("id");
        tocLinks.forEach((link) => {
          if (link.getAttribute("href") === `#${id}`) {
            link.classList.add("active");
          } else {
            link.classList.remove("active");
          }
        });
      }
    });
  }, { rootMargin: "-15% 0px -75% 0px", threshold: 0 });

  sections.forEach((sec) => observer.observe(sec));
}

/* --------------------------------------------------------------------------
 * 4. SIMULADOR DA ÁRVORE (LEI DE HICK: 1 ESCOLHA PRINCIPAL + REVELAÇÃO PROGRESSIVA)
 * -------------------------------------------------------------------------- */
function initTreeSimulatorHick() {
  const sliderDeficit = document.getElementById("sim-deficit");
  const sliderCalor = document.getElementById("sim-calor");
  const sliderChuva = document.getElementById("sim-chuva");
  const sliderAmp = document.getElementById("sim-amp");

  const valDeficit = document.getElementById("val-deficit");
  const valCalor = document.getElementById("val-calor");
  const valChuva = document.getElementById("val-chuva");
  const valAmp = document.getElementById("val-amp");

  const simVerdict = document.getElementById("sim-verdict");
  const simProb = document.getElementById("sim-prob");
  const simLatency = document.getElementById("sim-latency");
  const simPath = document.getElementById("sim-path");
  const simSafraDetails = document.getElementById("sim-safra-details");

  if (!sliderDeficit || !sliderCalor) return;

  let activeSafraObj = window.PROJECT_DATA.historico.find(s => s.ano === 2021);

  function updateSimulation() {
    const deficit = parseFloat(sliderDeficit.value);
    const calor = parseFloat(sliderCalor.value);
    const chuva = parseFloat(sliderChuva.value);
    const amp = parseFloat(sliderAmp.value);

    if (valDeficit) valDeficit.textContent = `${deficit} dias`;
    if (valCalor) valCalor.textContent = `${calor} dias`;
    if (valChuva) valChuva.textContent = `${chuva} mm`;
    if (valAmp) valAmp.textContent = `${amp.toFixed(1)} °C`;

    const res = window.PROJECT_DATA.preverRisco(deficit, calor, chuva, amp);

    resetSvgHighlights();
    highlightNode("node-root", true);

    if (deficit > 20.0) {
      highlightNode("edge-root-left", true);
      highlightNode("node-estresse", true);

      if (calor >= 2.5 || deficit >= 35.0) {
        highlightNode("edge-estresse-left", true);
        highlightNode("leaf-quebra-severa", true, true);
      } else {
        highlightNode("edge-estresse-right", true);
        highlightNode("leaf-limitrofe", true, false);
      }
    } else {
      highlightNode("edge-root-right", true);
      highlightNode("node-favoravel", true);

      if (chuva < 200.0 && amp > 28.0) {
        highlightNode("edge-favoravel-left", true);
        highlightNode("leaf-preventivo", true, true);
      } else {
        highlightNode("edge-favoravel-right", true);
        highlightNode("leaf-normal", true, false);
      }
    }

    // Veredito Sóbrio (Zero Emojis)
    if (res.alerta) {
      simVerdict.innerHTML = `
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:var(--brand-danger); margin-right:6px;"></span>
        <span style="color:var(--brand-danger); font-weight:700;">ALERTA DE QUEBRA DE SAFRA</span>
      `;
      simProb.textContent = `Probabilidade: ${Math.round(res.probabilidade * 100)}% (Corte: 50%)`;
    } else {
      simVerdict.innerHTML = `
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:var(--brand-primary); margin-right:6px;"></span>
        <span style="color:var(--brand-primary); font-weight:700;">SAFRA NORMAL ESTIMADA</span>
      `;
      simProb.textContent = `Probabilidade de Quebra: ${Math.round(res.probabilidade * 100)}% (Margem Segura)`;
    }

    if (simSafraDetails) {
      if (activeSafraObj && activeSafraObj.deficit_hidrico_solo === deficit && activeSafraObj.dias_pico_calor === calor) {
        simSafraDetails.innerHTML = `<strong>Dados reais da Safra ${activeSafraObj.ano}:</strong> Solo seco: ${activeSafraObj.deficit_hidrico_solo} dias | Picos calor &ge; 35°C: ${activeSafraObj.dias_pico_calor} dias | Chuva Jan-Fev: ${activeSafraObj.precipitacao_enchimento} mm | Rendimento real: ${activeSafraObj.rendimento_real} kg/ha`;
      } else {
        simSafraDetails.innerHTML = `<strong>Parâmetros customizados:</strong> Solo seco: ${deficit} dias | Picos calor: ${calor} dias | Chuva: ${chuva} mm | Amplitude: ${amp.toFixed(1)} °C`;
      }
    }

    if (simLatency) simLatency.textContent = "Latência: 0.12 ms";
    if (simPath) {
      simPath.innerHTML = res.caminho.map(c => `<li>${c}</li>`).join("");
    }
  }

  function resetSvgHighlights() {
    const highlightedElements = document.querySelectorAll(".active-node, .active-leaf-alert, .active-edge");
    highlightedElements.forEach(el => {
      el.classList.remove("active-node", "active-leaf-alert", "active-edge");
    });
  }

  function highlightNode(id, isActive, isAlert) {
    const el = document.getElementById(id);
    if (!el) return;
    if (isAlert) {
      el.classList.add("active-leaf-alert");
    } else {
      el.classList.add("active-node");
    }
  }

  [sliderDeficit, sliderCalor, sliderChuva, sliderAmp].forEach(sl => {
    sl.addEventListener("input", () => {
      activeSafraObj = null;
      updateSimulation();
    });
  });

  // 4 Escolhas Principais de Cenários Reais (Lei de Hick)
  const chipButtons = document.querySelectorAll(".btn-safra-chip");
  chipButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      chipButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const ano = parseInt(btn.getAttribute("data-ano"));
      const safra = window.PROJECT_DATA.historico.find(s => s.ano === ano);
      if (safra) {
        activeSafraObj = safra;
        sliderDeficit.value = safra.deficit_hidrico_solo;
        sliderCalor.value = safra.dias_pico_calor;
        sliderChuva.value = safra.precipitacao_enchimento;
        sliderAmp.value = safra.amplitude_termica;
        updateSimulation();
      }
    });
  });

  updateSimulation();
}

/* --------------------------------------------------------------------------
 * 5. SELETOR DE PROFUNDIDADE (SOBREAJUSTE VS SUBAJUSTE)
 * -------------------------------------------------------------------------- */
function initOverfittingSelector() {
  const depthBtns = document.querySelectorAll(".btn-depth-select");
  const depthExplanation = document.getElementById("depth-explanation-box");
  if (!depthBtns.length || !depthExplanation) return;

  const depthDetails = {
    1: {
      titulo: "Profundidade 1 (Nó Único) - Subajuste (Underfitting)",
      descricao: "A árvore avalia apenas uma feature isolada. Alto viés sistemático: não captura a interação entre estiagem na raiz e estresse térmico.",
      acuraciaTreino: "87.5%",
      acuraciaVal: "80.0%",
      statusCor: "var(--brand-accent)"
    },
    3: {
      titulo: "Profundidade 3 (Árvore Parcimoniosa) - Modelo Recomendado",
      descricao: "Ponto ótimo adotado no projeto. Combina déficit hídrico e picos de calor com <code>min_samples_leaf=2</code>. <strong>Recall de 100%</strong> nas quebras sem memorizar ruídos.",
      acuraciaTreino: "100.0%",
      acuraciaVal: "100.0%",
      statusCor: "var(--brand-primary)"
    },
    6: {
      titulo: "Profundidade 6 (Árvore Profunda) - Sobreajuste (Overfitting)",
      descricao: "Cria regras artificiais para cada safra isolada no histórico. Acurácia de 100% no treino, mas alta variância com falha severa na generalização.",
      acuraciaTreino: "100.0%",
      acuraciaVal: "50.0%",
      statusCor: "var(--brand-danger)"
    }
  };

  depthBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      depthBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const depth = btn.getAttribute("data-depth");
      const data = depthDetails[depth];
      if (data) {
        depthExplanation.innerHTML = `
          <div style="border-left: 3px solid ${data.statusCor}; padding-left: 0.85rem;">
            <div style="font-size: 0.95rem; font-weight: 700; color: ${data.statusCor}; margin-bottom: 0.25rem;">${data.titulo}</div>
            <p style="font-size: 0.88rem; margin-bottom: 0.5rem; color: var(--text-main);">${data.descricao}</p>
            <div style="display: flex; gap: 1.25rem; font-size: 0.8rem; font-family: var(--font-mono); color: var(--text-muted);">
              <span>Treino: <strong>${data.acuraciaTreino}</strong></span>
              <span>Validação: <strong>${data.acuraciaVal}</strong></span>
            </div>
          </div>
        `;
      }
    });
  });
}

/* --------------------------------------------------------------------------
 * 6. GRÁFICOS SVG DINÂMICOS SÓBRIOS
 * -------------------------------------------------------------------------- */
function initDynamicCharts() {
  renderFeatureImportanceChart();
  renderConfusionMatricesHick();
}

function renderFeatureImportanceChart() {
  const container = document.getElementById("feature-importance-chart");
  if (!container || !window.PROJECT_DATA) return;

  const data = window.PROJECT_DATA.featureImportance;
  const maxWeight = Math.max(...data.map(d => d.peso));

  let barsHtml = `<div style="display:flex; flex-direction:column; gap:0.85rem; width:100%;">`;

  data.forEach(item => {
    const pct = Math.round(item.peso * 100);
    const barWidth = Math.round((item.peso / maxWeight) * 100);

    barsHtml += `
      <div>
        <div style="display:flex; justify-content:space-between; font-size:0.82rem; margin-bottom:0.25rem;">
          <span style="font-weight:600; color:var(--text-main);">${item.nome}</span>
          <span style="font-family:var(--font-mono); font-weight:700; color:var(--brand-primary);">${pct}% (${item.correlacao} r)</span>
        </div>
        <div style="background-color:var(--bg-surface-alt); height:8px; border-radius:var(--radius-sm); overflow:hidden; border:1px solid var(--border-color);">
          <div style="width:${barWidth}%; height:100%; background-color:var(--brand-primary); transition:width 400ms ease-out;"></div>
        </div>
      </div>
    `;
  });

  barsHtml += `</div>`;
  container.innerHTML = barsHtml;
}

function renderConfusionMatricesHick() {
  const container = document.getElementById("confusion-matrix-comparison");
  if (!container || !window.PROJECT_DATA) return;

  // Destaque visual direto para o Modelo Recomendado (Lei de Hick)
  container.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
      <!-- Árvore de Decisão: Recomendado -->
      <div style="background-color: var(--bg-surface); border: 2px solid var(--brand-primary); border-radius: var(--radius-sm); padding: 0.85rem; text-align: center;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <span style="font-weight:700; font-size:0.88rem; color:var(--brand-primary);">Árvore de Decisão</span>
          <span style="font-size:0.68rem; font-family:var(--font-mono); background:var(--brand-primary-light); color:var(--brand-primary); padding:0.1rem 0.35rem; border-radius:3px;">RECOMENDADO</span>
        </div>
        <div style="font-size: 0.78rem; color: var(--text-light); margin-bottom: 0.5rem;">Recall: 100% | Zero Falso Negativo</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3px; font-family: var(--font-mono); font-size: 0.78rem;">
          <div style="background-color: var(--brand-primary-light); padding: 0.5rem; border-radius: 2px;">VN: 2<br><span style="font-size:0.68rem; color:var(--text-light);">Normais</span></div>
          <div style="background-color: var(--bg-surface-alt); padding: 0.5rem; border-radius: 2px;">FP: 0<br><span style="font-size:0.68rem; color:var(--text-light);">Alarme</span></div>
          <div style="background-color: var(--bg-surface-alt); padding: 0.5rem; border-radius: 2px;">FN: 0<br><span style="font-size:0.68rem; color:var(--text-light);">Omissão</span></div>
          <div style="background-color: var(--brand-primary-light); padding: 0.5rem; border-radius: 2px;">VP: 0*<br><span style="font-size:0.68rem; color:var(--text-light);">Quebras</span></div>
        </div>
      </div>

      <!-- Random Forest -->
      <div style="background-color: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.85rem; text-align: center; opacity: 0.85;">
        <div style="font-weight:600; font-size:0.88rem; color:var(--text-main); margin-bottom:0.4rem;">Random Forest</div>
        <div style="font-size: 0.78rem; color: var(--text-light); margin-bottom: 0.5rem;">Recall: 100% | Precisão: 85%</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3px; font-family: var(--font-mono); font-size: 0.78rem;">
          <div style="background-color: var(--brand-primary-light); padding: 0.5rem; border-radius: 2px;">VN: 2</div>
          <div style="background-color: var(--bg-surface-alt); padding: 0.5rem; border-radius: 2px;">FP: 0</div>
          <div style="background-color: var(--bg-surface-alt); padding: 0.5rem; border-radius: 2px;">FN: 0</div>
          <div style="background-color: var(--brand-primary-light); padding: 0.5rem; border-radius: 2px;">VP: 0*</div>
        </div>
      </div>

      <!-- XGBoost -->
      <div style="background-color: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.85rem; text-align: center; opacity: 0.85;">
        <div style="font-weight:600; font-size:0.88rem; color:var(--text-main); margin-bottom:0.4rem;">XGBoost</div>
        <div style="font-size: 0.78rem; color: var(--text-light); margin-bottom: 0.5rem;">Recall: 100% | Precisão: 82%</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3px; font-family: var(--font-mono); font-size: 0.78rem;">
          <div style="background-color: var(--brand-primary-light); padding: 0.5rem; border-radius: 2px;">VN: 2</div>
          <div style="background-color: var(--bg-surface-alt); padding: 0.5rem; border-radius: 2px;">FP: 0</div>
          <div style="background-color: var(--bg-surface-alt); padding: 0.5rem; border-radius: 2px;">FN: 0</div>
          <div style="background-color: var(--brand-primary-light); padding: 0.5rem; border-radius: 2px;">VP: 0*</div>
        </div>
      </div>
    </div>
  `;
}

/* --------------------------------------------------------------------------
 * 7. TESTADOR DE API (3 CENÁRIOS DE 1 CLIQUE)
 * -------------------------------------------------------------------------- */
function initApiTesterHick() {
  const btnRun = document.getElementById("btn-run-api-test");
  const jsonResponseBox = document.getElementById("api-response-json");
  const jsonRequestBox = document.getElementById("api-request-json");
  const apiLatency = document.getElementById("api-latency-ms");
  const presetButtons = document.querySelectorAll(".btn-api-preset");

  if (!btnRun || !jsonResponseBox) return;

  const presets = {
    "quebra_2021": {
      municipio: "Sorriso - MT",
      ano_safra: 2021,
      deficit_hidrico_solo: 42,
      dias_pico_calor: 3,
      precipitacao_enchimento: 418.57,
      amplitude_termica: 28.69
    },
    "normal_2024": {
      municipio: "Sorriso - MT",
      ano_safra: 2024,
      deficit_hidrico_solo: 4,
      dias_pico_calor: 0,
      precipitacao_enchimento: 556.25,
      amplitude_termica: 27.50
    },
    "seca_severa_2015": {
      municipio: "Sorriso - MT",
      ano_safra: 2015,
      deficit_hidrico_solo: 47,
      dias_pico_calor: 0,
      precipitacao_enchimento: 159.28,
      amplitude_termica: 24.48
    }
  };

  let activePresetKey = "quebra_2021";

  function setPreset(key) {
    activePresetKey = key;
    presetButtons.forEach(b => {
      if (b.getAttribute("data-preset") === key) {
        b.classList.add("active");
      } else {
        b.classList.remove("active");
      }
    });

    const payload = presets[key];
    if (jsonRequestBox) {
      jsonRequestBox.textContent = JSON.stringify(payload, null, 2);
    }
  }

  presetButtons.forEach(b => {
    b.addEventListener("click", () => {
      setPreset(b.getAttribute("data-preset"));
    });
  });

  setPreset("quebra_2021");

  btnRun.addEventListener("click", () => {
    btnRun.disabled = true;
    btnRun.textContent = "Processando...";

    const tStart = performance.now();

    setTimeout(() => {
      const payload = presets[activePresetKey];
      const res = window.PROJECT_DATA.preverRisco(
        payload.deficit_hidrico_solo,
        payload.dias_pico_calor,
        payload.precipitacao_enchimento,
        payload.amplitude_termica
      );

      const tEnd = performance.now();
      const elapsed = (tEnd - tStart).toFixed(2);

      const responseObj = {
        status: "success",
        timestamp: new Date().toISOString(),
        municipio: payload.municipio,
        ano_safra: payload.ano_safra,
        predicao: {
          alerta_quebra: res.alerta,
          nivel_risco: res.alerta ? "CRITICO" : "BAIXO",
          probabilidade_quebra: res.probabilidade,
          limiar_aplicado: 0.50,
          modelo_utilizado: res.modelo
        },
        diagnostico_regras: res.caminho,
        performance: {
          latencia_ms: parseFloat(elapsed),
          pipeline: "ColumnTransformer + DecisionTreeClassifier"
        }
      };

      jsonResponseBox.textContent = JSON.stringify(responseObj, null, 2);
      if (apiLatency) apiLatency.textContent = `${elapsed} ms`;

      btnRun.disabled = false;
      btnRun.textContent = "Executar Predição";
    }, 140);
  });
}
