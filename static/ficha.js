/* ==========================================================
   Ficha D&D 5.5 INTERATIVA — cascata de escolhas que auto-preenche
   ========================================================== */
(function () {
  "use strict";

  const pid = parseInt(location.pathname.split("/ficha/")[1], 10);
  if (!pid) { document.body.innerHTML = "<p style='padding:40px'>Informe um ID: /ficha/&lt;id&gt;</p>"; return; }

  const root = document.getElementById("ficha-root");
  let state = null;   // resposta /full

  // ============================================================
  // Toon Fire Shader (Three.js) — para a patente "Lenda".
  // Adaptado do CodePen MWyxYjw (Yugam, 2020) — sem bloom (canvas pequeno).
  // ============================================================
  let _threeLoadPromise = null;
  function _loadThree() {
    if (window.THREE) return Promise.resolve();
    if (_threeLoadPromise) return _threeLoadPromise;
    _threeLoadPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/three@0.120.0/build/three.min.js";
      s.onload = resolve;
      s.onerror = () => reject(new Error("falha carregando three.js"));
      document.head.appendChild(s);
    });
    return _threeLoadPromise;
  }

  // Cleanup function da última instância renderizada (re-render destroi a anterior).
  let _toonFireCleanup = null;
  async function mountToonFire(container) {
    if (_toonFireCleanup) { try { _toonFireCleanup(); } catch (e) {} _toonFireCleanup = null; }
    if (!container) return;
    await _loadThree();
    const THREE = window.THREE;

    const W = container.clientWidth || 200;
    const H = container.clientHeight || 60;

    const scene = new THREE.Scene();
    // Câmera ortográfica + plano 2x2 = preenche viewport inteiro com UV 0..1
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);  // transparente — bg dark vem do CSS
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const uniforms = {
      time: { value: 10.0 },
      resolution: { value: new THREE.Vector2(W, H) },
      // base (interior) e border — RGB 0..255 (shader divide por 255)
      color1: { value: new THREE.Vector3(255, 200, 80) },   // base dourada
      color0: { value: new THREE.Vector3(120, 30, 0) },     // borda vermelho-escuro
    };

    const vert = `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;
    const frag = `
      #define NUM_OCTAVES 5
      uniform vec2 resolution;
      uniform vec3 color1;
      uniform vec3 color0;
      uniform float time;
      varying vec2 vUv;

      float rand(vec2 n) {
        return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
      }
      float noise(vec2 p){
        vec2 ip = floor(p);
        vec2 u = fract(p);
        u = u*u*(3.0-2.0*u);
        float res = mix(
          mix(rand(ip), rand(ip+vec2(1.0,0.0)), u.x),
          mix(rand(ip+vec2(0.0,1.0)), rand(ip+vec2(1.0,1.0)), u.x), u.y);
        return res*res;
      }
      float fbm(vec2 x) {
        float v = 0.0;
        float a = 0.5;
        vec2 shift = vec2(100);
        mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
        for (int i = 0; i < NUM_OCTAVES; ++i) {
          v += a * noise(x);
          x = rot * x * 2.0 + shift;
          a *= 0.5;
        }
        return v;
      }
      vec3 rgbcol(float r, float g, float b) {
        return vec3(r/255.0, g/255.0, b/255.0);
      }
      float setOpacity(float r, float g, float b) {
        float tone = (r + g + b) / 3.0;
        return tone < 0.99 ? 0.0 : 1.0;
      }
      void main() {
        // UV aspect-corrected pra ruído ficar isotrópico (não esticado em retângulo)
        vec2 uv = vUv;
        vec2 uvAspect = uv;
        uvAspect.x *= resolution.x / resolution.y;

        vec2 newUv = uvAspect + vec2(0.0, -time * 0.0004);
        float scale = 6.0;
        vec2 p = newUv * scale;
        float n = fbm(p + fbm(p));

        // Verticalidade: chama mais densa embaixo, dispersa em cima.
        float vert = uv.y;

        vec4 backColor = vec4(1.0 - vert) + vec4(vec3(n*(1.0 - vert)), 1.0);
        float aback = setOpacity(backColor.r, backColor.g, backColor.b);
        backColor.a = aback;
        backColor.rgb = rgbcol(color1.r, color1.g, color1.b);

        vec4 frontColor = vec4(1.08 - vert) + vec4(vec3(n*(1.0 - vert)), 1.0);
        float afront = setOpacity(frontColor.r, frontColor.g, frontColor.b);
        frontColor.a = afront;
        frontColor.rgb = rgbcol(color0.r, color0.g, color0.b);

        frontColor.a = frontColor.a - backColor.a;
        if (frontColor.a > 0.0) gl_FragColor = frontColor;
        else                    gl_FragColor = backColor;
      }
    `;
    // Plano 2x2 cobre o frustum [-1,1] × [-1,1] da câmera ortográfica
    const geo = new THREE.PlaneGeometry(2, 2);
    const mat = new THREE.ShaderMaterial({
      uniforms,
      transparent: true,
      vertexShader: vert,
      fragmentShader: frag,
    });
    const mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);

    let raf = null;
    let alive = true;
    function loop(delta) {
      if (!alive) return;
      raf = requestAnimationFrame(loop);
      uniforms.time.value = delta;
      renderer.render(scene, camera);
    }
    raf = requestAnimationFrame(loop);

    _toonFireCleanup = () => {
      alive = false;
      if (raf) cancelAnimationFrame(raf);
      geo.dispose();
      mat.dispose();
      renderer.dispose();
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    };
  }

  const mod = v => Math.floor(((v||10) - 10) / 2);
  const sgn = n => (n >= 0 ? `+${n}` : String(n));

  // Bônus de proficiência por nível (D&D 5.5)
  function profByLevel(n) {
    if (n >= 17) return 6;
    if (n >= 13) return 5;
    if (n >=  9) return 4;
    if (n >=  5) return 3;
    return 2;
  }

  // Médias (arredondadas p/ cima) para cálculo de PV pós-nv 1
  const HD_AVG = { d6: 4, d8: 5, d10: 6, d12: 7 };
  const HD_MAX = { d6: 6, d8: 8, d10: 10, d12: 12 };

  function calcPVMax(hd, nivel, conMod) {
    if (!hd || !HD_MAX[hd]) return null;
    // nivel 1: HD máx + CON  |  demais: média + CON  (D&D 5e)
    const maxL1  = HD_MAX[hd] + conMod;
    const perLv  = HD_AVG[hd] + conMod;
    return maxL1 + (nivel - 1) * perLv;
  }

  // Multiclasse (D&D 5.5): só o primeiro nível da PRIMEIRA classe usa HD_MAX.
  // Todos os outros níveis (mesma classe ou classe nova) usam HD_AVG do dado de vida
  // dessa classe específica. Cada classe contribui CON × Nivel.
  // classes: [{DadoVida, Nivel, Ordem}], conMod: number
  function calcPVMaxMC(classes, conMod) {
    if (!Array.isArray(classes) || !classes.length) return null;
    const ordered = [...classes].sort((a, b) => (a.Ordem ?? 99) - (b.Ordem ?? 99));
    let total = 0;
    ordered.forEach((c, idx) => {
      const hd = c.DadoVida;
      const nv = c.Nivel || 0;
      if (!hd || !HD_MAX[hd] || nv <= 0) return;
      if (idx === 0) {
        total += HD_MAX[hd] + conMod;          // primeiro nível da primeira classe
        total += (nv - 1) * (HD_AVG[hd] + conMod); // resto da primeira classe
      } else {
        total += nv * (HD_AVG[hd] + conMod);   // classe secundária inteira em média
      }
    });
    return total;
  }

  // Retorna valor final do atributo (base + bg + ASI desbloqueado).
  // Prioridade: state.atributos_efetivos.valores (calculado pelo backend), fallback antigo.
  function atrFinal(state, key) {
    const efetivos = state.atributos_efetivos?.valores;
    if (efetivos && key in efetivos) return efetivos[key];
    const base = state.personagem.atributos[key] || 10;
    const bg = state.personagem.BackgroundBonusJSON
      ? (JSON.parse(state.personagem.BackgroundBonusJSON)[key] || 0) : 0;
    return base + bg;
  }

  // ---------- API helpers ----------
  const api = {
    full:          () => fetch(`/api/personagens/${pid}/full`).then(r => r.json()),
    patch: (body)  => fetch(`/api/personagens/${pid}`, {
      method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
    }).then(r => r.json()),
    racas:         () => fetch("/api/racas").then(r => r.json()),
    linhagens: (slug)=> fetch(`/api/racas/${slug}/linhagens`).then(r => r.json()),
    essencias:     () => fetch("/api/essencias").then(r => r.json()),
    essLinhagens: (slug) => fetch(`/api/essencias/${slug}/linhagens`).then(r => r.json()),
    classes:       () => fetch("/api/classes").then(r => r.json()),
    subclasses: (slug) => fetch(`/api/classes/${slug}/subclasses`).then(r => r.json()),
  };

  // ---------- MODAL custom: Editar classe (subclasse + nivel + remover) ----------
  function openClasseEditor({ title, classeAtual, subclasses, niveisMax, onSave, onRemove, multiclassReq, multiclassProf, ordem }) {
    const back = document.createElement("div");
    back.className = "picker-backdrop";
    const subOptions = subclasses.map(s =>
      `<option value="${s.Id_Subclasse}" ${s.Id_Subclasse===classeAtual.Id_Subclasse?'selected':''}>${escapeHtmlBare(s.Nome)}</option>`
    ).join("");
    const niveisOptions = Array.from({length: niveisMax}, (_, i) => i+1).map(n =>
      `<option value="${n}" ${n===classeAtual.Nivel?'selected':''}>${n}</option>`
    ).join("");
    // Info de multiclasse: req + profs ganhas (apenas Ordem >= 1 = multiclasse)
    let infoHTML = "";
    if (ordem !== undefined && ordem >= 1) {
      let reqStr = "—";
      if (multiclassReq) {
        try {
          const r = typeof multiclassReq === "string" ? JSON.parse(multiclassReq) : multiclassReq;
          if (r.atribs) {
            const conector = (r.logica === "any") ? " ou " : " e ";
            reqStr = r.atribs.map(a => `${a} ${r.min}+`).join(conector);
          }
        } catch {}
      }
      let profStr = "—";
      try {
        const p = multiclassProf ? (typeof multiclassProf === "string" ? JSON.parse(multiclassProf) : multiclassProf) : [];
        if (p.length) profStr = p.join(", ");
      } catch {}
      infoHTML = `<div style="font-size:11px; color:#555; background:#fff8e6; padding:6px 8px; border-left: 2px solid var(--accent); margin-top:4px">
        <b>Multiclasse (Ordem ${ordem+1})</b><br>
        Pré-requisito: <b>${escapeHtmlBare(reqStr)}</b><br>
        Proficiências ganhas: <b>${escapeHtmlBare(profStr)}</b>
      </div>`;
    }
    back.innerHTML = `
      <div class="picker classe-editor">
        <div class="picker-head">${title}</div>
        <div class="picker-body" style="padding:12px 16px; display:flex; flex-direction:column; gap:12px">
          ${infoHTML}
          <label style="display:flex; flex-direction:column; gap:4px; font-size:12px">
            <b>Subclasse</b>
            <select data-field="Id_Subclasse" style="padding:6px; font-size:13px">
              <option value="">— sem subclasse —</option>
              ${subOptions}
            </select>
          </label>
          <label style="display:flex; flex-direction:column; gap:4px; font-size:12px">
            <b>Nível nesta classe (1–${niveisMax})</b>
            <select data-field="Nivel" style="padding:6px; font-size:13px">
              ${niveisOptions}
            </select>
          </label>
        </div>
        <div class="picker-foot">
          ${onRemove ? '<button class="picker-btn" data-act="remove" style="margin-right:auto; background:#c62828; color:#fff">Remover classe</button>' : ''}
          <button class="picker-btn" data-close>Cancelar</button>
          <button class="picker-btn bg-save" data-act="save">Salvar</button>
        </div>
      </div>`;
    function close() { back.remove(); }
    back.addEventListener("click", (e) => {
      if (e.target === back || e.target.dataset.close !== undefined) close();
    });
    back.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    document.body.appendChild(back);
    back.querySelector('[data-act="save"]').addEventListener("click", async () => {
      const idSub = back.querySelector('[data-field="Id_Subclasse"]').value || null;
      const nivel = parseInt(back.querySelector('[data-field="Nivel"]').value, 10);
      close();
      await onSave({ Id_Subclasse: idSub ? parseInt(idSub, 10) : null, Nivel: nivel });
    });
    if (onRemove) {
      back.querySelector('[data-act="remove"]').addEventListener("click", async () => {
        if (!confirm("Remover essa classe do personagem?")) return;
        close();
        await onRemove();
      });
    }
  }

  // ---------- MODAL de escolha ----------
  function openPicker({ title, options, onPick, renderOption }) {
    const back = document.createElement("div");
    back.className = "picker-backdrop";
    back.innerHTML = `
      <div class="picker">
        <div class="picker-head">${title}</div>
        <div class="picker-search-row">
          <input type="search" class="picker-search" placeholder="Buscar pelo nome (Esc fecha)…" autocomplete="off" />
          <span class="picker-search-count"></span>
        </div>
        <div class="picker-list"></div>
        <div class="picker-foot">
          <button class="picker-btn" data-close>Cancelar</button>
        </div>
      </div>`;
    const list = back.querySelector(".picker-list");
    const search = back.querySelector(".picker-search");
    const countEl = back.querySelector(".picker-search-count");
    // armazena items + texto buscável pra filtragem rápida
    const items = options.map(opt => {
      const item = document.createElement("button");
      item.className = "picker-item";
      item.innerHTML = renderOption
        ? renderOption(opt)
        : `<b>${opt.Nome}</b>${opt.Tagline ? `<br><small>${opt.Tagline}</small>` : ""}${opt.Descricao ? `<br><small>${opt.Descricao}</small>` : ""}`;
      item.addEventListener("click", () => { close(); onPick(opt); });
      list.appendChild(item);
      const haystack = [
        opt.Nome, opt.Slug, opt.Descricao, opt.Tagline,
        opt.TagsJSON, opt.PreReqTexto,
      ].filter(Boolean).join(" ").toLowerCase()
       .normalize("NFD").replace(/[̀-ͯ]/g, "");
      return { el: item, haystack };
    });
    function applyFilter() {
      const q = (search.value || "").toLowerCase()
        .normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
      let visible = 0;
      items.forEach(({ el, haystack }) => {
        const match = !q || haystack.includes(q);
        el.style.display = match ? "" : "none";
        if (match) visible++;
      });
      countEl.textContent = q ? `${visible}/${items.length}` : `${items.length}`;
    }
    search.addEventListener("input", applyFilter);
    applyFilter();
    back.addEventListener("click", (e) => { if (e.target === back || e.target.dataset.close !== undefined) close(); });
    back.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    document.body.appendChild(back);
    setTimeout(() => search.focus(), 50);
    function close() { back.remove(); }
  }

  // ---------- Render principal ----------
  async function load() {
    state = await api.full();
    render();
  }

  // Catálogos de idioma/ferramenta vêm de TB_OpcaoJogo (Tipo='idioma'|'ferramenta').
  // Cache no escopo wrapper — compartilhado por render() e pickBackground().
  const _catalogCache = {};
  const fetchCatalogo = async (tipo) => {
    if (_catalogCache[tipo]) return _catalogCache[tipo];
    try {
      const r = await fetch(`/api/opcoes?tipo=${encodeURIComponent(tipo)}`);
      const opts = r.ok ? await r.json() : [];
      return _catalogCache[tipo] = opts.map(o => o.Nome).filter(Boolean)
        .sort((a, b) => a.localeCompare(b, "pt"));
    } catch { return []; }
  };

  function render() {
    const p = state.personagem;
    const atribs = p.atributos || {};
    const esc = p.escolha || {};
    const skips = [];

    const el = document.createElement("div");
    el.className = "ficha";

    // ===== HEADER =====
    // Multiclasse: linha resumo "Paladino 6 / Clérigo 3", lista detalhada abaixo do nivel.
    const classes = state.classes || [];
    const classeResumo = classes.length
      ? classes.map(c => `${c.NomeClasse} ${c.Nivel}`).join(" / ")
      : (state.classe ? `${state.classe.Nome} ${p.Nivel || 0}` : "<i>clique para escolher</i>");
    // Subclasse line: "Devoção / —" mostrando subclasse de cada classe na ordem
    const subResumo = classes.length
      ? classes.map(c => c.NomeSubclasse || "—").join(" / ")
      : (state.subclasse ? state.subclasse.Nome : "<i>subclasse…</i>");
    const racaTit = state.raca
      ? state.raca.Nome
        + (state.linhagem ? ` / ${state.linhagem.Nome}` : "")
        + (state.essencia ? ` · ${state.essencia.Nome}` : "")
        + (state.ess_linhagem ? ` (${state.ess_linhagem.Nome})` : "")
      : "<i>clique para escolher</i>";
    el.insertAdjacentHTML("beforeend", `
      <div class="f-header">
        <div class="f-name" data-pick="nome">
          <h1>${p.Nome}</h1>
          <small>CHARACTER NAME</small>
        </div>
        <div class="f-meta">
          ${classes.length
            ? classes.map((c, i) => `
                <div class="meta-line"><span class="t">${escapeHtmlBare(c.NomeClasse)} ${c.Nivel}</span><span>CLASSE ${i+1}</span></div>
                <div class="meta-line"><span>${escapeHtmlBare(c.NomeSubclasse || "—")}</span><span>SUBCLASSE ${i+1}</span></div>
              `).join("")
            : '<div class="meta-line"><span class="t"><i>clique para escolher</i></span><span>CLASSE</span></div>'
          }
          <div class="meta-line clickable" data-pick="raca"><span>${racaTit}</span><span>RAÇA</span></div>
          <div class="meta-line clickable" data-pick="background"><span>${p.BackgroundNome || "<i>clique para escolher</i>"}${bgBonusText(p.BackgroundBonusJSON)}</span><span>BACKGROUND</span></div>
          <div class="meta-line"><span>${p.Aventuras ?? "—"}</span><span>AVENTURAS</span></div>
          <div class="meta-line"><span>${p.ProximoNivel ?? "—"}</span><span>PRÓXIMO NÍVEL</span></div>
        </div>
        <div class="f-level">
          <div class="lvtotal">
            <div class="lvnum">${state.nivel_total ?? p.Nivel ?? 0}</div>
            <div class="lvlbl">NÍVEL TOTAL</div>
          </div>
          <div class="lv-classes">
            ${classes.map((c) => `
              <div class="lv-row clickable" data-pick-classe-row data-id-pc="${c.Id_PersonagemClasse}" title="Editar ${escapeHtmlBare(c.NomeClasse)}">
                <span class="lv-cls">${escapeHtmlBare(c.NomeClasse)}</span>
                <span class="lv-n">Nv ${c.Nivel}</span>
                <span class="lv-sub">${escapeHtmlBare(c.NomeSubclasse || "— sem subclasse")}</span>
              </div>
            `).join("")}
            <div class="lv-add clickable" data-pick-classe-add title="Adicionar classe (multiclasse)">
              <span>+ adicionar classe</span>
            </div>
          </div>
        </div>
      </div>`);

    // ===== MAIN =====
    // Total final = base + background + ASI (talentos de classe não-locked).
    // atrFinal() consulta state.atributos_efetivos.valores (vem do backend já somado).
    const bgBonus = p.BackgroundBonusJSON ? JSON.parse(p.BackgroundBonusJSON) : {};
    const attrsHTML = [
      ["FOR","Forca"], ["DES","Destreza"], ["CON","Constituicao"],
      ["INT","Inteligencia"], ["SAB","Sabedoria"], ["CAR","Carisma"],
    ].map(([l, k]) => {
      const total = atrFinal(state, k);
      const base = atribs[k] || 10;
      const extras = total - base;  // bg + ASI somados
      const bonusMark = extras > 0 ? `<span class="bg-mark" title="${extras} via background/talentos">+${extras}</span>` : "";
      return `<div class="attr clickable" data-pick="attr" data-attr="${k}">
        <div class="lbl">${l}</div>
        <div class="vals"><div class="mod">${sgn(mod(total))}</div><div class="raw">${total ?? '?'}${bonusMark}</div></div>
      </div>`;
    }).join("");

    // bônus de proficiência: auto pelo nível
    const prof = profByLevel(p.Nivel || 1);
    const SK_ABBR = { FOR:"For", DES:"Des", CON:"Con", INT:"Int", SAB:"Sab", CAR:"Car" };
    const skillsHTML = (state.pericias || []).map(s => {
      const atrFin = atrFinal(state, { FOR:"Forca", DES:"Destreza", CON:"Constituicao",
                                       INT:"Inteligencia", SAB:"Sabedoria", CAR:"Carisma" }[s.Atributo]);
      const m = mod(atrFin);
      const bonus = m + (s.Proficiente ? prof : 0) + (s.Expertise ? prof : 0);
      const dotCls = s.Expertise ? "dot exp" : (s.Proficiente ? "dot prof" : "dot");
      return `<div class="skill"><div class="${dotCls}"></div><div class="bonus">${sgn(bonus)}</div><div>${s.Nome}</div><div class="atr">${SK_ABBR[s.Atributo]||s.Atributo}</div></div>`;
    }).join("") || skips.push("Perícias vazias") && "";

    // HP calculado com base em dado de vida + nível + CON (com bônus de BG)
    // + bônus vindos de talentos de origem (ex.: Robusto = 2 × nível)
    // Multiclasse: usa state.classes pra dar HD_MAX só no Nv 1 da primeira classe;
    // demais níveis (mesma ou outra classe) usam HD_AVG do dado de vida daquela classe.
    const hd     = state.classe?.DadoVida;
    const conFin = atrFinal(state, "Constituicao");
    const conMod = mod(conFin);
    const pvBaseMC = calcPVMaxMC(state.classes || [], conMod);
    const pvBase = pvBaseMC ?? calcPVMax(hd, p.Nivel || 1, conMod) ?? p.PVMaximo ?? null;
    const pvBonusOrigem = state.pv_bonus_origem?.total || 0;
    const pvBonusFontes = state.pv_bonus_origem?.fontes || [];
    const pvMax  = (pvBase != null) ? (pvBase + pvBonusOrigem) : "?";
    const pvAtu  = p.PVAtual ?? pvMax;

    const pers = (state.personalidade || []).reduce((a, p) => { a[p.Tipo] = p.Texto; return a; }, {});

    el.insertAdjacentHTML("beforeend", `
      <div class="f-main">
        <div class="f-attrs">${attrsHTML}</div>
        <div class="f-skills-outer">
          <div class="f-subclass clickable" data-pick="subclasse">${(state.subclasse?.Nome || "ESCOLHA A SUBCLASSE").toUpperCase()}</div>
          <div class="f-profbonus"><div class="val">+${prof}</div><div>BÔNUS DE PROFICIÊNCIA (auto)</div></div>
          <div class="box"><h3>Testes de Resistência</h3><div class="skills">${renderSaves(state, prof).join("")}</div></div>
          <div class="box"><h3>Perícias</h3><div class="skills">${skillsHTML}</div></div>
        </div>
        <div class="f-center">
          <div class="ca-row">
            ${(() => {
              // CA: prefere o cálculo dinâmico (state.ca_efetiva) sobre o campo livre p.CA.
              // Override: se p.CA foi preenchido manualmente e difere do calculado, mostra "*" + tooltip.
              const ce = state.ca_efetiva || {};
              const calc = ce.valor;
              const tooltip = ce.detalhe ? escapeHtmlBare(ce.detalhe) : "CA calculada";
              const usedManual = (p.CA != null) && (calc != null) && (p.CA !== calc);
              const valor = (calc != null) ? calc : (p.CA ?? "?");
              const star = usedManual ? `<sup style="color:#b46b22;font-size:9px" title="Override manual: DB=${p.CA} · Calculado=${calc}">*</sup>` : "";
              return `<div class="ca-circle" title="${tooltip}">
                <div class="v">${valor}${star}</div>
                <div class="l">CA</div>
              </div>`;
            })()}
            <div class="ca-circle"><div class="v">${sgn(p.Iniciativa ?? mod(atribs.Destreza))}</div><div class="l">INIC</div></div>
            ${(() => {
              const mv = state.movimentos || {};
              const ICONS = { andar: "🚶", voar: "✈", nadar: "🏊", cavar: "⛏", escalar: "🧗" };
              const KINDS = ["andar", "voar", "nadar", "cavar", "escalar"];
              const rows = KINDS.map(k => {
                const m = mv[k];
                const right = m ? `${m.ft} ft / ${m.m} m` : `<span style="color:#bbb">—</span>`;
                const titleAttr = (m && m.origem && m.origem !== "base")
                  ? ` title="origem: ${escapeHtmlBare(m.origem)}"` : "";
                return `<div class="vel-row"${titleAttr}>
                  <span class="vel-kind">${ICONS[k]} ${k}</span>
                  <span class="vel-val">${right}</span>
                </div>`;
              }).join("");
              return `<div class="vel-box">
                <div class="vel-head">VEL</div>
                ${rows}
              </div>`;
            })()}
          </div>
          <div class="f-hp">
            <div class="big">${pvMax}</div>
            <div class="lbl">Pontos de Vida Máximos</div>
            <div class="mini"><small style="color:#888">${
              (state.classes || []).length > 1
                ? (state.classes || []).slice().sort((a,b)=>(a.Ordem??99)-(b.Ordem??99))
                    .map(c => `${escapeHtmlBare(c.NomeClasse)} ${c.Nivel}${c.DadoVida || ""}`).join(" / ")
                : `${hd || "?"} · nv ${p.Nivel || 1}`
            } · CON ${sgn(conMod)}${
              pvBonusOrigem ? ` · <span title="${escapeHtmlBare(pvBonusFontes.map(f => `${f.nome}: +${f.valor}`).join(', '))}">+${pvBonusOrigem} (origem)</span>` : ""
            }</small></div>
            ${(state.inventario || []).filter(i => i.Sintonizado).length
                ? `<ul>${state.inventario.filter(i => i.Sintonizado).map(i => `<li>${i.Item}</li>`).join("")}</ul>
                   <div class="lbl">Itens Sintonizados</div>`
                : `<div class="lbl" style="color:#bbb">sem sintonizados</div>`}
          </div>
          ${(() => {
            // Patente derivada do nível. Lv 20 deixa user ciclar entre Rubi/Diamante/Lenda.
            const nivel = state.nivel_total ?? p.Nivel ?? 1;
            const lv20Cycle = ["Rubi", "Diamante", "Lenda"];
            let patenteAuto;
            if (nivel <= 4)       patenteAuto = "Obsidiana";
            else if (nivel <= 8)  patenteAuto = "Ametista";
            else if (nivel <= 12) patenteAuto = "Topázio";
            else if (nivel <= 16) patenteAuto = "Esmeralda";
            else if (nivel <= 19) patenteAuto = "Âmbar";
            else patenteAuto = lv20Cycle.includes(p.Patente) ? p.Patente : "Rubi";
            const patClass = patenteAuto.toLowerCase()
              .replace("á","a").replace("â","a").replace("ã","a")
              .replace("é","e").replace("ô","o").replace("ç","c");
            const isLv20 = nivel >= 20;
            const tooltip = isLv20
              ? "Clique para alternar entre Rubi / Diamante / Lenda"
              : `Lv ${nivel} → ${patenteAuto}`;
            const isLenda = patenteAuto === "Lenda";
            // Lenda: shader Three.js (toon fire) cobre o retângulo TODO, atrás do texto.
            // Para outras patentes, ícone normal na coluna direita.
            const overlayHTML = isLenda
              ? `<div class="lenda-bonfire" data-toon-fire="1" aria-hidden="true"></div>`
              : "";
            const iconHTML = isLenda
              ? `<div class="icon"></div>`  // vazio — fogo já está atrás do texto
              : `<div class="icon">◈</div>`;
            return `<div class="f-patent patente-${patClass}${isLv20 ? ' clickable' : ''}"
                          data-patente-cycle="${isLv20 ? 1 : 0}"
                          title="${tooltip}">
              ${overlayHTML}
              <div class="name"><div>${patenteAuto}<small>PATENTE</small></div></div>
              ${iconHTML}
            </div>`;
          })()}
        </div>
        <div class="f-right">
          <div class="persona-slot clickable" data-pick="pers" data-tipo="traco"><span class="tag">Traços</span>${pers.traco || "<i>clique para editar</i>"}</div>
          <div class="persona-slot clickable" data-pick="pers" data-tipo="ideal"><span class="tag">Ideias</span>${pers.ideal || "<i>clique para editar</i>"}</div>
          <div class="persona-slot clickable" data-pick="pers" data-tipo="vinculo"><span class="tag">Vínculos</span>${pers.vinculo || "<i>clique para editar</i>"}</div>
          <div class="persona-slot clickable" data-pick="pers" data-tipo="defeito"><span class="tag">Defeitos</span>${pers.defeito || "<i>clique para editar</i>"}</div>
        </div>
      </div>`);

    // ===== Mini markdown renderer pra descrições de habs/traços =====
    // Suporta: **bold**, *italic*, `code`, listas com "- item", quebras \n\n.
    // Detecta HTML pre-renderizado (ex.: tabelas de progressão geradas no
    // seed/parser) — passa direto sem escape, preservando estrutura.
    function renderMarkdown(s) {
      if (!s) return "";
      // Se a descrição já tem HTML estrutural, assume pre-renderizado e retorna como está.
      // (Cobre tabelas de progressão, listas <ul>, parágrafos, etc.)
      if (/<(table|p|br|h[1-6]|ul|ol|li|div|span|em|strong|b)\b/i.test(s)) {
        return s;
      }
      // Escape HTML antes de aplicar markdown (segurança XSS pra texto livre)
      let out = String(s).replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[c]));
      // Bold antes de italic (** > *)
      out = out.replace(/\*\*([^*\n]+?)\*\*/g, "<b>$1</b>");
      out = out.replace(/(?<![*])\*([^*\n]+?)\*(?![*])/g, "<i>$1</i>");
      out = out.replace(/`([^`\n]+?)`/g, "<code>$1</code>");
      // Listas: linha com "- " no começo vira <li>
      const lines = out.split("\n");
      const blocks = [];
      let buf = [];
      let inList = false;
      const flush = () => {
        if (buf.length) blocks.push(buf.join("<br>"));
        buf = [];
      };
      for (const ln of lines) {
        const stripped = ln.trim();
        if (/^-\s+/.test(stripped)) {
          if (!inList) { flush(); blocks.push("<ul>"); inList = true; }
          blocks.push(`<li>${stripped.replace(/^-\s+/, "")}</li>`);
        } else {
          if (inList) { blocks.push("</ul>"); inList = false; }
          if (stripped === "") {
            flush();
          } else {
            buf.push(ln);
          }
        }
      }
      if (inList) blocks.push("</ul>");
      flush();
      return blocks.join("");
    }

    // ===== Helper: renderiza badges das tags (lado direito do nome) =====
    // Mapeamento prefixo → label curto + classe CSS
    const TAG_LABEL = {
      "pick":            { label: "+",       cls: "tag-pick"   },
      "prof":            { label: "Prof",    cls: "tag-prof"   },
      "prof-armadura":   { label: "Armad",   cls: "tag-prof"   },
      "prof-arma":       { label: "Arma",    cls: "tag-prof"   },
      "prof-ferramenta": { label: "Ferr",    cls: "tag-prof"   },
      "expertise":       { label: "Exp",     cls: "tag-exp"    },
      "save-prof":       { label: "Save",    cls: "tag-save"   },
      "resist":          { label: "Resist",  cls: "tag-resist" },
      "immune":          { label: "Imune",   cls: "tag-immune" },
      "vuln":            { label: "Vuln",    cls: "tag-vuln"   },
      "cond-immune":     { label: "ImCond",  cls: "tag-immune" },
      "adv-cond":        { label: "AdvCond", cls: "tag-save"   },
      "andar":           { label: "Andar",   cls: "tag-move"   },
      "voar":            { label: "Voar",    cls: "tag-move"   },
      "nadar":           { label: "Nadar",   cls: "tag-move"   },
      "cavar":           { label: "Cavar",   cls: "tag-move"   },
    };
    // Tags categoriais (standalone, sem ":") — chave = literal da tag
    const TAG_LABEL_STANDALONE = {
      "conjurador":   { label: "Conjurador", cls: "tag-conjurador" },
    };
    const ATR_ABBR = { Forca: "For", Destreza: "Des", Constituicao: "Con",
                       Inteligencia: "Int", Sabedoria: "Sab", Carisma: "Car" };
    // ===== HELPER ÚNICO: renderiza slots de picker a partir de TagsJSON =====
    // Qualquer card (traço, hab, sintético) que tenha pick:<tipo>:N ganha automaticamente
    // os N slots interativos. Universal: aceita qualquer tipo (estilo-de-luta, maestria-arma,
    // talento-geral, etc.) — não só perícia/idioma/ferramenta.
    //
    // Args:
    //   tagsJSON      — string JSON com lista de tags (string OU objeto {tag, n_por_nivel, filter})
    //   origem        — string usada como Origem em TB_PersonagemEscolha*
    //   filterList    — array opcional de nomes permitidos (whitelist via filter prop ou param)
    //   nivelEfetivo  — nível pra resolver n_por_nivel (NivelClasse de hab/classe; default p.Nivel)
    //   skipKinds     — array opcional de tipos a NÃO renderizar inline (têm slot dedicado em
    //                   outro lugar). Ex: traços com pick:talento-origem usam slot dedicado
    //                   "Talento de Origem (via X)" — não duplicar inline no card.
    //
    // Retorna HTML (string) ou "" se não houver tags pick.
    function renderPickSlotsFromTags(tagsJSON, origem, filterList, nivelEfetivo, skipKinds) {
      let tags;
      try { tags = JSON.parse(tagsJSON || "[]") || []; } catch { return ""; }
      if (!Array.isArray(tags) || !tags.length) return "";
      const nivel = nivelEfetivo || state.personagem?.Nivel || 1;

      // Resolve {nivel: N} pegando o maior nível ≤ nivelEfetivo.
      const resolveN = (progressao) => {
        let bestN = null, bestK = -1;
        for (const [k, v] of Object.entries(progressao || {})) {
          const ki = parseInt(k, 10), vi = parseInt(v, 10);
          if (isNaN(ki) || isNaN(vi)) continue;
          if (ki <= nivel && ki > bestK) { bestK = ki; bestN = vi; }
        }
        return bestN;
      };

      // Normaliza qualquer forma (string flat, string c/ filter, objeto) em {kind, n, filter, locked, minNivel, maxlen, descricoes}.
      const picks = [];
      for (const raw of tags) {
        let kind = null, n = 0, filter = null, locked = false, minNivel = null, maxlen = null, descricoes = null;
        if (typeof raw === "string") {
          // "pick:<tipo>:<N>" ou "pick:<tipo>:<N>=A|B|C"
          const m = raw.match(/^pick:([a-z][a-z0-9-]*):(\d+)(?:=(.+))?$/);
          if (!m) continue;
          kind = m[1]; n = parseInt(m[2], 10);
          if (m[3]) filter = m[3].split("|").map(s => s.trim()).filter(Boolean);
        } else if (raw && typeof raw === "object" && typeof raw.tag === "string") {
          // {tag: "pick:<tipo>" [: <N>], n_por_nivel?, filter?, min_nivel?, maxlen?, descricoes?, tipo?}
          const m = raw.tag.match(/^pick:([a-z][a-z0-9-]*)(?::(\d+))?$/);
          if (!m) continue;
          kind = m[1];
          if (raw.n_por_nivel && typeof raw.n_por_nivel === "object") {
            const r = resolveN(raw.n_por_nivel);
            if (r == null || r <= 0) continue;  // char abaixo do mínimo da progressão
            n = r;
          } else if (m[2]) {
            n = parseInt(m[2], 10);
          } else continue;
          if (Array.isArray(raw.filter) && raw.filter.length) filter = raw.filter.slice();
          // Gate min_nivel: slot fica visível mas locked até atingir o nível.
          if (typeof raw.min_nivel === "number" && nivel < raw.min_nivel) {
            locked = true;
            minNivel = raw.min_nivel;
          }
          // maxlen: limite de caracteres pra kind 'texto' (escolha livre com sugestões).
          if (typeof raw.maxlen === "number" && raw.maxlen > 0) maxlen = raw.maxlen;
          // descricoes: lookup {opcao: texto} mostrado no picker pra cada opção do filter.
          if (raw.descricoes && typeof raw.descricoes === "object") descricoes = raw.descricoes;
        } else continue;
        if (n <= 0) continue;
        picks.push({ kind, n, filter, locked, minNivel, maxlen, descricoes });
      }
      if (!picks.length) return "";

      // skipKinds: tipos com tratamento dedicado (ex: 'talento-origem' tem slot
      // próprio em renderOrigemSlot). Não renderiza inline pra evitar duplicata.
      const skipSet = Array.isArray(skipKinds) && skipKinds.length
        ? new Set(skipKinds) : null;

      // filterList vinda do call site sobrescreve filter da tag (ex: SkillsJSON.from da classe).
      // SlotIndex é GLOBAL por (origem, kind) — múltiplas tag-picks do mesmo kind
      // na mesma origem (ex: 2× pick:pericia:1 em "Instinto de Caçador") continuam
      // a numeração em vez de resetar, evitando colisão de SlotIndex no DB.
      const blocks = [];
      const slotCounter = new Map();  // key=kind, val=próximo slot global
      for (const { kind, n, filter, locked, minNivel, maxlen, descricoes } of picks) {
        if (skipSet && skipSet.has(kind)) continue;
        const flt = (filterList && filterList.length) ? filterList : (filter || null);
        const filterAttr = flt
          ? ` data-filter-list="${escapeHtmlBare(flt.join("|"))}"`
          : "";
        const maxlenAttr = maxlen ? ` data-maxlen="${maxlen}"` : "";
        // descricoesAttr: encoda lookup {opcao: texto} no slot dataset pra que o
        // picker handler mostre o texto sob cada opção (ex: cada Lua + suas magias).
        const descricoesAttr = descricoes
          ? ` data-pick-descricoes="${escapeHtmlBare(JSON.stringify(descricoes))}"`
          : "";
        // labelKind: nome legível no slot.
        const labelKind = ({
          pericia: "perícia", expertise: "expertise",
          idioma: "idioma", ferramenta: "ferramenta",
        })[kind] || kind;

        // Leitura do estado: pericia/expertise/idioma/ferramenta usam tabelas dedicadas; outros usam TB_PersonagemEscolhaTag.
        // pick:pericia e pick:expertise ambos usam TB_PersonagemEscolhaPericia,
        // distinguidos por Tipo ('proficiencia' vs 'expertise').
        const bySlot = {};
        if (kind === "pericia" || kind === "expertise") {
          const tipoEsperado = kind === "expertise" ? "expertise" : "proficiencia";
          (state.escolhas_pericia || [])
            .filter(e => e.Origem === origem && ((e.Tipo || "proficiencia") === tipoEsperado))
            .forEach(e => bySlot[e.SlotIndex] = { name: e.NomePericia });
        } else if (kind === "idioma" || kind === "ferramenta") {
          (state.escolhas_idioma || [])
            .filter(e => e.Origem === origem && e.Tipo === kind)
            .forEach(e => bySlot[e.SlotIndex] = { name: e.Nome });
        } else {
          (state.escolhas_tag || [])
            .filter(e => e.Origem === origem && e.Tipo === kind)
            .forEach(e => bySlot[e.SlotIndex] = { name: e.Valor });
        }

        const slots = [];
        const startSi = slotCounter.get(kind) || 0;
        for (let i = 0; i < n; i++) {
          const si = startSi + i;  // global por (origem, kind)
          // Slots locked: data-locked=1 + classe locked. Click handler ignora ou abre "planejar".
          const lockedAttr = locked ? ' data-locked="1"' : '';
          const dataAttrs = `data-pick-slot data-kind="${kind}" data-origem="${escapeHtmlBare(origem)}" data-slot="${si}"${filterAttr}${maxlenAttr}${descricoesAttr}${lockedAttr}`;
          const e = bySlot[si];
          if (e && !locked) {
            slots.push(`<div class="tier-slot filled" ${dataAttrs}>
              <span>${escapeHtmlBare(e.name || '?')}</span>
              <span class="hab-pin tier-x" data-pick-slot-remove data-kind="${kind}"
                data-origem="${escapeHtmlBare(origem)}" data-slot="${si}" title="Remover">×</span>
            </div>`);
          } else if (locked) {
            slots.push(`<div class="tier-slot empty locked" ${dataAttrs} title="Disponível no Nv ${minNivel}">
              <i>🔒 ${labelKind} ${si+1} — Nv ${minNivel}+</i>
            </div>`);
          } else {
            slots.push(`<div class="tier-slot empty" ${dataAttrs}>
              <i>${labelKind} ${si+1} — clique para escolher</i>
            </div>`);
          }
        }
        slotCounter.set(kind, startSi + n);
        blocks.push(`<div class="hab-pick-row">${slots.join("")}</div>`);
      }
      return blocks.join("");
    }

    // Resolve {nivel: N} pegando o maior nível ≤ nivelEfetivo. Espelha o backend.
    const _resolveNporNivel = (progressao, nivelEfetivo) => {
      let bestN = null, bestK = -1;
      for (const [k, v] of Object.entries(progressao || {})) {
        const ki = parseInt(k, 10), vi = parseInt(v, 10);
        if (isNaN(ki) || isNaN(vi)) continue;
        if (ki <= nivelEfetivo && ki > bestK) { bestK = ki; bestN = vi; }
      }
      return bestN;
    };

    // Converte tag-objeto para forma string equivalente — espelha o agregador.
    // Quando nivelEfetivo é dado, resolve n_por_nivel; senão mostra `:nv(...)`.
    const tagToCanonicalString = (tag, nivelEfetivo) => {
      if (typeof tag === "string") return tag;
      if (tag && typeof tag.tag === "string") {
        let s = tag.tag;
        if (tag.n_por_nivel && typeof tag.n_por_nivel === "object") {
          if (nivelEfetivo != null) {
            const n = _resolveNporNivel(tag.n_por_nivel, nivelEfetivo);
            if (n == null) return "";  // char abaixo do mínimo
            s = `${s}:${n}`;
          } else {
            const pares = Object.entries(tag.n_por_nivel)
              .map(([k, v]) => `${k}=${v}`)
              .sort((a, b) => parseInt(a) - parseInt(b))
              .join(",");
            if (pares) s = `${s}:nv(${pares})`;
          }
        }
        if (Array.isArray(tag.filter) && tag.filter.length) {
          s = `${s}=${tag.filter.join("|")}`;
        }
        return s;
      }
      return "";
    };

    const renderTagBadges = (tagsJSON, nivelEfetivo) => {
      let tags = [];
      try { tags = JSON.parse(tagsJSON || "[]") || []; } catch { return ""; }
      if (!Array.isArray(tags) || !tags.length) return "";
      const nivelCheck = nivelEfetivo ?? state.nivel_total ?? state.personagem?.Nivel ?? 1;
      return tags.map(rawTag => {
        // Tag-objeto com min_nivel: badge fica visualmente locked se nivel < min_nivel.
        // O conteúdo (+1 perícia, etc) continua dentro do badge — só o estilo muda.
        const isLocked = rawTag && typeof rawTag === "object"
          && typeof rawTag.min_nivel === "number"
          && nivelCheck < rawTag.min_nivel;
        const lockSuffix = isLocked
          ? ` <small style="opacity:.85">(Nv ${rawTag.min_nivel}+)</small>`
          : "";
        const lockClass = isLocked ? " tag-locked" : "";
        const lockIcon = isLocked ? "🔒 " : "";

        // Normaliza tag-objeto pra string (regra de tags universais §4.0)
        const tag = tagToCanonicalString(rawTag, nivelEfetivo);
        if (!tag) return "";
        // Tag acumuladora "+chave:N" — exibe "+N chave" (princípio: cada fonte soma).
        if (tag.startsWith("+")) {
          const body = tag.slice(1);
          const ci = body.indexOf(":");
          if (ci > 0) {
            const chave = body.slice(0, ci);
            const n = body.slice(ci + 1).split("=")[0];
            return `<span class="tag-badge tag-bonus${lockClass}" title="${escapeHtmlBare(tag)}${isLocked ? ' (locked Nv ' + rawTag.min_nivel + '+)' : ''}">${lockIcon}+${escapeHtmlBare(n)} ${escapeHtmlBare(chave)}${lockSuffix}</span>`;
          }
        }
        const colon = tag.indexOf(":");
        if (colon < 0) {
          const stand = TAG_LABEL_STANDALONE[tag];
          return stand
            ? `<span class="tag-badge ${stand.cls}${lockClass}" title="${escapeHtmlBare(tag)}">${lockIcon}${stand.label}${lockSuffix}</span>`
            : `<span class="tag-badge${lockClass}">${lockIcon}${escapeHtmlBare(tag)}${lockSuffix}</span>`;
        }
        const prefix = tag.slice(0, colon);
        const valor = tag.slice(colon + 1);
        const meta = TAG_LABEL[prefix];
        if (!meta) return `<span class="tag-badge${lockClass}">${lockIcon}${escapeHtmlBare(tag)}${lockSuffix}</span>`;
        // pick:pericia:N → "+2 perícias", pick:expertise:N → "+2 expertise", etc.
        if (prefix === "pick") {
          const parts = valor.split(":");
          const kind = parts[0]; const n = parts[1] || "?";
          return `<span class="tag-badge ${meta.cls}${lockClass}" title="${escapeHtmlBare(tag)}${isLocked ? ' (locked Nv ' + rawTag.min_nivel + '+)' : ''}">${lockIcon}+${n} ${escapeHtmlBare(kind)}${lockSuffix}</span>`;
        }
        // save-prof:Inteligencia → "Save: Int"
        const v = (prefix === "save-prof") ? (ATR_ABBR[valor] || valor) : valor;
        return `<span class="tag-badge ${meta.cls}${lockClass}" title="${escapeHtmlBare(tag)}">${lockIcon}${meta.label}: ${escapeHtmlBare(v)}${lockSuffix}</span>`;
      }).join("");
    };

    // ===== Features de classe (preto) + subclasse (cor do brand) + traços raciais =====
    const fmtHab = (h, origem) => {
      // Gate condicional: tag 'gate:<X>' faz a hab aparecer só se '<X>' está ativa
      // em aggregated_tags. Convenção universal — útil pra opções de pick que
      // ativam features específicas (ex: Manifestação Mística do Místico Nv 1).
      try {
        const habTags = JSON.parse(h.TagsJSON || "[]") || [];
        const gates = (Array.isArray(habTags) ? habTags : [])
          .map(t => typeof t === "string" && t.startsWith("gate:") ? t.slice(5) : null)
          .filter(Boolean);
        if (gates.length) {
          const ativas = new Set((state.aggregated_tags || []).map(t => t.tag));
          if (!gates.some(g => ativas.has(g))) return ""; // todas ausentes → esconde
        }
      } catch {}
      const hasChoice = !!h.TemEscolha;
      const nivelOK = (p.Nivel || 1) >= (h.NivelAdquirido || 1);
      const isArquetipo = /Arqu[ée]tipo/i.test(h.Nome);
      const isLista = /manobra/i.test(h.Nome);
      const vinculadas = (state.tecnicas || []).filter(t => t.Id_Habilidade === h.Id_Habilidade);
      const escolhido = isArquetipo
        ? (state.subclasse?.Nome || "")
        : isLista
          ? (vinculadas.length ? vinculadas.map(t => t.Nome).join(", ") : "")
          : "";

      // pin pequeno à direita do título — só pra arquétipo (precisa de subclasse)
      let pin = "";
      if (isArquetipo) {
        if (!nivelOK) pin = `<span class="hab-pin locked" title="Adquire no Nv ${h.NivelAdquirido}">🔒</span>`;
        else pin = `<span class="hab-pin ${escolhido ? "ok" : "todo"}">${escolhido ? "✓" : "⚙"}</span>`;
      }

      const kind = isArquetipo ? "arquetipo" : "default";
      const clickable = (isArquetipo || (hasChoice && !isLista)) && nivelOK;

      // Slots de picker driven-by-tag — qualquer hab com pick:<tipo>:N (incluindo
      // estilo-de-luta, talento-geral, pericia-cortesao, etc.) ganha slots automaticamente.
      // NivelClasse vem do SELECT de habs_cls/sub — usado pra resolver n_por_nivel.
      // tags_de_opcoes_por_origem é overlay RUNTIME (não persiste no DB) — tags vindas
      // das opções escolhidas POR ESTE PLAYER. Frontend combina aqui pra render apenas.
      let tagsBase = [];
      try { tagsBase = JSON.parse(h.TagsJSON || "[]") || []; } catch {}
      const tagsOverlay = (state.tags_de_opcoes_por_origem || {})[h.Nome] || [];
      const tagsCombinadas = tagsBase.concat(tagsOverlay);
      const tagsCombinadasJSON = JSON.stringify(tagsCombinadas);
      const habPickBlocks = renderPickSlotsFromTags(tagsCombinadasJSON, h.Nome, undefined, h.NivelClasse, ['talento-origem', 'maestria-arma', 'tecnica-furtividade', 'metamagia', 'estilo-danca', 'infusao-artificer']);
      const habTagBadges = renderTagBadges(tagsCombinadasJSON, h.NivelClasse);

      return `<div class="feat-card feat-${origem} ${clickable ? "clickable" : ""} ${!nivelOK ? "hab-locked" : ""}"
                   data-hab-id="${h.Id_Habilidade||""}"
                   data-has-choice="${clickable ? 1 : 0}"
                   data-kind="${kind}">
        <div class="feat-card-head">
          <span class="feat-nome">${h.Nome}</span>
          ${habTagBadges}
          <span class="feat-nivel">Nv ${h.NivelAdquirido || 1}</span>
          ${pin}
        </div>
        ${escolhido ? `<div class="feat-card-choice">→ <em>${escolhido}</em></div>` : ""}
        ${habPickBlocks}
        <div class="feat-card-desc">${renderMarkdown(h.Descricao || "")}</div>
      </div>`;
    };

    // pequeno helper para escapar texto vindo do catálogo
    function escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, c => ({
        "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
      }[c]));
    }
    // features com "Manobras de Combate..." são roteadas para a seção Técnicas
    // e omitidas das colunas de classe/subclasse (evita duplicação).
    // Features marcadas com a tag 'asi-feature' (Incremento/Aprimoramento de
    // Atributo ou Talento, Aumento de Atributo, Talento Épico, etc.) são
    // ocultadas dos blocos — já são representadas pelos tier-slots de Talentos.
    const isManobraFeature = (h) => /^Manobras de Combate/i.test(h.Nome);
    const hasTag = (h, tag) => {
      try {
        const t = h.TagsJSON ? JSON.parse(h.TagsJSON) : [];
        return Array.isArray(t) && t.some(x =>
          x === tag || (typeof x === "object" && x && x.tag === tag));
      } catch { return false; }
    };
    const isASIFeature = (h) => hasTag(h, "asi-feature");
    // Tag genérica 'oculta-hab': esconde a feature dos blocos de classe/subclasse
    // (ex.: catálogo de Infusões do Artífice, que agora vive no picker dedicado).
    const isOcultaFeature = (h) => hasTag(h, "oculta-hab");
    // Habs separadas por classe (ordem igual a state.classes)
    const habFiltrar = (h) => !isManobraFeature(h) && !isASIFeature(h) && !isOcultaFeature(h);
    const allHabsCls = (state.habilidades_classe || []).filter(habFiltrar);
    const allHabsSub = (state.habilidades_subclasse || []).filter(habFiltrar);
    // Bloco "Proficiências de Classe" — card Nv 0 (renderizado igual a uma habilidade).
    // Multiclasse: mostra MulticlassProfJSON em vez de armor/weapon/tool da primeira classe.
    const renderProfCard = (c, isPrimeira) => {
      const parseList = (raw) => { try { return JSON.parse(raw || "[]") || []; } catch { return []; } };
      const saves = parseList(c.SavesJSON);
      const armorBase = parseList(c.ArmorProfJSON);
      const weaponsBase = parseList(c.WeaponProfJSON);
      const tools = parseList(c.ToolProfJSON);
      const mcprof = parseList(c.MulticlassProfJSON);
      const skillsSpec = (() => { try { return JSON.parse(c.SkillsJSON || "null"); } catch { return null; } })();

      // Proficiências extras vindas de tags (prof-armadura:* / prof-arma:*).
      // Mescla com base sem duplicar (case-insensitive).
      const extrasArm = (state.profs_armadura_extras || []).map(x => x.valor);
      const extrasArma = (state.profs_arma_extras || []).map(x => x.valor);
      const mergeUnique = (base, extras) => {
        const seen = new Set(base.map(s => s.toLowerCase()));
        const out = base.slice();
        for (const e of extras) {
          if (!seen.has(e.toLowerCase())) { out.push(e); seen.add(e.toLowerCase()); }
        }
        return out;
      };
      const armor = mergeUnique(armorBase, extrasArm);
      const weapons = mergeUnique(weaponsBase, extrasArma);

      const linhas = [];
      if (isPrimeira) {
        if (saves.length) linhas.push(`<li><b>Resistências:</b> ${saves.map(escapeHtmlBare).join(", ")}</li>`);
        if (skillsSpec?.from?.length) {
          linhas.push(`<li><b>Perícias:</b> escolha ${skillsSpec.choose} dentre ${skillsSpec.from.map(escapeHtmlBare).join(", ")}</li>`);
        }
        if (armor.length) linhas.push(`<li><b>Armaduras:</b> ${armor.map(escapeHtmlBare).join(", ")}</li>`);
        if (weapons.length) linhas.push(`<li><b>Armas:</b> ${weapons.map(escapeHtmlBare).join(", ")}</li>`);
        if (tools.length) linhas.push(`<li><b>Ferramentas:</b> ${tools.map(escapeHtmlBare).join(", ")}</li>`);
      } else if (mcprof.length) {
        linhas.push(`<li><b>Proficiências (Multiclasse):</b> ${mcprof.map(escapeHtmlBare).join(", ")}</li>`);
      }
      if (!linhas.length) return "";
      // Tags sintéticas — derivadas das colunas SavesJSON/ArmorProfJSON/WeaponProfJSON/
      // ToolProfJSON/SkillsJSON da TB_Classe. Cada coluna vira badge correspondente:
      //   SavesJSON ["Forca","Constituicao"] → save-prof:Forca, save-prof:Constituicao
      //   ArmorProfJSON ["Leve","Média"]      → prof-armadura:Leve, prof-armadura:Média
      //   WeaponProfJSON ["Simples"]          → prof-arma:Simples
      //   ToolProfJSON ["Kit do Curandeiro"]  → prof-ferramenta:Kit do Curandeiro
      //   SkillsJSON.choose=N                 → pick:pericia:N (com filter SkillsJSON.from)
      // Já existia só pick:pericia. Expandido pra cobrir tudo. Espelha a regra
      // "todo bloco mostra suas tags em cima". Backend agregará effetos quando
      // a TagsJSON da própria TB_Classe estiver populada — aqui é só exibição.
      const synthTags = [];
      if (isPrimeira) {
        for (const s of saves) synthTags.push(`save-prof:${s}`);
        if (skillsSpec?.choose > 0) synthTags.push(`pick:pericia:${skillsSpec.choose}`);
        for (const a of armorBase) synthTags.push(`prof-armadura:${a}`);
        for (const w of weaponsBase) synthTags.push(`prof-arma:${w}`);
        for (const t of tools) synthTags.push(`prof-ferramenta:${t}`);
        // Tags ad-hoc da TB_Classe.TagsJSON — entram no card de Proficiências
        // (ex: Monge pick:ferramenta:1 = "Escolha 1 ferramenta de artesão").
        try {
          const extraTags = JSON.parse(c.ClasseTagsJSON || "[]") || [];
          if (Array.isArray(extraTags)) synthTags.push(...extraTags);
        } catch {}
      }
      const synthTagsJSON = JSON.stringify(synthTags);
      const badges    = renderTagBadges(synthTagsJSON);
      const pickRow   = renderPickSlotsFromTags(synthTagsJSON, c.NomeClasse, skillsSpec?.from, c.Nivel, ['talento-origem', 'maestria-arma', 'tecnica-furtividade', 'metamagia', 'estilo-danca', 'infusao-artificer']);

      return `<div class="feat-card feat-classe">
        <div class="feat-card-head">
          <span class="feat-nome">Proficiências de Classe</span>
          ${badges}
          <span class="feat-nivel">Nv 0</span>
        </div>
        <div class="feat-card-desc"><ul style="margin:4px 0 0 18px;padding:0">${linhas.join("")}</ul></div>
        ${pickRow}
      </div>`;
    };

    // Bloco "Equipamento Inicial" — card Nv 0 separado.
    // Só aparece na primeira classe (multiclasse não dá equipamento inicial).
    const renderEquipCard = (c, isPrimeira) => {
      if (!isPrimeira) return "";
      let equip = [];
      try { equip = JSON.parse(c.EquipamentoInicialJSON || "[]") || []; } catch { equip = []; }
      if (!equip.length) return "";
      const itens = equip.map(e => {
        const qtd = e.qtd > 1 ? `<b>${e.qtd}×</b> ` : "";
        const valor = e.valor ? ` <small style="color:#888">(${escapeHtmlBare(e.valor)})</small>` : "";
        return `<li>${qtd}${escapeHtmlBare(e.nome)}${valor}</li>`;
      }).join("");
      return `<div class="feat-card feat-classe">
        <div class="feat-card-head">
          <span class="feat-nome">Equipamento Inicial</span>
          <span class="feat-nivel">Nv 0</span>
        </div>
        <div class="feat-card-desc">
          <small style="color:#aaa">Itens iniciais da classe (PHB 2024 — naming do Bonfire Tales).</small>
          <ul style="margin:6px 0 0 18px;padding:0">${itens}</ul>
        </div>
      </div>`;
    };

    const renderHabsClasse = (state.classes || []).map((c, i) => {
      const habs = allHabsCls.filter(h => h.Id_Classe === c.Id_Classe);
      const isPrimeira = (c.Ordem ?? i) === 0;
      const titulo = `Classe ${i+1} · ${c.NomeClasse} ${c.Nivel}${isPrimeira ? " (primária)" : ""}`;
      const profCard  = renderProfCard(c, isPrimeira);
      const equipCard = renderEquipCard(c, isPrimeira);
      const inner = habs.length
        ? habs.map(h => fmtHab(h, "classe")).join("")
        : `<div class="feat-item" style="color:#bbb">— sem características cadastradas</div>`;
      // Tags da TB_Classe e TB_Subclasse linha-mãe — cada bloco mostra suas tags em cima.
      const classeTags = renderTagBadges(c.ClasseTagsJSON);
      const subTags = c.NomeSubclasse ? renderTagBadges(c.SubclasseTagsJSON) : "";
      const subHeader = c.NomeSubclasse
        ? `<div class="feat-head" style="font-size:11px;opacity:.85">Subclasse · ${escapeHtmlBare(c.NomeSubclasse)} ${subTags}</div>`
        : "";
      return `<div class="feat-head">${escapeHtmlBare(titulo)} ${classeTags}</div>${profCard}${equipCard}${subHeader}${inner}`;
    }).join("");
    // Tabela "Magias de Domínio/Juramento" — agrupa magias_subclasse por tier_unlock
    // Estilo igual à progression-table que o Guerreiro/Cavaleiro Arcano usa.
    const renderTabelaMagiasDominio = (subNome, classeNomeRotulo) => {
      const mags = (state.magias_subclasse || []).filter(m => m.__via_origem === subNome);
      if (!mags.length) return "";
      // Agrupa por tier_unlock (tier de classe quando a magia foi liberada)
      const byTier = {};
      mags.forEach(m => {
        const tier = m.tier_unlock || parseInt(m.fonte_lista, 10);  // fallback
        (byTier[tier] = byTier[tier] || []).push(m);
      });
      const tiers = Object.keys(byTier).map(Number).sort((a,b) => a-b);
      const rows = tiers.map(tier => {
        const spells = byTier[tier].map(m =>
          `${escapeHtmlBare(m.nome)}${m.nome_ingles ? ` <small style="color:#888">(${escapeHtmlBare(m.nome_ingles)})</small>` : ""}`
        ).join(", ");
        return `<tr><td>${tier}º</td><td>${spells}</td></tr>`;
      }).join("");
      return `<table class="progression-table magias-dominio-table">
        <thead><tr><th>Nível de ${escapeHtmlBare(classeNomeRotulo)}</th><th>Magias</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    };

    const renderHabsSubclasse = (state.classes || []).map((c, i) => {
      // habs da subclasse específica desta classe
      const habs = c.Id_Subclasse
        ? allHabsSub.filter(h => h.Id_Subclasse === c.Id_Subclasse)
        : [];
      const subNome = c.NomeSubclasse || "— sem subclasse";
      const titulo = `Subclasse ${i+1} · ${subNome}`;

      // Card sintético da subclasse: aparece SEMPRE que c.Id_Subclasse existe,
      // mesmo sem habs cadastradas. Padrão "blocos universais" — todo bloco visível.
      // Nome + tags da TB_Subclasse + descrição/tagline.
      let cardSub = "";
      if (c.Id_Subclasse) {
        const subTagBadges = renderTagBadges(c.SubclasseTagsJSON);
        const tagline = c.SubclasseTagline || "";
        cardSub = `<div class="feat-card feat-classe">
          <div class="feat-card-head">
            <span class="feat-nome">${escapeHtml(subNome)}</span>
            ${subTagBadges}
            <span class="feat-nivel">Nv ${c.Nivel}</span>
          </div>
          ${tagline ? `<div class="feat-card-desc"><small>${escapeHtmlBare(tagline)}</small></div>` : ""}
        </div>`;
      }

      const inner = habs.length
        ? habs.map(h => fmtHab(h, "subclasse")).join("")
        : (c.Id_Subclasse
            ? `<div class="feat-item" style="color:#bbb">— habilidades de subclasse Nv 3+ não populadas no catálogo ainda</div>`
            : `<div class="feat-item" style="color:#bbb">— escolha uma subclasse</div>`);
      const tabelaDominio = c.Id_Subclasse
        ? renderTabelaMagiasDominio(c.NomeSubclasse, c.NomeClasse || "Classe")
        : "";
      return `<div class="feat-head">${escapeHtmlBare(titulo)}</div>${cardSub}${inner}${tabelaDominio}`;
    }).join("");
    // fallback se zero classes
    const habCls = renderHabsClasse || `<div class="feat-item" style="color:#bbb">—</div>`;
    const habSub = renderHabsSubclasse || `<div class="feat-item" style="color:#bbb">—</div>`;
    // tracos raciais: feat-card style. Separa em 4 grupos para hierarquia visual:
    //   1) Raça base: Id_Raca set, sem Id_Linhagem, sem Id_Essencia
    //   2) Linhagem racial: Id_Linhagem set
    //   3) Essência base: Id_Essencia set, sem Id_EssLinhagem
    //   4) Sub-linhagem da essência: Id_EssLinhagem set
    const allTracos = state.tracos || [];
    const tracosRacaBase = allTracos.filter(t => t.Id_Raca && !t.Id_Linhagem && !t.Id_Essencia);
    const tracosRacaLin  = allTracos.filter(t => t.Id_Linhagem);
    const tracosEssBase  = allTracos.filter(t => t.Id_Essencia && !t.Id_EssLinhagem && !t.Id_Raca);
    const tracosEssSub   = allTracos.filter(t => t.Id_EssLinhagem);

    const fmtTraco = (t) => {
      // pick:* slots vêm direto da tag — qualquer traço com pick:pericia:N etc ganha auto.
      // Skip pick:talento-origem — esse tem slot dedicado em "Talento de Origem (via X)".
      const pickerBlocks = renderPickSlotsFromTags(
        t.TagsJSON, t.Nome, undefined, undefined, ['talento-origem', 'maestria-arma', 'tecnica-furtividade', 'metamagia', 'estilo-danca', 'infusao-artificer'],
      );
      return `<div class="feat-card feat-raca">
        <div class="feat-card-head">
          <span class="feat-nome">${escapeHtml(t.Nome)}</span>
          ${renderTagBadges(t.TagsJSON)}
        </div>
        <div class="feat-card-desc">${renderMarkdown(t.Descricao || "")}</div>
        ${pickerBlocks}
      </div>`;
    };

    // Card sintético do legado da sub-linhagem da essência. Post-R4: dados
    // derivados de tags em TB_EssenciaLinhagem.TagsJSON (resist:*, truque-inato:*,
    // magia-1uso:*) via state.auto_efeitos no payload.
    let cardLegado = "";
    if (state.ess_linhagem && state.auto_efeitos) {
      const ae = state.auto_efeitos;
      const partes = [];
      if (ae.resistencia) partes.push(`<li><b>Resistência:</b> ${escapeHtml(ae.resistencia)}</li>`);
      if (ae.truque) partes.push(`<li><b>Truque inato:</b> ${escapeHtml(ae.truque)}</li>`);
      if (ae.magia_n3) {
        partes.push(`<li><b>Magia nv 1 (1×/descanso longo, desbloqueia Nv 3+):</b> ${escapeHtml(ae.magia_n3)}</li>`);
      }
      if (partes.length) {
        // Tags sintéticas — Legado dos Círculos é card derivado.
        const synth = [];
        if (ae.resistencia) synth.push(`resist:${ae.resistencia}`);
        if (ae.truque) synth.push(`truque-inato:${ae.truque}`);
        if (ae.magia_n3) synth.push(`magia-1uso:${ae.magia_n3}`);
        cardLegado = `<div class="feat-card feat-raca">
          <div class="feat-card-head">
            <span class="feat-nome">Legado dos Círculos — ${escapeHtml(state.ess_linhagem.Nome)}</span>
            ${renderTagBadges(JSON.stringify(synth))}
          </div>
          <div class="feat-card-desc"><ul style="margin:6px 0 0 18px;padding:0">${partes.join("")}</ul></div>
        </div>`;
      }
    }

    // Slot do Talento de Origem principal + extra (Raízes Profundas) + racial (traço com pick:talento-origem:1).
    // Renderiza como feat-card. Picker filtra Marcas mutuamente — só 1 Marca permitida no total.
    const renderOrigemSlot = (to, kind /* 'principal' | 'extra' | 'racial' */, label) => {
      if (to) {
        // pick:* slots vêm direto da TagsJSON do talento — mesma lógica de fmtTraco/tierSlot.
        // Permite talentos como "Iniciado no Juramento das Três Luas" (pick:texto:1=A|B|C)
        // spawnarem slot inline. Skip 'talento-origem' (slot dedicado abaixo).
        const pickerBlocks = renderPickSlotsFromTags(
          to.TagsJSON, to.Nome, undefined, undefined, ['talento-origem', 'maestria-arma', 'tecnica-furtividade', 'metamagia', 'estilo-danca', 'infusao-artificer'],
        );
        return `<div class="feat-card feat-raca clickable" data-pick-talento-origem-slot data-kind="${kind}" data-id-opcao="${to.Id_Opcao}" title="Click para trocar/remover">
          <div class="feat-card-head">
            <span class="feat-nome">${escapeHtml(to.Nome)}</span>
            ${renderTagBadges(to.TagsJSON)}
            <span class="hab-pin ok">✓</span>
          </div>
          <div class="feat-card-desc">${renderMarkdown(to.Descricao || "")}</div>
          ${pickerBlocks}
        </div>`;
      }
      return `<div class="tier-slot empty" data-pick-talento-origem-slot data-kind="${kind}">
        <i>${escapeHtml(label)} — clique para escolher</i>
      </div>`;
    };

    let blocoTalentoOrigem = renderOrigemSlot(state.talento_origem, "principal", "Talento de Origem");

    // Slot extra: render se aggregated_tags contém pick:talento-origem:1 de
    // QUALQUER origem que NÃO seja traço racial (esses têm slot dedicado abaixo)
    // e NÃO seja o talento de origem principal (BG, já tem slot). Regra do
    // user: tag presente → campo aparece. Sem regex em nome.
    const tracoOrigemNomes = new Set((state.tracos || []).filter(t => {
      try {
        const tt = JSON.parse(t.TagsJSON || "[]");
        return Array.isArray(tt) && tt.some(x => typeof x === "string" && /^pick:talento-origem:\d+$/.test(x));
      } catch { return false; }
    }).map(t => t.Nome));
    const principalNome = state.talento_origem?.Nome || null;
    const temRaizes = (state.aggregated_tags || []).some(t => {
      if (typeof t !== "object" || t.tag !== "pick:talento-origem:1") return false;
      const origem = t.origem || "";
      if (principalNome && origem === principalNome) return false;
      if (tracoOrigemNomes.has(origem)) return false;
      // origem composta "X · Y" (escolhas_tag promovida) — verifica o último nó
      const tail = origem.includes(" · ") ? origem.split(" · ").pop() : origem;
      if (tracoOrigemNomes.has(tail)) return false;
      return true;
    });
    if (temRaizes) {
      blocoTalentoOrigem += `<div class="traco-secao-label" style="font-size:10px">+ Talento de Origem Extra (via Raízes Profundas)</div>`;
      blocoTalentoOrigem += renderOrigemSlot(state.talento_origem_extra, "extra", "Talento de Origem Extra");
    }

    // Slot racial: aparece se algum traço da raça/linhagem/essência tem pick:talento-origem:1
    // (ex.: Erthari "Determinação Comum"). Separado de Raízes Profundas.
    const tracoOrigem = (state.tracos || []).find(t => {
      try {
        const tags = JSON.parse(t.TagsJSON || "[]");
        return Array.isArray(tags) && tags.some(x => /^pick:talento-origem:\d+$/.test(x));
      } catch { return false; }
    });
    if (tracoOrigem) {
      blocoTalentoOrigem += `<div class="traco-secao-label" style="font-size:10px">+ Talento de Origem (via ${escapeHtml(tracoOrigem.Nome)})</div>`;
      blocoTalentoOrigem += renderOrigemSlot(state.talento_origem_racial, "racial", `Talento de Origem (${tracoOrigem.Nome})`);
    }

    // Slots por instância de Segredo Místico que dá pick:talento-origem:N
    // (ex.: Aprendizado dos Antigos × N — repetível). Cada instância tem seu próprio
    // slot dedicado, idêntico em layout aos slots fixos. Ordenado por SlotIndex.
    const segredosComPickTO = (state.segredos_misticos || []).filter(seg => {
      try {
        const tags = JSON.parse(seg.TagsJSON || "[]");
        return Array.isArray(tags) && tags.some(x => /^pick:talento-origem:\d+$/.test(x));
      } catch { return false; }
    });
    segredosComPickTO.sort((a, b) => (a.SlotIndex || 0) - (b.SlotIndex || 0));
    segredosComPickTO.forEach((seg, idx) => {
      const labelSuf = segredosComPickTO.length > 1 ? ` #${idx + 1}` : "";
      const to = seg.talento_origem;
      const sid = seg.Id;
      blocoTalentoOrigem += `<div class="traco-secao-label" style="font-size:10px">+ Talento de Origem (via ${escapeHtml(seg.Nome)}${labelSuf})</div>`;
      if (to) {
        blocoTalentoOrigem += `<div class="feat-card feat-raca clickable" data-pick-talento-origem-segredo data-sid="${sid}" title="Click para trocar/remover">
          <div class="feat-card-head">
            <span class="feat-nome">${escapeHtml(to.Nome)}</span>
            ${renderTagBadges(to.TagsJSON)}
            <span class="hab-pin ok">✓</span>
          </div>
          <div class="feat-card-desc">${renderMarkdown(to.Descricao || "")}</div>
        </div>`;
      } else {
        blocoTalentoOrigem += `<div class="tier-slot empty" data-pick-talento-origem-segredo data-sid="${sid}">
          <i>Talento de Origem (${escapeHtml(seg.Nome)}${labelSuf}) — clique para escolher</i>
        </div>`;
      }
    });

    const tracosR = [
      // Headers de seção carregam tags da própria linha-mãe (TB_Raca/Linhagem/Essencia/EssLinhagem) —
      // cada bloco mostra suas tags em cima, conforme regra de tags universais.
      tracosRacaBase.length ? `<div class="traco-secao-label">Raça base — ${escapeHtml(state.raca?.Nome || "—")} ${renderTagBadges(state.raca?.TagsJSON)}</div>` + tracosRacaBase.map(fmtTraco).join("") : "",
      tracosRacaLin.length  ? `<div class="traco-secao-label">Linhagem — ${escapeHtml(state.linhagem?.Nome || "—")} ${renderTagBadges(state.linhagem?.TagsJSON)}</div>` + tracosRacaLin.map(fmtTraco).join("") : "",
      tracosEssBase.length  ? `<div class="traco-secao-label">Essência — ${escapeHtml(state.essencia?.Nome || "—")} ${renderTagBadges(state.essencia?.TagsJSON)}</div>` + tracosEssBase.map(fmtTraco).join("") : "",
      tracosEssSub.length   ? `<div class="traco-secao-label">Sub-linhagem — ${escapeHtml(state.ess_linhagem?.Nome || "—")} ${renderTagBadges(state.ess_linhagem?.TagsJSON)}</div>` + tracosEssSub.map(fmtTraco).join("") : "",
      cardLegado,
      `<div class="traco-secao-label">Talento de Origem</div>` + blocoTalentoOrigem,
    ].filter(Boolean).join("");
    el.insertAdjacentHTML("beforeend", `
      <div class="f-features f-features-grid">
        <div class="feat-col">${habCls}</div>
        <div class="feat-col">${habSub}</div>
        <div class="feat-col">
          <div class="feat-head">Raça / Traços</div>
          ${tracosR || `<div class="feat-item" style="color:#bbb">—</div>`}
        </div>
      </div>
      <div class="sec-label">Características</div>`);

    // ===== Talentos por tier =====
    const TIERS_RACIAIS = [1, 5, 9, 13, 17];
    const nivelAtual = p.Nivel || 1;

    // Raça + Essência compartilham os mesmos 5 slots — user escolhe 1 por tier
    const talsRacEss = (state.talentos || []).filter(t => t.Categoria === "raca" || t.Categoria === "essencia");

    // Talentos de classe: slots nos níveis de ASI da classe (D&D 5.5)
    // Multiclasse: cada classe tem seu próprio campo de "Talentos de Classe".
    // Slots ASI vêm de TB_Classe.ASINiveisJSON da CLASSE específica, gated pelo
    // nível DAQUELA classe (não total). Talentos atribuídos por Id_Classe.
    const allTalsClasse = (state.talentos || []).filter(t => t.Categoria === "classe");

    // Slots de talento (raça/essência ou classe). Quando filled, renderiza descrição completa
    // como feat-card; quando empty/locked, mantém o slot compacto. Botão X explícito remove.
    // nivelEfetivo: nivel pra resolver lock. Default = nivelAtual (total). Pra classe usar c.Nivel.
    const tierSlot = (cat, tier, arr, rotulo, nivelEfetivo) => {
      const nivelLock = (nivelEfetivo != null) ? nivelEfetivo : nivelAtual;
      const locked = nivelLock < tier;
      const t = arr.find(x => (x.Nivel || 1) === tier);
      if (t) {
        const cls = locked ? "tier-slot tier-slot-card locked filled" : "tier-slot tier-slot-card filled";
        const lockIcon = locked ? "🔒 " : "";
        const desc = t.Detalhes_Final || t.Detalhes || t.DescricaoCatalogo || "";

        // save-prof-vontade: parse a tag p/ render inline picker (raca/essencia/classe).
        // Tag: "save-prof-vontade:<default>|<alt1>,<alt2>"
        // - Se char já tem default em classe_saves → render botões pra escolher entre alts.
        // - Senão → mostra badge "auto: save-prof:<default>" (informativo, sem pick).
        // Pick é gravado em AumentoAtributo via mesma rota dos ASIs ('int'/'car'/'sab').
        let vontadeBlock = "";
        try {
          const tagsArr = JSON.parse(t.TagsJSON || "[]") || [];
          const vTag = tagsArr.find(x => typeof x === "string" && x.startsWith("save-prof-vontade:"));
          if (vTag) {
            const valor = vTag.split(":", 2)[1] || "";
            const parts = valor.split("|");
            const defSave = (parts[0] || "").trim();
            const alts = (parts[1] || "").split(",").map(s => s.trim()).filter(Boolean);
            const classeSaves = state.classe_saves || [];
            const SHORT_BY_FULL = {Forca:"for", Destreza:"dex", Constituicao:"con",
                                   Inteligencia:"int", Sabedoria:"sab", Carisma:"car"};
            const FULL_BY_SHORT = {for:"Forca", dex:"Destreza", con:"Constituicao",
                                   int:"Inteligencia", sab:"Sabedoria", car:"Carisma"};
            if (classeSaves.includes(defSave)) {
              const escolhidaShort = (t.AumentoAtributo || "").toLowerCase();
              const escolhidaFull = FULL_BY_SHORT[escolhidaShort];
              if (escolhidaFull && alts.includes(escolhidaFull)) {
                vontadeBlock = `<span class="aumento-badge" data-vontade-pick data-tid="${t.Id_Talento}" title="Trocar/limpar">save-prof: ${escapeHtml(escolhidaFull)}</span>`;
              } else if (locked) {
                vontadeBlock = `<small style="color:#aa3">save-prof (locked) — escolha um quando ativar</small>`;
              } else {
                const btns = alts.map(a => {
                  const sh = SHORT_BY_FULL[a] || a.slice(0,3).toLowerCase();
                  return `<button type="button" class="aumento-btn" data-vontade-pick data-tid="${t.Id_Talento}" data-attr="${sh}">save-prof: ${escapeHtml(a)}</button>`;
                }).join("");
                vontadeBlock = `<span class="aumento-pick-row">${btns}</span>`;
              }
            } else {
              vontadeBlock = `<span class="aumento-badge" style="opacity:.7" title="Auto-aplicado: você ainda não tem ${escapeHtml(defSave)} de outra fonte">auto: save-prof: ${escapeHtml(defSave)}</span>`;
            }
          }
        } catch (e) { /* tag malformada → ignora */ }

        // Aumento de Atributo: badge(s) se já escolhido, picker(s) inline se não.
        // Locked = não permite escolher (e bonus não conta).
        // spec.picks=1 → 1 atributo. picks=2 → 2 atributos diferentes.
        let aumentoBlock = "";
        if (t.AumentoSpec && cat === "classe") {
          const labels = {for:"FOR", dex:"DEX", con:"CON", int:"INT", sab:"SAB", car:"CAR"};
          const picks = t.AumentoSpec.picks || 1;
          const bonus = t.AumentoSpec.bonus || 1;
          const escolhidas = (t.AumentoAtributo || "").toLowerCase().split(",").filter(Boolean);
          const permitidos = t.AumentoSpec.permitidos || [];
          const lockedTag = locked ? " <small style='color:#aa3'>(locked, não conta)</small>" : "";

          if (escolhidas.length >= picks) {
            // todos escolhidos — mostra badges (cada uma clicável pra trocar/limpar tudo)
            const badges = escolhidas.map(a =>
              `<span class="aumento-badge" data-aumento-pick data-tid="${t.Id_Talento}" title="Trocar/limpar (afeta todas)">+${bonus} ${labels[a] || a.toUpperCase()}</span>`
            ).join(" ");
            aumentoBlock = `${badges}${lockedTag}`;
          } else if (locked) {
            aumentoBlock = `<small style="color:#aa3">+${bonus}${picks > 1 ? " ×" + picks : ""} atributo (locked)</small>`;
          } else {
            // pelo menos 1 falta — todos permitidos como botão (repetir é OK quando spec.diferentes=false)
            const opts = permitidos.map(a =>
              `<button type="button" class="aumento-btn" data-aumento-pick data-tid="${t.Id_Talento}" data-attr="${a}">+${bonus} ${labels[a] || a.toUpperCase()}</button>`
            ).join("");
            const jaEscolhidas = escolhidas.length
              ? escolhidas.map(a => `<span class="aumento-badge" data-aumento-pick data-tid="${t.Id_Talento}" title="Trocar">+${bonus} ${labels[a] || a.toUpperCase()}</span>`).join(" ") + " "
              : "";
            const restanteLabel = picks > 1 ? `<small style="color:#888">${picks - escolhidas.length}/${picks}:</small> ` : "";
            aumentoBlock = `${jaEscolhidas}<span class="aumento-pick-row">${restanteLabel}${opts}</span>`;
          }
        }
        // pick:* slots vêm direto da TagsJSON do talento — mesma lógica de fmtTraco.
        // Permite traços/talentos como Multi-talentoso (pick:talento-geral:1) ou
        // Aprendizado dos Antigos (pick:talento-origem:1) spawnarem slots inline.
        // Skip 'talento-origem' — esse tem slot dedicado em "Talento de Origem".
        const pickerBlocks = locked ? "" : renderPickSlotsFromTags(
          t.TagsJSON, t.Nome, undefined, nivelLock, ['talento-origem', 'maestria-arma', 'tecnica-furtividade', 'metamagia', 'estilo-danca', 'infusao-artificer'],
        );
        return `<div class="${cls}" data-pick-tier="${cat}" data-tier="${tier}" data-talid="${t.Id_Talento || ""}" data-tid="${t.Id_Talento || ""}" data-locked="${locked ? 1 : 0}">
          <div class="feat-card-head">
            <span class="feat-nome">${lockIcon}${escapeHtml(t.Nome)}</span>
            ${renderTagBadges(t.TagsJSON)}
            ${aumentoBlock}
            ${vontadeBlock}
            <span class="hab-pin tier-x" data-tier-remove="${cat}-${tier}" title="Remover">×</span>
          </div>
          <div class="feat-card-desc">${desc}</div>
          ${pickerBlocks}
        </div>`;
      }
      const lockIcon = locked ? "🔒 " : "";
      const cls = locked ? "tier-slot locked empty" : "tier-slot empty";
      return `<div class="${cls}" data-pick-tier="${cat}" data-tier="${tier}" data-locked="${locked ? 1 : 0}">
        <i>${lockIcon}${rotulo} — clique para ${locked ? "planejar" : "escolher"}</i>
      </div>`;
    };

    // Coluna Raça+Essência (combinada)
    const colRacEss = `
      <div class="talent-col tier-col">
        <h3>Talentos de Raça / Essência</h3>
        ${TIERS_RACIAIS.map(nv => tierSlot("racess", nv, talsRacEss, `Nv ${nv}+`)).join("")}
      </div>`;

    // Coluna Classe — UMA por classe do personagem (multiclasse).
    // Talents filtrados por Id_Classe; slots gated pelo nível DAQUELA classe.
    const colsClasse = (state.classes || []).length ? (state.classes || []).map(c => {
      let asiNiveisCls = [];
      // ASINiveisJSON vem de TB_Classe; classes_pc agora também tem se quiser.
      // Como classes_pc não traz, busca lookup via state.classe se for primária OU
      // assume PHB padrão [4,8,12,16,19] se não tiver dado (fallback de Guerreiro
      // tem [4,6,8,12,14,16,19] específico — só funciona se for primária).
      if (state.classe && state.classe.Id_Classe === c.Id_Classe && state.classe.ASINiveisJSON) {
        try { asiNiveisCls = JSON.parse(state.classe.ASINiveisJSON); } catch {}
      }
      // Fallback PHB 2024 padrão (5 ASIs)
      if (!asiNiveisCls.length) asiNiveisCls = [4, 8, 12, 16, 19];
      // Compat: talentos legacy sem Id_Classe (NULL) → atribui à classe primária (ordem 0)
      const ehPrimaria = c.Ordem === 0 || c.Ordem === undefined;
      const talsThisClasse = allTalsClasse.filter(t =>
        t.Id_Classe === c.Id_Classe || (ehPrimaria && (t.Id_Classe === null || t.Id_Classe === undefined))
      );
      // Usa o renderer canônico tierSlot — feat-card completo (descrição, ASI block,
      // vontade block, tags) tanto pra raça/essência quanto pra classe. Lock gated por
      // c.Nivel (nível DAQUELA classe, não total). data-id-classe é injetado depois
      // via attribute fixup pra rotear pickers/removes pra classe certa.
      const slots = asiNiveisCls.map(nv => {
        const html = tierSlot("classe", nv, talsThisClasse, `Nv ${nv}`, c.Nivel);
        // Injeta data-id-classe="..." na div externa do slot — necessário pra
        // multiclasse: handler usa esse id pra associar talento à classe correta.
        return html.replace(
          'data-pick-tier="classe"',
          `data-pick-tier="classe" data-id-classe="${c.Id_Classe}"`,
        );
      }).join("");
      return `<div class="talent-col tier-col">
        <h3>Talentos de Classe <small>(${escapeHtmlBare(c.NomeClasse)} ${c.Nivel})</small></h3>
        ${slots}
      </div>`;
    }).join("") : `<div class="talent-col tier-col">
      <h3>Talentos de Classe</h3>
      <div class="tier-slot locked">escolha uma classe primeiro</div>
    </div>`;

    // Layout: Raça/Essência + N colunas de classe
    const numClasseCols = (state.classes || []).length || 1;
    const gridCols = `1fr ${' 1fr'.repeat(numClasseCols)}`;
    el.insertAdjacentHTML("beforeend", `
      <div class="sec-grid" style="grid-template-columns:${gridCols};">
        ${colRacEss}
        ${colsClasse}
      </div>`);

    // ===== Idiomas + Ferramentas + Percepção =====
    // Padroniza com caixas estilo Resistências/Imunidades — cada item vira card
    // individual com tooltip de origem (igual ao byRes/byCond abaixo).
    // Mescla múltiplas fontes (sem duplicar, case-insensitive):
    //   - state.idiomas (TB_PersonagemIdioma — picks via tag, background, manual)
    //   - state.profs_idioma_extras / profs_ferramenta_extras (tags prof-idioma/prof-ferramenta)
    //   - TB_Classe.ToolProfJSON da classe primária → ferramentas concedidas
    const renderItens = (lista) => {
      const items = lista.map(x => {
        const titleAttr = x.Origem ? ` title="${escapeHtmlBare(x.Origem)}"` : "";
        return `<div class="r"${titleAttr}>${escapeHtmlBare(x.Nome)}</div>`;
      });
      return items.join("") || `<div class="r" style="color:#ccc">—</div>`;
    };
    const mergeUniqueByName = (...listas) => {
      const seen = new Set();
      const out = [];
      for (const lista of listas) {
        for (const it of lista) {
          const k = (it.Nome || "").toLowerCase();
          if (!k || seen.has(k)) continue;
          seen.add(k);
          out.push(it);
        }
      }
      return out;
    };
    // Ferramentas vindas de TB_Classe.ToolProfJSON (cada classe primária)
    const toolsDeClasses = [];
    (state.classes || []).forEach(c => {
      if ((c.Ordem ?? 0) !== 0) return;  // só primária
      try {
        const arr = JSON.parse(c.ToolProfJSON || "[]") || [];
        for (const t of arr) toolsDeClasses.push({ Nome: t, Origem: `Classe ${c.NomeClasse}` });
      } catch {}
    });
    // Armaduras/Armas vindas da classe primária
    const armorDeClasses = [];
    const weaponsDeClasses = [];
    (state.classes || []).forEach(c => {
      if ((c.Ordem ?? 0) !== 0) return;
      try {
        for (const a of (JSON.parse(c.ArmorProfJSON || "[]") || []))
          armorDeClasses.push({ Nome: a, Origem: `Classe ${c.NomeClasse}` });
        for (const w of (JSON.parse(c.WeaponProfJSON || "[]") || []))
          weaponsDeClasses.push({ Nome: w, Origem: `Classe ${c.NomeClasse}` });
      } catch {}
    });
    const idiomasItens = mergeUniqueByName(
      (state.idiomas || []).filter(x => x.Tipo === "idioma"),
      (state.profs_idioma_extras || []).map(x => ({ Nome: x.valor, Origem: x.origem })),
    );
    const ferramItens = mergeUniqueByName(
      (state.idiomas || []).filter(x => x.Tipo === "ferramenta"),
      (state.profs_ferramenta_extras || []).map(x => ({ Nome: x.valor, Origem: x.origem })),
      toolsDeClasses,
    );
    const armaduraItens = mergeUniqueByName(
      armorDeClasses,
      (state.profs_armadura_extras || []).map(x => ({ Nome: x.valor, Origem: x.origem })),
    );
    const armaItens = mergeUniqueByName(
      weaponsDeClasses,
      (state.profs_arma_extras || []).map(x => ({ Nome: x.valor, Origem: x.origem })),
    );
    el.insertAdjacentHTML("beforeend", `
      <div class="sec-grid" style="grid-template-columns:1fr 2fr;">
        <div class="box" style="text-align:center;">
          <h3>Percepção Passiva</h3>
          <div style="font-size:36px; font-weight:700; color:var(--accent);">${p.PercepcaoPassiva ?? "?"}</div>
        </div>
        <div class="resist-wrap" style="grid-template-columns:1fr 1fr 1fr 1fr;">
          <div class="resist-box"><h4>Idiomas</h4>${renderItens(idiomasItens)}</div>
          <div class="resist-box"><h4>Ferramentas</h4>${renderItens(ferramItens)}</div>
          <div class="resist-box"><h4>Armaduras</h4>${renderItens(armaduraItens)}</div>
          <div class="resist-box"><h4>Armas</h4>${renderItens(armaItens)}</div>
        </div>
      </div>`);

    // ===== Aprendidos por dinheiro / treino — idiomas+ferramentas livres =====
    const aprendidos = (state.idiomas || []).filter(i => i.Origem === "aprendido");
    const aprendIdioms = aprendidos.filter(i => i.Tipo === "idioma");
    const aprendFerrs = aprendidos.filter(i => i.Tipo === "ferramenta");
    const renderAprend = (lst) => lst.length
      ? lst.map(i => `<span class="aprend-chip" data-id="${i.Id}">${escapeHtml(i.Nome)} <span class="aprend-x" data-aprend-remove="${i.Id}" title="Remover">×</span></span>`).join("")
      : `<small style="color:#aaa">— nenhum —</small>`;
    el.insertAdjacentHTML("beforeend", `
      <div class="aprendidos-box">
        <h3>Aprendidos por dinheiro / treino</h3>
        <div class="aprend-row">
          <div class="aprend-label">Idiomas:</div>
          <div class="aprend-list">${renderAprend(aprendIdioms)}</div>
          <button class="aprend-add" data-aprend-add="idioma">+ Idioma</button>
        </div>
        <div class="aprend-row">
          <div class="aprend-label">Ferramentas:</div>
          <div class="aprend-list">${renderAprend(aprendFerrs)}</div>
          <button class="aprend-add" data-aprend-add="ferramenta">+ Ferramenta</button>
        </div>
      </div>`);

    // ===== Resistências / Imunidades / Vulnerabilidades =====
    // Backend já agrega tags resist/immune/vuln + auto-efeitos da linhagem + manuais.
    const rs = state.resistencias || [];
    const byRes = (t) => {
      const items = rs.filter(r => r.Tipo === t).map(r => {
        const isLinhagem = (r.Origem || "").startsWith("Linhagem");
        const cls = isLinhagem ? "r auto" : "r";
        const star = isLinhagem ? " <small>★</small>" : "";
        const titleAttr = r.Origem ? ` title="${escapeHtmlBare(r.Origem)}"` : "";
        return `<div class="${cls}"${titleAttr}>${escapeHtmlBare(r.DanoTipo)}${star}</div>`;
      });
      return items.join("") || `<div class="r" style="color:#ccc">—</div>`;
    };
    // Condições: imune (não pode ser aplicada) e vantagem (vantagem em save)
    const conds = state.condicoes || [];
    const byCond = (t) => {
      const items = conds.filter(c => c.Tipo === t).map(c => {
        const titleAttr = c.Origem ? ` title="${escapeHtmlBare(c.Origem)}"` : "";
        return `<div class="r"${titleAttr}>${escapeHtmlBare(c.Condicao)}</div>`;
      });
      return items.join("") || `<div class="r" style="color:#ccc">—</div>`;
    };
    el.insertAdjacentHTML("beforeend", `
      <div class="resist-wrap">
        <div class="resist-box"><h4>Resistências <small>(dano)</small></h4>${byRes("resistencia")}</div>
        <div class="resist-box"><h4>Imunidades <small>(dano)</small></h4>${byRes("imunidade")}</div>
        <div class="resist-box"><h4>Vulnerabilidades</h4>${byRes("vulnerabilidade")}</div>
        <div class="resist-box"><h4>Imune a Condição</h4>${byCond("condicao-imune")}</div>
        <div class="resist-box"><h4>Vantagem vs. Condição</h4>${byCond("condicao-vantagem")}</div>
      </div>`);

    // ===== Inventário =====
    const invRows = (state.inventario || []).map(i => `
      <div class="r ${i.Sintonizado ? "s" : ""}">${i.Qtd}</div>
      <div class="r ${i.Sintonizado ? "s" : ""}">${i.Item}${i.Sintonizado ? " ◆" : ""}</div>
      <div class="r right">${i.Custo || ""}</div>
      <div class="r right">${i.Peso || ""}</div>
      <div class="r"></div>
    `).join("");
    el.insertAdjacentHTML("beforeend", `
      <div class="inv-wrap">
        <h3>Mochila & Equipamento</h3>
        <div class="inv-grid">
          <div class="h">#</div><div class="h">ITEM</div><div class="h">CUSTO</div><div class="h">PESO</div><div class="h"></div>
          ${invRows || `<div class="r" style="grid-column:1/-1;color:#aaa;">vazio</div>`}
        </div>
      </div>`);

    // ===== Técnicas / Manobras — slots derivados da progressão da classe =====
    // Padrão idêntico aos talentos de Raça/Essência: cada slot tem min_level próprio,
    // empty/filled/locked. Locked = clicável p/ planejamento.
    const slotsSpec = state.manobras_slots || [];
    if (slotsSpec.length > 0) {
      const tecnicas = state.tecnicas || [];
      const limiteAtual = parseInt(state.limites?.manobras, 10) || 0;
      const atuais = tecnicas.length;

      const slotsHTML = slotsSpec.map((s, i) => {
        const t = tecnicas[i];
        const locked = nivelAtual < (s.min_level || 1);
        const grauHint = `Grau ≤ ${s.grau_max_at}`;
        if (t) {
          // preenchido: nome + grau + (descrição inicialmente collapsed). Click expande, X remove.
          const tagBadge = `<small class="tal-grau">${t.Grau ? `Grau ${t.Grau}` : ""}</small>`;
          const desc = t.Descricao || "";
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-tecnica-slot data-tid="${t.Id}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(t.Nome)}</span>
              ${tagBadge}
              <span class="hab-pin tier-x" data-tecnica-remove="${t.Id}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="0">${desc}</div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level}+`;
        const verb = locked ? "planejar" : "escolher";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-tecnica-slot data-slot="${s.slot}" data-min-level="${s.min_level}" data-grau-max="${s.grau_max_at}">
          <i>${lockIcon}Manobra ${s.slot} (${lvlText} · ${grauHint}) — clique para ${verb}</i>
        </div>`;
      }).join("");

      // CD de Manobra: 8 + BP + max(For mod, Dex mod). Útil pra manobras que pedem save.
      const profMan = profByLevel(state.personagem?.Nivel || 1);
      const forMod = mod(atrFinal(state, "Forca"));
      const dexMod = mod(atrFinal(state, "Destreza"));
      const manAttr = forMod >= dexMod ? "FOR" : "DES";
      const manMod = Math.max(forMod, dexMod);
      const manCD = 8 + profMan + manMod;
      const manInfo = `<small style="margin-left:8px;color:#5d4d2a">· CD ${manCD} · ${manAttr} ${sgn(manMod)}</small>`;
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Técnicas / Manobras <small class="tech-count">${atuais}/${limiteAtual}</small>${manInfo}</h3>
          <div class="tech-slots-grid">${slotsHTML}</div>
        </div>`);
    } else if ((state.tecnicas || []).length) {
      // fallback legado: classe sem progressão de manobras mas tem técnicas
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list">
          <h3>Técnicas</h3>
          ${state.tecnicas.map(t => `<div class="tech-item"><span class="n">${escapeHtml(t.Nome)}.</span>${t.Descricao || ""}</div>`).join("")}
        </div>`);
    }

    // ===== Segredos de Caçador — gated pela tag flat "segredos". Layout idêntico
    // ao de Manobras, mas sem grau (Caçador conhece todos os 19 desde Nv 2).
    const segSlots = state.segredos_slots || [];
    const hasSegTag = (state.aggregated_tags || []).some(t => t && t.tag === "segredos");
    if (hasSegTag && segSlots.length > 0) {
      const segredos = state.segredos || [];
      const limSeg = parseInt(state.limites?.segredos, 10) || segSlots.length;
      const atuaisSeg = segredos.length;
      const slotsSegHTML = segSlots.map((s, i) => {
        const seg = segredos[i];
        const locked = nivelAtual < (s.min_level || 1);
        if (seg) {
          const linhaBadge = `<small class="tal-grau">${escapeHtml(seg.Linha || "")}</small>`;
          const acaoBadge = seg.Acao ? `<small class="tal-grau">${escapeHtml(seg.Acao)}</small>` : "";
          const custo = seg.Custo ? `<small class="tal-grau">Custo ${seg.Custo}</small>` : "";
          const desc = seg.Descricao || "";
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-segredo-slot data-sid="${seg.Id}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(seg.Nome)}</span>
              ${linhaBadge}${acaoBadge}${custo}
              <span class="hab-pin tier-x" data-segredo-remove="${seg.Id}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="0">${desc}</div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level}+`;
        const verb = locked ? "planejar" : "escolher";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-segredo-slot data-slot="${s.slot}" data-min-level="${s.min_level}">
          <i>${lockIcon}Segredo ${s.slot} (${lvlText}) — clique para ${verb}</i>
        </div>`;
      }).join("");
      // Habilidade de Conjuração do Caçador: INT ou SAB. CD = 8 + BP + max(INT, SAB)
      const profSeg = profByLevel(state.personagem?.Nivel || 1);
      const intMod = mod(atrFinal(state, "Inteligencia"));
      const sabMod = mod(atrFinal(state, "Sabedoria"));
      const segAttr = intMod >= sabMod ? "INT" : "SAB";
      const segMod = Math.max(intMod, sabMod);
      const segCD = 8 + profSeg + segMod;
      const pontos = state.pontos_segredo_max || 0;
      const dado = state.dado_cacador || "";
      const segInfo = `<small style="margin-left:8px;color:#5d4d2a">· Pontos ${pontos} · Dado ${dado} · CD ${segCD} · ${segAttr} ${sgn(segMod)}</small>`;
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Segredos de Caçador <small class="tech-count">${atuaisSeg}/${limSeg}</small>${segInfo}</h3>
          <div class="tech-slots-grid">${slotsSegHTML}</div>
        </div>`);
    }

    // ===== Inimigo Favorito — gated pela tag flat "inimigo-favorito".
    const inimSlots = state.inimigos_favoritos_slots || [];
    const hasInimTag = (state.aggregated_tags || []).some(t => t && t.tag === "inimigo-favorito");
    if (hasInimTag && inimSlots.length > 0) {
      const inims = state.inimigos_favoritos || [];
      const limInim = parseInt(state.limites?.inimigos_favoritos, 10) || inimSlots.length;
      const atuaisInim = inims.length;
      const slotsInimHTML = inimSlots.map((s, i) => {
        const inim = inims[i];
        const locked = nivelAtual < (s.min_level || 1);
        if (inim) {
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-inimigo-slot data-iid="${inim.Id}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(inim.Nome)}</span>
              <span class="hab-pin tier-x" data-inimigo-remove="${inim.Id}" title="Remover">×</span>
            </div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level}+`;
        const verb = locked ? "planejar" : "escolher";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-inimigo-slot data-slot="${s.slot}" data-min-level="${s.min_level}">
          <i>${lockIcon}Inimigo ${s.slot} (${lvlText}) — clique para ${verb}</i>
        </div>`;
      }).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Inimigo Favorito <small class="tech-count">${atuaisInim}/${limInim}</small></h3>
          <div class="tech-slots-grid">${slotsInimHTML}</div>
        </div>`);
    }

    // ===== Evolução Totêmica — gated pela tag flat "evolucao-totemica".
    const evolSlots = state.evolucoes_totemicas_slots || [];
    const hasEvolTag = (state.aggregated_tags || []).some(t => t && t.tag === "evolucao-totemica");
    if (hasEvolTag && evolSlots.length > 0) {
      const evols = state.evolucoes_totemicas || [];
      const limEvol = parseInt(state.limites?.evolucoes_totemicas, 10) || evolSlots.length;
      const atuaisEvol = evols.length;

      // Card "ficha do bicho" no topo: variante ativa via tag (Terra/Céu/Mar).
      const ep = state.espirito_primordial;
      let espiritoCard = "";
      if (ep) {
        const velLine = [
          ["andar", ep.Vel_Andar], ["voar", ep.Vel_Voar],
          ["nadar", ep.Vel_Nadar], ["escalar", ep.Vel_Escalar],
        ].filter(([_k,v]) => v > 0).map(([k,v]) => `${k} ${v}ft`).join(" · ");
        const atrCol = (lbl, v) => `<div class="ep-atr"><div class="ep-atr-l">${lbl}</div><div class="ep-atr-v">${v}</div><div class="ep-atr-m">${sgn(mod(v))}</div></div>`;
        espiritoCard = `
          <div class="espirito-primordial-card">
            <div class="ep-head">
              <span class="ep-nome">Espírito Primordial — ${escapeHtml(ep.Nome)}</span>
              <span class="ep-stat">CA ${ep.CA}</span>
              <span class="ep-stat">PV ${ep.PV_Max}</span>
              <span class="ep-stat">Vel ${velLine}</span>
            </div>
            <div class="ep-atrs">
              ${atrCol("FOR", ep.Forca)}${atrCol("DES", ep.Destreza)}${atrCol("CON", ep.Constituicao)}
              ${atrCol("INT", ep.Inteligencia)}${atrCol("SAB", ep.Sabedoria)}${atrCol("CAR", ep.Carisma)}
            </div>
            ${ep.Flavor ? `<div class="ep-flavor"><small><i>${escapeHtmlBare(ep.Flavor)}</i></small></div>` : ""}
          </div>`;
      } else if (hasEvolTag) {
        espiritoCard = `<div class="espirito-primordial-card empty">
          <small><i>Escolha o Companheiro Primordial (Terra/Céu/Mar) para revelar a ficha do espírito.</i></small>
        </div>`;
      }
      const slotsEvolHTML = evolSlots.map((s, i) => {
        const ev = evols[i];
        const locked = nivelAtual < (s.min_level || 1);
        if (ev) {
          const tierBadge = `<small class="tal-grau">${escapeHtml(ev.Tier || "")}</small>`;
          const variantBadge = ev.Variante ? `<small class="tal-grau">${escapeHtml(ev.Variante)}</small>` : "";
          const desc = ev.Descricao || "";
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-evolucao-slot data-eid="${ev.Id}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(ev.Nome)}</span>
              ${tierBadge}${variantBadge}
              <span class="hab-pin tier-x" data-evolucao-remove="${ev.Id}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="0">${desc}</div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level}+`;
        const tierText = s.tier_max === "maior" ? "Menor ou Maior" : "Menor";
        const verb = locked ? "planejar" : "escolher";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-evolucao-slot data-slot="${s.slot}" data-min-level="${s.min_level}" data-tier-max="${s.tier_max}">
          <i>${lockIcon}Evolução ${s.slot} (${lvlText} · ${tierText}) — clique para ${verb}</i>
        </div>`;
      }).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Evolução Totêmica <small class="tech-count">${atuaisEvol}/${limEvol}</small></h3>
          ${espiritoCard}
          <div class="tech-slots-grid">${slotsEvolHTML}</div>
        </div>`);
    }

    // ===== Estilos de Ki — gated pela tag flat "estilos-ki" (Monge Nv 2+).
    const kiSlots = state.estilos_ki_slots || [];
    const hasKiTag = (state.aggregated_tags || []).some(t => t && t.tag === "estilos-ki");
    if (hasKiTag && kiSlots.length > 0) {
      const estilos = state.estilos_ki || [];
      const limKi = parseInt(state.limites?.estilos_ki, 10) || kiSlots.length;
      const atuaisKi = estilos.length;
      const slotsKiHTML = kiSlots.map((s, i) => {
        const k = estilos[i];
        const locked = nivelAtual < (s.min_level || 1);
        if (k) {
          const custoBadge = `<small class="tal-grau">Custo ${k.CustoKi} Ki</small>`;
          const desc = k.Descricao || "";
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-estilo-ki-slot data-eid="${k.Id}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(k.Nome)}</span>
              ${custoBadge}
              <span class="hab-pin tier-x" data-estilo-ki-remove="${k.Id}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="0">${desc}</div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level}+`;
        const verb = locked ? "planejar" : "escolher";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-estilo-ki-slot data-slot="${s.slot}" data-min-level="${s.min_level}">
          <i>${lockIcon}Estilo ${s.slot} (${lvlText}) — clique para ${verb}</i>
        </div>`;
      }).join("");
      // Header muda pra "Estilos Kensei" se char tem a tag (sub Kensei)
      const isKensei = (state.aggregated_tags || []).some(t => t && t.tag === "kensei-estilos");
      const titleKi = isKensei ? "Estilos Kensei" : "Estilos de Ki";
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>${titleKi} <small class="tech-count">${atuaisKi}/${limKi}</small></h3>
          <div class="tech-slots-grid">${slotsKiHTML}</div>
        </div>`);
    }

    // ===== Segredos Místicos — gated pela tag flat 'segredos-misticos' (Místico Nv 2+).
    const segMSlots = state.segredos_misticos_slots || [];
    const hasSegMTag = (state.aggregated_tags || []).some(t => t && t.tag === "segredos-misticos");
    if (hasSegMTag && segMSlots.length > 0) {
      const segsM = state.segredos_misticos || [];
      const limSegM = parseInt(state.limites?.segredos_misticos, 10) || segMSlots.length;
      const atuaisSegM = segsM.length;
      const slotsSegMHTML = segMSlots.map((s, i) => {
        const seg = segsM[i];
        const locked = nivelAtual < (s.min_level || 1);
        if (seg) {
          const secaoBadge = `<small class="tal-grau">${escapeHtml(seg.Secao || "")}</small>`;
          const repBadge = seg.Repetivel ? `<small class="tal-grau" style="background:#2e8b5b22;color:#2e8b5b">♻ repetível</small>` : "";
          const tagBadges = renderTagBadges(seg.TagsJSON);
          const desc = seg.Descricao || "";
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-segredo-mistico-slot data-sid="${seg.Id}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(seg.Nome)}</span>
              ${secaoBadge}${repBadge}${tagBadges}
              <span class="hab-pin tier-x" data-segredo-mistico-remove="${seg.Id}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="0">${desc}</div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level}+`;
        const verb = locked ? "planejar" : "escolher";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-segredo-mistico-slot data-slot="${s.slot}" data-min-level="${s.min_level}">
          <i>${lockIcon}Segredo ${s.slot} (${lvlText}) — clique para ${verb}</i>
        </div>`;
      }).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Segredos Místicos <small class="tech-count">${atuaisSegM}/${limSegM}</small></h3>
          <div class="tech-slots-grid">${slotsSegMHTML}</div>
        </div>`);
    }

    // ===== Maestrias de Armas — slots derivados de "Maestrias de Armas" da progressão =====
    const maesSlots = state.maestrias_armas_slots || [];
    if (maesSlots.length > 0) {
      const picks = state.maestrias_armas || [];
      const pickBySlot = {};
      picks.forEach(p => { if (p && p.SlotIndex != null) pickBySlot[p.SlotIndex] = p; });
      const limAtual = maesSlots.filter(s => nivelAtual >= (s.min_level || 1)).length;
      const atuaisCount = picks.length;

      const maesHTML = maesSlots.map((s, i) => {
        const slotIdx = s.slot - 1;  // SlotIndex 0-based no DB
        const p = pickBySlot[slotIdx];
        const locked = nivelAtual < (s.min_level || 1);
        if (p && p.ArmaNome) {
          // preenchido: arma + maestria + descrição collapsed. Click expande, X remove.
          const maestriaTxt = p.MaestriaNome
            ? `${escapeHtml(p.MaestriaNome)}${p.MaestriaIngles ? ` (${escapeHtml(p.MaestriaIngles)})` : ""}`
            : "<i style='color:#aa3'>maestria não definida</i>";
          const desc = p.MaestriaEfeito || "";
          const kenseiBadge = p.is_arma_kensei ? `<small class="tag-badge tag-conjurador" title="Arma de Kensei — recebe efeitos da Tradição Kensei">⚔ Arma de Kensei</small>` : "";
          return `<div class="tier-slot filled expandable${locked ? " locked" : ""}" data-maestria-slot data-slot-index="${slotIdx}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(p.ArmaNome)}</span>
              <small class="tal-grau">${maestriaTxt}</small>
              ${kenseiBadge}
              <span class="hab-pin tier-x" data-maestria-remove="${slotIdx}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="0">${desc}</div>
          </div>`;
        }
        const lockIcon = locked ? "🔒 " : "";
        const lvlText = `Nv ${s.min_level || 1}+`;
        const verb = locked ? "planejar" : "escolher";
        const origemTxt = s.origem ? ` <small style="color:#888">⟵ ${escapeHtml(s.origem)}</small>` : "";
        return `<div class="tier-slot empty${locked ? " locked" : ""}" data-pick-maestria-slot data-slot-index="${slotIdx}" data-min-level="${s.min_level || 1}" title="${escapeHtml(s.origem || '')}">
          <i>${lockIcon}Maestria ${s.slot} (${lvlText}) — clique para ${verb}</i>${origemTxt}
        </div>`;
      }).join("");

      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Maestrias de Armas <small class="tech-count">${atuaisCount}/${limAtual}</small></h3>
          <div class="tech-slots-grid">${maesHTML}</div>
        </div>`);
    }

    // ===== Surto Selvagem (Druida) — gated pela tag flat 'surto-selvagem'.
    // ND Máximo é calculado pelo backend (state.surto_selvagem.cr_max). Druida
    // da Lua (presença da tag 'druida-lua') altera o cálculo para ⌈nv/3⌉.
    // Mostra: ND atual, formas conhecidas, voo permitido, badge "Druida da Lua".
    const hasSurto = (state.aggregated_tags || []).some(t =>
      (typeof t === "object" && t.tag === "surto-selvagem") ||
      (typeof t === "string" && t === "surto-selvagem"));
    const ss = state.surto_selvagem;
    if (hasSurto && ss && ss.nivel_druida > 0) {
      const luaBadge = ss.eh_lua
        ? `<span class="hab-pin" style="background:#5d3a8a;color:#fff;cursor:default;margin-left:8px" title="Círculo da Lua — ND = ⌈nível/3⌉">Druida da Lua</span>`
        : "";
      const vooTxt = ss.voo ? "Sim" : "Não";
      // Card de Surto Selvagem combina:
      //  (a) 3 slots informativos com cálculo do backend — ND Máximo, Formas
      //      Conhecidas, Voo Permitido (Forma Selvagem depende deles)
      //  (b) 5 opções expansíveis — uma por modalidade de gasto do uso
      const infoSlots = [
        {
          nome: "ND Máximo",
          valor: escapeHtmlBare(ss.cr_max),
          desc: ss.eh_lua
            ? `Círculo da Lua: ND = ⌈nível/3⌉ = ⌈${ss.nivel_druida}/3⌉ = <b>${escapeHtmlBare(ss.cr_max)}</b>.`
            : `Druida padrão: Nv 2→1/4, Nv 4→1/2, Nv 8→1.`
        },
        {
          nome: "Formas Conhecidas",
          valor: String(ss.formas_conhecidas),
          desc: "Bestas conhecidas que você pode assumir. Substitua 1 em cada Descanso Longo."
        },
        {
          nome: "Voo Permitido",
          valor: vooTxt,
          desc: "Bestas com deslocamento de voo liberadas a partir do Nv 8."
        },
      ];
      const infoHTML = infoSlots.map(s => `
        <div class="tier-slot filled">
          <div class="slot-head">
            <span class="tal-nome">${escapeHtmlBare(s.nome)}</span>
            <small class="tal-grau">${s.valor}</small>
          </div>
          <div class="slot-desc" data-collapsed="0">${s.desc}</div>
        </div>`).join("");

      const opcoes = [
        { nome: "Forma Selvagem", custo: "Ação Bônus · 1 uso",
          desc: "Transforma-se em uma de suas Formas Conhecidas por nº de horas = metade do nível de Druida (arred. baixo). PV temp. = 2 × nível de Druida. Usa Força/Destreza/Constituição da besta (mantém Int/Sab/Car), mantém proficiências (usa a maior). Não pode conjurar magias (mantém Concentração). Equipamento se funde ao corpo. Use os parâmetros calculados acima (ND, Formas, Voo)." },
        { nome: "Rito dos Antigos", custo: "Ação · 1 uso",
          desc: "Conjura uma magia de Druida preparada com a tag Ritual, sem gastar espaço e sem os 10 min extras de ritual." },
        { nome: "Erupção Elemental", custo: "Ação · 1 uso",
          desc: "Cria coluna cilíndrica de 1,5 m raio × 9 m altura em ponto a até 9 m. Terreno difícil até o início do seu próximo turno. Escolha Ar (trovejante), Terra (concussão), Ígneo (fogo) ou Água (frio). Cada criatura na área faz TR Destreza vs. sua CD de magia; falha sofre 2d6 + nível de Druida do tipo escolhido, sucesso metade. Colunas adicionais: Nv 9 = 2; Nv 17 = 3 (pontos distintos)." },
        { nome: "Elo Primal", custo: "Ação · 1 uso",
          desc: "Aprende encontrar familiar (não conta no limite preparado) e pode conjurá-la sem espaço/componentes. Familiar é Besta ou Planta, tamanho Miúdo ou Pequeno. ND máximo: Nv 2 = 0, Nv 4 = 1/8, Nv 8 = 1/4, Nv 12 = 1/2, Nv 16 = 1." },
        { nome: "Crescimento Virente", custo: "Ação · 1 uso",
          desc: "Aura de vegetação densa raio 3 m centrada em você, dura 1 min ou até ficar Incapacitado. Área é terreno difícil para criaturas hostis. Alcance expandido: Nv 9 = 6 m; Nv 17 = 9 m." },
      ];
      const opcoesHTML = opcoes.map(o => `
        <div class="tier-slot filled expandable">
          <div class="slot-head">
            <span class="tal-nome">${escapeHtmlBare(o.nome)}</span>
            <small class="tal-grau">${escapeHtmlBare(o.custo)}</small>
          </div>
          <div class="slot-desc" data-collapsed="1">${o.desc}</div>
        </div>`).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Surto Selvagem <small class="tech-count">ND ${escapeHtmlBare(ss.cr_max)} · 5 opções</small>${luaBadge}<small style="margin-left:8px;color:#5d4d2a">· Druida Nv ${ss.nivel_druida} · gasta 1 uso cada</small></h3>
          <div class="tech-slots-grid">${infoHTML}${opcoesHTML}</div>
        </div>`);
    }

    // ===== Pontos de Feitiçaria (Feiticeiro) — gated pela tag flat 'pontos-feiticaria'.
    // Mostra reserva max (= nível Feiticeiro) + tabela de conversão espaço↔PF.
    // Read-only — display de informação canônica do recurso de classe.
    const hasPF = (state.aggregated_tags || []).some(t =>
      (typeof t === "object" && t.tag === "pontos-feiticaria") ||
      (typeof t === "string" && t === "pontos-feiticaria"));
    const pfMax = state.pontos_feiticaria_max || 0;
    if (hasPF && pfMax > 0) {
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Pontos de Feitiçaria <small class="tech-count">${pfMax} PF</small><small style="margin-left:8px;color:#5d4d2a">· recupera em Descanso Longo</small></h3>
          <div class="tech-slots-grid">
            <div class="tier-slot filled">
              <div class="slot-head"><span class="tal-nome">Converter Espaço → PF</span></div>
              <div class="slot-desc" data-collapsed="0">Sem ação: gaste um espaço de magia para ganhar PF igual ao nível do espaço.</div>
            </div>
            <div class="tier-slot filled">
              <div class="slot-head"><span class="tal-nome">Criar Espaço com PF</span><small class="tal-grau">Ação Bônus</small></div>
              <div class="slot-desc" data-collapsed="0">Custo em PF por nível: 1º=2, 2º=3, 3º=5, 4º=6, 5º=7.</div>
            </div>
          </div>
        </div>`);
    }

    // ===== Metamagias (Feiticeiro) — picker via pick:metamagia:N progressivo
    // + auto-grants via tag flat `metamagia:<slug>` (features de origens que dão
    // 1 metamagia "sempre preparada que não conta no limite"). Catálogo
    // TB_OpcaoJogo Tipo='metamagia' (10 entries Bonfire). Custo em PF em
    // NivelMinimo. Picks vão pra TB_PersonagemEscolhaTag.
    const metamagiaSlots = [];
    const metamagiaAutoGrants = [];  // [{slug, origem}] — tag flat metamagia:<slug>
    (state.aggregated_tags || []).forEach(t => {
      if (typeof t !== "object") return;
      const tag = t.tag || "";
      const m = tag.match(/^pick:metamagia:(\d+)$/);
      if (m) {
        const n = parseInt(m[1], 10);
        const origem = t.origem || "Metamagia";
        for (let i = 0; i < n; i++) metamagiaSlots.push({ origem, idxLocal: i });
        return;
      }
      const ag = tag.match(/^metamagia:([a-z0-9-]+)$/);
      if (ag) metamagiaAutoGrants.push({ slug: ag[1], origem: t.origem || "auto" });
    });
    if (metamagiaSlots.length > 0 || metamagiaAutoGrants.length > 0) {
      const metaPicks = (state.escolhas_tag || []).filter(e => e.Tipo === "metamagia");
      const pickByKey = {};
      metaPicks.forEach(p => { pickByKey[`${p.Origem}|${p.SlotIndex}`] = p; });
      // Catálogo pra mostrar custo PF inline no slot filled
      const catBySlug = {};
      const catByNome = {};
      (state.metamagias_catalogo || []).forEach(o => {
        catBySlug[o.Slug] = o; catByNome[o.Nome] = o;
      });
      // Auto-grants vêm primeiro (sempre preparadas, não contam no limite).
      // Filtra duplicatas (mesma origem pode aparecer 2x via aggregated_tags).
      const seenAuto = new Set();
      const autoHTML = metamagiaAutoGrants.filter(ag => {
        if (seenAuto.has(ag.slug)) return false;
        seenAuto.add(ag.slug);
        return true;
      }).map(ag => {
        const cat = catBySlug[ag.slug] || {};
        const nome = cat.Nome || ag.slug;
        const custo = cat.NivelMinimo ? `${cat.NivelMinimo} PF` : "";
        const desc = (cat.Descricao || "").replace(/^\s*Custo:\s*\d+\s*PF\.?\s*/, "");
        return `<div class="tier-slot filled expandable" data-auto-grant="metamagia">
          <div class="slot-head">
            <span class="tal-nome">${escapeHtmlBare(nome)}</span>
            <small class="tal-grau">${escapeHtmlBare(custo)}</small>
            <span class="hab-pin" title="Sempre preparada — não conta no limite" style="background:#7a5d2a;color:#fff;cursor:default">sempre preparada</span>
          </div>
          <div class="slot-desc" data-collapsed="1"><small style="color:#7a5d2a">via ${escapeHtmlBare(ag.origem)}</small><br>${escapeHtmlBare(desc)}</div>
        </div>`;
      }).join("");

      let metaDone = 0;
      const metaHTML = metamagiaSlots.map((s, globalIdx) => {
        const key = `${s.origem}|${s.idxLocal}`;
        const p = pickByKey[key];
        if (p && p.Valor) {
          metaDone++;
          const cat = catByNome[p.Valor] || catBySlug[p.Valor] || {};
          const custo = cat.NivelMinimo ? `${cat.NivelMinimo} PF` : "";
          const desc = (cat.Descricao || "").replace(/^\s*Custo:\s*\d+\s*PF\.?\s*/, "");
          return `<div class="tier-slot filled expandable" data-pick-slot data-kind="metamagia" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtmlBare(p.Valor)}</span>
              <small class="tal-grau">${escapeHtmlBare(custo)}</small>
              <span class="hab-pin tier-x" data-pick-slot-remove data-kind="metamagia" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="1">${escapeHtmlBare(desc)}</div>
          </div>`;
        }
        return `<div class="tier-slot empty" data-pick-slot data-kind="metamagia" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}">
          <i>Metamagia ${globalIdx + 1} — clique para escolher <small style="color:#888">⟵ ${escapeHtmlBare(s.origem)}</small></i>
        </div>`;
      }).join("");
      const autoCount = seenAuto.size;
      const counterHTML = autoCount > 0
        ? `<small class="tech-count">${metaDone}/${metamagiaSlots.length} <span style="color:#7a5d2a">+${autoCount} sempre preparada${autoCount > 1 ? 's' : ''}</span></small>`
        : `<small class="tech-count">${metaDone}/${metamagiaSlots.length}</small>`;
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Metamagias ${counterHTML}<small style="margin-left:8px;color:#5d4d2a">· custo em PF · só 1 por feitiço (exceto se a opção indicar)</small></h3>
          <div class="tech-slots-grid">${autoHTML}${metaHTML}</div>
        </div>`);
    }

    // ===== Estilos de Dança (Bardo da Dança) — picker via pick:estilo-danca:N
    // progressivo (Nv 3=1, 6=2, 14=3, 18=4). Catálogo: estilos_danca_catalogo
    // (reusa TB_EstiloKi.Catalogo='ki' = 18 estilos do Monge). Regra de custo:
    // "1 ponto de Ki" → "1 uso de Inspiração Bárdica" para o Bardo da Dança.
    // Picks vão pra TB_PersonagemEscolhaTag Tipo='estilo-danca'.
    const danceSlots = [];
    (state.aggregated_tags || []).forEach(t => {
      if (typeof t !== "object") return;
      const tag = t.tag || "";
      const m = tag.match(/^pick:estilo-danca:(\d+)$/);
      if (!m) return;
      const n = parseInt(m[1], 10);
      const origem = t.origem || "Dança em Cena";
      for (let i = 0; i < n; i++) danceSlots.push({ origem, idxLocal: i });
    });
    if (danceSlots.length > 0) {
      const dancePicks = (state.escolhas_tag || []).filter(e => e.Tipo === "estilo-danca");
      const danceByKey = {};
      dancePicks.forEach(p => { danceByKey[`${p.Origem}|${p.SlotIndex}`] = p; });
      const danceCatBySlug = {};
      const danceCatByNome = {};
      (state.estilos_danca_catalogo || []).forEach(o => {
        danceCatBySlug[o.Slug] = o; danceCatByNome[o.Nome] = o;
      });
      let danceDone = 0;
      const danceHTML = danceSlots.map((s, globalIdx) => {
        const key = `${s.origem}|${s.idxLocal}`;
        const p = danceByKey[key];
        if (p && p.Valor) {
          danceDone++;
          const cat = danceCatByNome[p.Valor] || danceCatBySlug[p.Valor] || {};
          // Lê custo como "Inspiração Bárdica" no lugar de "Ki"
          const custo = cat.NivelMinimo ? `${cat.NivelMinimo} Insp. Bárdica` : "";
          // Substitui menções a "Ki" no texto do estilo (cosmético)
          const desc = (cat.Descricao || "")
            .replace(/(\d+)\s*ponto[s]? de Ki/gi, "$1 uso de Inspiração Bárdica")
            .replace(/\bKi\b/g, "Inspiração Bárdica");
          return `<div class="tier-slot filled expandable" data-pick-slot data-kind="estilo-danca" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtmlBare(p.Valor)}</span>
              <small class="tal-grau">${escapeHtmlBare(custo)}</small>
              <span class="hab-pin tier-x" data-pick-slot-remove data-kind="estilo-danca" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="1">${escapeHtmlBare(desc)}</div>
          </div>`;
        }
        return `<div class="tier-slot empty" data-pick-slot data-kind="estilo-danca" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}">
          <i>Estilo de Dança ${globalIdx + 1} — clique para escolher</i>
        </div>`;
      }).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Estilos de Dança <small class="tech-count">${danceDone}/${danceSlots.length}</small><small style="margin-left:8px;color:#5d4d2a">· custo em Inspiração Bárdica · pool = Estilos de Ki do Monge</small></h3>
          <div class="tech-slots-grid">${danceHTML}</div>
        </div>`);
    }

    // ===== Infusões de Artificer — picker via pick:infusao-artificer:N.
    // N = progressão da classe (n_por_nivel {2:4,6:5,10:6,14:7,18:8}) somada a
    // cada talento "Infusão de Artificer" (+1, emite pick:infusao-artificer:1).
    // Cada slot recebe: (a) infusão do catálogo (filtrada por NivelMinimo <=
    // nível Artífice; nível 1 = sem restrição), ou (b) item mágico Replicado
    // (selecionado da página de equipamentos, tratado como infusão).
    const infSlots = [];
    (state.aggregated_tags || []).forEach(t => {
      if (typeof t !== "object") return;
      const m = (t.tag || "").match(/^pick:infusao-artificer:(\d+)$/);
      if (!m) return;
      const n = parseInt(m[1], 10);
      const origem = t.origem || "Infusões";
      for (let i = 0; i < n; i++) infSlots.push({ origem, idxLocal: i });
    });
    if (infSlots.length > 0) {
      // nível do Artífice (filtra catálogo por restrição)
      const artClasse = (state.classes || []).find(c =>
        (c.SlugClasse || c.NomeClasse || "").toLowerCase().includes("artif"));
      const nivelArt = artClasse ? (artClasse.Nivel || 0) : (state.nivel_total || 0);
      const itensInfMax = state.itens_infundidos_max || 0;
      const infPicks = (state.escolhas_tag || []).filter(e => e.Tipo === "infusao-artificer");
      const infByKey = {};
      infPicks.forEach(p => { infByKey[`${p.Origem}|${p.SlotIndex}`] = p; });
      const infCatByNome = {};
      (state.infusoes_artificer_catalogo || []).forEach(o => { infCatByNome[o.Nome] = o; });
      let infDone = 0;
      // re-indexa slots num índice global contínuo (origens diferentes somam)
      const infHTML = infSlots.map((s, globalIdx) => {
        const key = `${s.origem}|${s.idxLocal}`;
        const p = infByKey[key];
        if (p && p.Valor) {
          infDone++;
          const ehReplica = p.Valor.startsWith("Replicar:");
          const cat = infCatByNome[p.Valor] || {};
          const badge = ehReplica
            ? `<small class="tal-grau" style="background:#2a5d7a22;color:#2a5d7a">item replicado</small>`
            : (cat.NivelMinimo > 1 ? `<small class="tal-grau">Nv ${cat.NivelMinimo}+</small>` : "");
          const desc = ehReplica
            ? "Item mágico replicado (selecionado da página de equipamentos). Trata-se como uma Infusão: imbui um objeto com as propriedades do item, seguindo as regras normais."
            : (cat.Descricao || "");
          return `<div class="tier-slot filled expandable" data-pick-slot data-kind="infusao-artificer" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}">
            <div class="slot-head">
              <span class="tal-nome">${escapeHtmlBare(p.Valor)}</span>
              ${badge}
              <span class="hab-pin tier-x" data-pick-slot-remove data-kind="infusao-artificer" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}" title="Remover">×</span>
            </div>
            <div class="slot-desc" data-collapsed="1">${escapeHtmlBare(desc)}</div>
          </div>`;
        }
        return `<div class="tier-slot empty" data-pick-slot data-kind="infusao-artificer" data-origem="${escapeHtmlBare(s.origem)}" data-slot="${s.idxLocal}">
          <i>Infusão ${globalIdx + 1} — clique para escolher (ou Replicar Item Mágico)</i>
        </div>`;
      }).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Infusões de Artificer <small class="tech-count">${infDone}/${infSlots.length}</small><small style="margin-left:8px;color:#5d4d2a">· Itens Infundidos ativos: ${itensInfMax} · inclui Replicar Item Mágico</small></h3>
          <div class="tech-slots-grid">${infHTML}</div>
        </div>`);
    }

    // ===== Técnicas de Furtividade — POOL ABERTO (read-only).
    // Não é picker. Todas as técnicas estão sempre disponíveis ao Ladino; o
    // jogador escolhe qual usar no momento do ataque pagando o custo em d6.
    // Section ativa quando aggregated_tags contém a flat tag 'tecnica-furtividade'.
    // Cada Trilha (subclass) adiciona uma técnica especial via subclass hab própria
    // (já renderizada na seção Habilidades de Subclasse).
    const hasTecnicaFurtividade = (state.aggregated_tags || []).some(t =>
      (typeof t === "object" && t.tag === "tecnica-furtividade") ||
      (typeof t === "string" && t === "tecnica-furtividade")
    );
    if (hasTecnicaFurtividade) {
      const tfCat = state.tecnicas_furtividade_catalogo || [];
      if (tfCat.length > 0) {
        // CD de Técnica: 8 + BP + Mod Destreza
        const profTF = profByLevel(state.personagem?.Nivel || 1);
        const dexModTF = mod(atrFinal(state, "Destreza"));
        const tfCD = 8 + profTF + dexModTF;
        const tfInfo = `<small style="margin-left:8px;color:#5d4d2a">· CD ${tfCD} · DES ${sgn(dexModTF)}</small>`;

        // Render: mesmas classes CSS do Guerreiro Manobras (tier-slot filled expandable).
        // Read-only — sem botão de remover, sem locked, sem picker. Pool aberto.
        const slotsHTML = tfCat.map(o => {
          const efeito = (o.Descricao || "").replace(/^\s*Custo:\s*\d+d6\.?\s*/, "");
          const custoBadge = `<small class="tal-grau">${escapeHtml(o.PreReqTexto || `Custo: ${o.NivelMinimo}d6`)}</small>`;
          return `<div class="tier-slot filled expandable" data-tf-slot>
            <div class="slot-head">
              <span class="tal-nome">${escapeHtml(o.Nome)}</span>
              ${custoBadge}
            </div>
            <div class="slot-desc" data-collapsed="1">${escapeHtml(efeito)}</div>
          </div>`;
        }).join("");

        el.insertAdjacentHTML("beforeend", `
          <div class="tech-list tech-slots">
            <h3>Técnicas de Furtividade <small class="tech-count">${tfCat.length}</small>${tfInfo}</h3>
            <div class="tech-slots-grid">${slotsHTML}</div>
          </div>`);
      }
    }

    // ===== Magia Expandida — derivada do Talento de Origem (read-only) =====
    // Apenas transcrição: estas magias ficam visíveis aqui, mas só são "aprendidas"
    // de fato quando o personagem as adquire via classe/subclasse de conjuração.
    const magiaExp = state.magia_expandida || [];
    if (magiaExp.length > 0) {
      // agrupa por fonte_lista
      const grupos = {};
      magiaExp.forEach(m => {
        const k = m.fonte_lista || "—";
        (grupos[k] = grupos[k] || []).push(m);
      });
      const blocosGrupo = Object.entries(grupos).map(([fonte, magias]) => `
        <div class="magia-exp-grupo">
          <div class="magia-exp-fonte">${escapeHtml(fonte)}</div>
          <ul class="magia-exp-lista">
            ${magias.map(m => `
              <li>
                <span class="magia-exp-nome">${escapeHtml(m.nome || "")}</span>
                ${m.nome_ingles ? `<small style="color:#888"> [${escapeHtml(m.nome_ingles)}]</small>` : ""}
              </li>`).join("")}
          </ul>
        </div>`).join("");
      // Fontes reais: dedup do __via_origem das magias listadas. Se vazio, fallback razoável.
      const fontesSet = new Set();
      magiaExp.forEach(m => { if (m.__via_origem) fontesSet.add(m.__via_origem); });
      const fontesList = Array.from(fontesSet);
      const fontesLabel = fontesList.length
        ? fontesList.map(f => `<em>${escapeHtml(f)}</em>`).join(", ")
        : `<em>${escapeHtml(state.talento_origem_extra?.Nome || state.talento_origem?.Nome || "—")}</em>`;
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list magia-exp-list">
          <h3>Magia Expandida <small class="tech-count">${magiaExp.length} listadas</small></h3>
          <div class="magia-exp-info"><small style="color:#555">
            Fonte: ${fontesLabel}.
            Estas magias são apenas transcrição do talento de origem.
            Para conjurar, você precisa aprendê-las via classe/subclasse de conjuração.
          </small></div>
          ${blocosGrupo}
        </div>`);
    }

    // ===== Magias ===== (só se classe for full/half OU subclasse for third)
    const classeConj   = state.classe?.Conjuracao;     // 'full' | 'half' | 'none'
    const subConj      = state.subclasse?.Conjuracao;  // 'third' | null
    // isSpellcaster: existe pra section Magias REGULAR. Místico puro NÃO tem
    // section regular (vai pra Feitiçaria Mística isolada). Quando classe primária
    // é Místico SEM outra caster classe, caster_level=0 (excluído) → não mostra.
    const isMisticoOnly = (state.classe?.Slug || "").toLowerCase() === "mistico"
                       && (state.caster_level || 0) === 0;
    const isSpellcaster = !isMisticoOnly
      && (classeConj === "full" || classeConj === "half" || subConj === "third");

    // Detecta Marca Potente (talento de classe ativo, não locked) — promove magia expandida.
    // Usa nivel_total (soma de TB_PersonagemClasse) em vez de TB_Personagem.Nivel,
    // que pode estar dessincronizado (mesmo bug do fix de patente em 2026-05-06).
    const nivelPers = state.nivel_total ?? state.personagem?.Nivel ?? 1;
    const temMarcaPotente = (state.talentos || []).some(t =>
      t.Categoria === "classe"
      && /marca potente/i.test(t.Nome || "")
      && (t.Nivel || 1) <= nivelPers
    );

    // Feitiçaria Mística (Místico) — flag pra trocar o título da section. Mesmo
    // pipeline de Magias normal (slots, preparadas, etc); só o nome muda.
    const hasFeiticariaMistica = (state.aggregated_tags || []).some(t => t && t.tag === "feiticaria-mistica");
    if ((isSpellcaster || temMarcaPotente) && !isMisticoOnly) {
      const byLv = {};
      for (const m of (state.magias || [])) (byLv[m.Nivel] ||= []).push(m);
      // injeta auto-efeitos da linhagem da essência (sempre disponíveis)
      const ae = state.auto_efeitos || {};
      if (ae.truque) (byLv[0] ||= []).push({ Nome: ae.truque + " ⟵ linhagem", Preparada: 1, __auto: 1 });
      if (ae.magia_n3) (byLv[1] ||= []).push({ Nome: ae.magia_n3 + " (1×/descanso longo ⟵ linhagem)", Preparada: 1, __auto: 1 });
      // Injeta magias **auto-preparadas** do Talento de Origem (do tipo "sempre tem X preparada"
      // na prosa do talento, ex.: Marca Arcana da Restauração concede Curar Ferimentos preparada).
      // NÃO mescla a "lista expandida" (Magias do Decreto) — essas só são auto-preparadas se o
      // personagem tiver o talento "Marca Potente" (talento-geral separado, ainda não detectado aqui).
      // Quando spell_level conhecido for null, default = 1.
      // O __via_origem vem do backend (set por magia, considera principal vs extra de Raízes).
      const SPELL_LEVELS = {
        // mapeamento mínimo de magias D&D 5.5 conhecidas → nível.
        // Estende quando aparecerem outras magias auto-preparadas em talentos.
        "curar ferimentos": 1, "cure wounds": 1,
        "restauração menor": 2, "lesser restoration": 2,
        "palavra curativa": 1, "healing word": 1,
        "raio de fogo": 0, "fire bolt": 0,
        "golpe incandescente": 1, "searing smite": 1,
      };
      const ptLevel = (m) => {
        const k1 = (m.nome_ingles || "").toLowerCase().trim();
        const k2 = (m.nome || "").toLowerCase().trim();
        if (k1 in SPELL_LEVELS) return SPELL_LEVELS[k1];
        if (k2 in SPELL_LEVELS) return SPELL_LEVELS[k2];
        return 1;  // fallback: assume 1° círculo
      };
      const nivelPersonagem = nivelPers;
      // Quando há Marca Potente, TODAS magias expandidas (incluindo "Magias do Decreto")
      // viram preparadas — não só as auto-preparadas explícitas da prosa.
      // Sem Marca Potente: só as marcadas auto_preparada do talento.
      // Auto-prep: itera DUAS fontes:
      //  - state.magia_expandida (talento de origem; afetada pelo "Marca Potente")
      //  - state.magias_subclasse (subclasse — sempre auto-prep, sem promoção)
      const lvMagiaCalc = (m) => {
        const fonteNum = parseInt(m.fonte_lista, 10);
        return (Number.isFinite(fonteNum) && fonteNum >= 0 && fonteNum <= 9)
          ? fonteNum : ptLevel(m);
      };
      for (const m of (state.magia_expandida || [])) {
        const isAuto = !!m.auto_preparada;
        const isPromoted = temMarcaPotente && !isAuto;
        if (!isAuto && !isPromoted) continue;
        const lvMagia = lvMagiaCalc(m);
        const viaOrigem = m.__via_origem || state.talento_origem?.Nome || "";
        const suffixPotente = isPromoted ? " (preparada via Marca Potente)" : "";
        const nomeFmt = `${m.nome}${m.nome_ingles ? ` [${m.nome_ingles}]` : ""} ⟵ ${viaOrigem}${suffixPotente}`;
        (byLv[lvMagia] ||= []).push({ Nome: nomeFmt, Preparada: 1, __via_origem: 1 });
      }
      // Subclasse: sempre auto-prep (Magias de Domínio/Juramento)
      for (const m of (state.magias_subclasse || [])) {
        if (!m.auto_preparada) continue;
        const lvMagia = lvMagiaCalc(m);
        const viaOrigem = m.__via_origem || "";
        const nomeFmt = `${m.nome}${m.nome_ingles ? ` [${m.nome_ingles}]` : ""} ⟵ ${viaOrigem}`;
        (byLv[lvMagia] ||= []).push({ Nome: nomeFmt, Preparada: 1, __via_origem: 1 });
      }
      // níveis exibidos: maior entre (slots da multiclasse) e (auto-prep mais alta).
      // Auto-prep não exige slot — a habilidade sempre prepara; a multiclasse dá o slot.
      // Então mesmo se um auto-prep tiver nível acima dos slots, a coluna deve aparecer.
      const slotsObj = state.spell_slots || {};
      const slotKeys = Object.keys(slotsObj).map(Number).filter(n => n > 0);
      const nivelPersAtual = state.personagem?.Nivel || 1;
      // autoPrepLevels: máx Nv de magia auto-prep entre (talento + subclasse).
      // Garante que a coluna apareça mesmo se não há slot daquele nível.
      const autoPrepLevels = [
        ...(state.magia_expandida || []).filter(m => m.auto_preparada),
        ...(state.magias_subclasse || []).filter(m => m.auto_preparada),
      ].map(m => parseInt(m.fonte_lista, 10))
       .filter(n => Number.isFinite(n) && n >= 1 && n <= 9);
      const maxFromSlots = slotKeys.length ? Math.max(...slotKeys) : 0;
      const maxFromAuto  = autoPrepLevels.length ? Math.max(...autoPrepLevels) : 0;
      // fallbackByConj só ativa quando NÃO tem slots reais nem auto-prep
      // (ex: char placeholder sem nivel ainda). Caso contrário, slots reais
      // mandam — Clérigo Nv 9 mostra até 5° círculo, não infla pra 9°.
      const fallbackByConj = (classeConj === "full" ? 9
            : classeConj === "half" ? 5
            : classeConj === "third" || subConj === "third" ? 4
            : 0);
      let maxLv = Math.max(maxFromSlots, maxFromAuto);
      if (maxLv === 0) maxLv = fallbackByConj;
      // Marca Potente: 1/3 caster ganha acesso a slot de magia da Marca até 5° nível
      // (metade do nível arredondado pra cima, cap 5). Para Frosty Nv16: 8 → cap 5.
      if (temMarcaPotente) {
        const halfLv = Math.min(5, Math.ceil(nivelPers / 2));
        maxLv = Math.max(maxLv, halfLv);
      }
      // Se não é caster mas tem Marca Potente, ainda mostra os níveis pra magia da Marca
      if (!isSpellcaster && temMarcaPotente && maxLv === 0) {
        maxLv = Math.min(5, Math.ceil(nivelPers / 2));
      }
      const levels = [];
      for (let i = 0; i <= maxLv; i++) levels.push(String(i));
      const grid = levels.map(lv => {
        const list = byLv[lv] || [];
        const items = list.map(m => {
          const removable = m.Id && !m.__auto && !m.__via_origem;
          const xBtn = removable
            ? `<span class="hab-pin tier-x spell-x" data-magia-remove="${m.Id}" title="Remover">×</span>`
            : "";
          const togglable = m.Id && !m.__auto && !m.__via_origem;
          const prepIcon = togglable
            ? `<span class="spell-prep-toggle" data-magia-toggle="${m.Id}" data-prep="${m.Preparada ? 1 : 0}" title="Toggle preparada">${m.Preparada ? "☑" : "☐"}</span>`
            : (m.Preparada ? "☑" : "☐");
          return `<li class="${m.Preparada ? "prep" : ""}">${prepIcon} ${escapeHtmlBare(m.Nome)} ${xBtn}</li>`;
        }).join("");
        return `
        <div class="spell-level">
          <h4>${lv === "0" ? "Truques" : `Nível ${lv}${slotsObj[lv] ? ` <small style="color:#888">(${slotsObj[lv]} slots)</small>` : ""}`}</h4>
          <ul>${items || `<li style="color:#bbb; font-style:italic;">—</li>`}
            <li class="spell-add" data-magia-add="${lv}"><i style="color:#888">+ adicionar</i></li>
          </ul>
        </div>`;
      }).join("");
      const tipoLabel = classeConj === "full" ? "Conjurador Pleno"
                      : classeConj === "half" ? "Meio-Conjurador"
                      : "Conjurador de Subclasse (1/3)";
      // Atributo de conjuração: hardcoded por slug de classe/subclasse (PHB 2024).
      // Permite calcular CD e ataque de magia automaticamente.
      const SPELLCAST_ATTR = {
        "mago": "Inteligencia",
        "feiticeiro": "Carisma",
        "bardo": "Carisma",
        "bruxo": "Carisma",
        "paladino": "Carisma",
        "mistico": "Carisma", "místico": "Carisma",
        "clerigo": "Sabedoria", "clérigo": "Sabedoria",
        "druida": "Sabedoria",
        "patrulheiro": "Sabedoria", "ranger": "Sabedoria", "cacador": "Sabedoria", "caçador": "Sabedoria",
        "artifice": "Inteligencia", "artífice": "Inteligencia",
        // subclasses 1/3 e psionicas
        "cavaleiro-arcano": "Inteligencia",
        "cavaleiro-das-sombras": "Inteligencia",
        "guerreiro-psionico": "Inteligencia",
        "ladino-arcano": "Inteligencia",
        "trapaceiro-arcano": "Inteligencia",
      };
      const slugClasse = (state.classe?.Slug || "").toLowerCase();
      const slugSub = (state.subclasse?.Slug || "").toLowerCase();
      const conjAttr = SPELLCAST_ATTR[slugSub] || SPELLCAST_ATTR[slugClasse] || "Inteligencia";
      const conjMod = mod(atrFinal(state, conjAttr));
      const cd = 8 + prof + conjMod;
      const ataque = prof + conjMod;
      const attrAbbr = { Forca:"FOR", Destreza:"DES", Constituicao:"CON", Inteligencia:"INT", Sabedoria:"SAB", Carisma:"CAR" }[conjAttr] || conjAttr;
      const cdInfo = `<small style="margin-left:8px;color:#5d4d2a">· CD ${cd} · Ataque ${sgn(ataque)} · ${attrAbbr} ${sgn(conjMod)}</small>`;
      el.insertAdjacentHTML("beforeend", `
        <div class="sec-label">Magias — ${tipoLabel}${cdInfo}</div>
        <div class="spell-grid">${grid}</div>`);
    } else {
      // mesmo sem ser conjurador, a linhagem da essência concede magias inatas
      const ae = state.auto_efeitos || {};
      if (ae.truque || ae.magia_n3) {
        el.insertAdjacentHTML("beforeend", `
          <div class="sec-label">Magias Inatas — ${ae.origem || ""}</div>
          <div class="spell-grid" style="grid-template-columns:repeat(2,1fr);">
            <div class="spell-level"><h4>Truque</h4><ul>
              <li class="prep">☑ ${ae.truque || "—"}</li>
            </ul></div>
            <div class="spell-level"><h4>Magia (nv 3+)</h4><ul>
              <li class="${ae.magia_n3 ? 'prep' : ''}">${ae.magia_n3 ? '☑ '+ae.magia_n3+' <small>(1×/descanso longo)</small>' : '<i>desbloqueia no nível 3</i>'}</li>
            </ul></div>
          </div>`);
      }
      if ((state.magias || []).length) {
        skips.push("Há magias cadastradas mas a classe/subclasse não é conjuradora — escondidas");
      }
    }

    // ===== Feitiçaria Mística — Sistema de Pontos de Misticismo (Bonfire).
    // NÃO usa slots fixos. Pontos convertem em slots: 1°=2pt · 2°=3pt · 3°=4pt · 4°=5pt · 5°=6pt.
    // Recupera em Descanso Curto OU Longo. Magias são CONHECIDAS (não preparadas).
    const fm = state.feiticaria_mistica;
    if (hasFeiticariaMistica && fm) {
      const carMod = mod(atrFinal(state, "Carisma"));
      const profFM = profByLevel(state.personagem?.Nivel || 1);
      const cdFM = 8 + profFM + carMod;
      const ataqueFM = profFM + carMod;
      const cdInfoFM = `<small style="margin-left:8px;color:#5d4d2a">· CD ${cdFM} · Ataque ${sgn(ataqueFM)} · CAR ${sgn(carMod)}</small>`;
      const conv = fm.conversao_pontos_slot || {};
      const tabelaPts = Object.keys(conv)
        .filter(k => parseInt(k, 10) <= (fm.ciclo_max || 0))
        .map(k => `<span style="display:inline-block;margin-right:10px"><b>${k}°</b>=${conv[k]}pt</span>`)
        .join("");
      // Magias (todas em state.magias por enquanto). Auto-preparadas via talento + subclasse incluídas.
      const magiasFM = (state.magias || []).slice();
      for (const m of (state.magia_expandida || [])) {
        const isAuto = !!m.auto_preparada;
        const isPromoted = temMarcaPotente && !isAuto;
        if (!isAuto && !isPromoted) continue;
        const fonteNum = parseInt(m.fonte_lista, 10);
        const lv = (Number.isFinite(fonteNum) && fonteNum >= 0 && fonteNum <= 9) ? fonteNum : 1;
        const viaOrigem = m.__via_origem || state.talento_origem?.Nome || "";
        const sufx = isPromoted ? " (Marca Potente)" : "";
        magiasFM.push({
          Nome: `${m.nome}${m.nome_ingles ? ` [${m.nome_ingles}]` : ""} ⟵ ${viaOrigem}${sufx}`,
          Nivel: lv, Preparada: 1, __via_origem: 1,
        });
      }
      for (const m of (state.magias_subclasse || [])) {
        if (!m.auto_preparada) continue;
        const fonteNum = parseInt(m.fonte_lista, 10);
        const lv = (Number.isFinite(fonteNum) && fonteNum >= 0 && fonteNum <= 9) ? fonteNum : 1;
        magiasFM.push({
          Nome: `${m.nome}${m.nome_ingles ? ` [${m.nome_ingles}]` : ""} ⟵ ${m.__via_origem || ""}`,
          Nivel: lv, Preparada: 1, __via_origem: 1,
        });
      }
      const byLvFM = {};
      for (const m of magiasFM) (byLvFM[m.Nivel] ||= []).push(m);
      // Mostra Truques + 1° até ciclo_max
      const niveisFM = [0];
      for (let i = 1; i <= (fm.ciclo_max || 0); i++) niveisFM.push(i);
      const cellFM = (lv) => {
        const list = (byLvFM[lv] || []).map(m => {
          const xBtn = m.Id ? `<span class="hab-pin tier-x spell-x" data-magia-remove="${m.Id}" title="Remover">×</span>` : "";
          return `<li class="prep">${escapeHtmlBare(m.Nome)} ${xBtn}</li>`;
        }).join("") || `<li style="color:#bbb;font-style:italic">—</li>`;
        const head = lv === 0
          ? `Truques <small style="color:#888">(${fm.truques_lim} conhecidos)</small>`
          : `${lv}° Ciclo <small style="color:#888">(${conv[lv] || "?"} pts)</small>`;
        return `<div class="spell-level"><h4>${head}</h4><ul>${list}
          <li class="spell-add" data-magia-add="${lv}"><i style="color:#888">+ adicionar</i></li>
        </ul></div>`;
      };
      const gridFM = niveisFM.map(cellFM).join("");
      el.insertAdjacentHTML("beforeend", `
        <div class="sec-label">Feitiçaria Mística — Místico Nv ${fm.nivel_mistico}${cdInfoFM}</div>
        <div style="background:#fff8ee;border:1px solid #d8c8a8;border-radius:4px;padding:6px 10px;margin:4px 0;font-size:12px">
          <b>Pontos de Misticismo:</b> ${fm.pontos_max} <small style="color:#888">(recupera em Descanso Curto/Longo)</small>
          · <b>Ciclo Máx:</b> ${fm.ciclo_max}°
          · <b>Magias Conhecidas:</b> ${fm.magias_lim}
          · <b>Truques:</b> ${fm.truques_lim}
          <div style="margin-top:4px;color:#666"><small><b>Conversão:</b> ${tabelaPts}</small></div>
        </div>
        <div class="spell-grid">${gridFM}</div>`);
    }

    root.innerHTML = "";
    root.appendChild(el);
    wireClicks();
  }

  // ---------- Wiring dos cliques ----------
  function wireClicks() {
    root.querySelectorAll("[data-pick]").forEach(elem => {
      elem.addEventListener("click", () => onPick(elem.dataset.pick, elem.dataset));
    });
    // Click numa linha de classe → editor (subclasse + nivel + remover)
    root.querySelectorAll('[data-pick-classe-row]').forEach(row => {
      row.addEventListener("click", async () => {
        const idPc = parseInt(row.dataset.idPc, 10);
        const c = (state.classes || []).find(x => x.Id_PersonagemClasse === idPc);
        if (!c) return;
        // Carrega subclasses dessa classe
        let subclasses = [];
        if (c.SlugClasse) {
          try { subclasses = await api.subclasses(c.SlugClasse); } catch { subclasses = []; }
        }
        // Cap: 20 menos soma das outras classes
        const outrasSomas = (state.classes || [])
          .filter(x => x.Id_PersonagemClasse !== idPc)
          .reduce((acc, x) => acc + (x.Nivel || 0), 0);
        const niveisMax = Math.max(1, 20 - outrasSomas);
        openClasseEditor({
          title: `Editar ${c.NomeClasse}`,
          classeAtual: { Id_Subclasse: c.Id_Subclasse, Nivel: c.Nivel },
          subclasses,
          niveisMax,
          ordem: c.Ordem,
          multiclassReq: c.MulticlassReqJSON,
          multiclassProf: c.MulticlassProfJSON,
          onSave: async (payload) => {
            await fetch(`/api/personagens/${pid}/classes/${idPc}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            await load();
          },
          onRemove: async () => {
            await fetch(`/api/personagens/${pid}/classes/${idPc}`, { method: "DELETE" });
            await load();
          },
        });
      });
    });
    // Click "+ adicionar classe" → fetch elegíveis (com prereq check) → editor
    root.querySelectorAll('[data-pick-classe-add]').forEach(btn => {
      btn.addEventListener("click", async () => {
        const elegiveis = await fetch(`/api/personagens/${pid}/classes-elegiveis`).then(r => r.json());
        const candidatas = elegiveis.filter(c => !c.ja_tem);
        if (!candidatas.length) {
          alert("Personagem já tem todas as classes disponíveis.");
          return;
        }
        openPicker({
          title: "Escolher classe (multiclasse — verifica prereqs)",
          options: candidatas,
          renderOption: (c) => {
            // formata prereq pra display
            let req = "";
            try {
              const r = c.MulticlassReqJSON ? JSON.parse(c.MulticlassReqJSON) : null;
              if (r && r.atribs) {
                const conector = (r.logica === "any") ? " ou " : " e ";
                req = `<small style="color:#888"> · ${r.atribs.map(a => `${a} ${r.min}+`).join(conector)}</small>`;
              }
            } catch {}
            const flag = c.elegivel
              ? '<span style="color:#2a6b1c">✓</span>'
              : `<span style="color:#a82626" title="${escapeHtmlBare(c.motivo || '')}">✗</span>`;
            const profs = c.MulticlassProfJSON ? JSON.parse(c.MulticlassProfJSON) : [];
            const profStr = profs.length
              ? `<br><small style="color:#666">Multi-prof: ${profs.map(escapeHtmlBare).join(", ")}</small>`
              : "";
            const motivoStr = !c.elegivel && c.motivo
              ? `<br><small style="color:#a82626">${escapeHtmlBare(c.motivo)}</small>`
              : "";
            return `${flag} <b>${escapeHtmlBare(c.Nome)}</b>${c.DadoVida ? ` <small>(${c.DadoVida})</small>` : ''}${req}${profStr}${motivoStr}`;
          },
          onPick: async (c) => {
            if (!c.elegivel) {
              if (!confirm(`Esta classe não atende os prereqs:\n${c.motivo}\n\nAdicionar mesmo assim? (Force=true)`)) {
                return;
              }
            }
            // Após escolher classe, abre o editor pra subclasse + nivel
            let subclasses = [];
            try { subclasses = await api.subclasses(c.Slug); } catch { subclasses = []; }
            const outrasSomas = (state.classes || []).reduce((acc, x) => acc + (x.Nivel || 0), 0);
            const niveisMax = Math.max(1, 20 - outrasSomas);
            openClasseEditor({
              title: `Adicionar ${c.Nome}`,
              classeAtual: { Id_Subclasse: null, Nivel: 1 },
              subclasses,
              niveisMax,
              ordem: (state.classes || []).length,  // próxima ordem = num atuais
              multiclassReq: c.MulticlassReqJSON,
              multiclassProf: c.MulticlassProfJSON,
              onSave: async (payload) => {
                const r = await fetch(`/api/personagens/${pid}/classes`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    Id_Classe: c.Id_Classe,
                    Id_Subclasse: payload.Id_Subclasse,
                    Nivel: payload.Nivel,
                    Force: !c.elegivel,  // se já confirmou no prompt, força
                  }),
                });
                if (!r.ok) {
                  const err = await r.json().catch(() => ({}));
                  alert(`Erro: ${err.error || 'falhou ao adicionar'}\n${(err.motivos || []).join('\\n')}`);
                  return;
                }
                await load();
              },
              // sem onRemove — ainda nem foi adicionada
            });
          },
        });
      });
    });
    // Patente Lenda — monta toon fire shader (Three.js) no canvas
    const toonFireEl = root.querySelector('[data-toon-fire="1"]');
    if (toonFireEl) {
      mountToonFire(toonFireEl).catch(err => console.error("Toon fire falhou:", err));
    } else if (_toonFireCleanup) {
      // Sai do estado Lenda → limpa renderer
      try { _toonFireCleanup(); } catch (e) {}
      _toonFireCleanup = null;
    }
    // Patente Lv 20 — clique cicla Rubi → Diamante → Lenda → Rubi
    root.querySelectorAll('[data-patente-cycle="1"]').forEach(el => {
      el.addEventListener("click", async () => {
        const cycle = ["Rubi", "Diamante", "Lenda"];
        const atual = state.personagem?.Patente || "Rubi";
        const idx = cycle.indexOf(atual);
        const next = cycle[(idx + 1) % cycle.length];
        await fetch(`/api/personagens/${pid}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ Patente: next }),
        });
        await load();
      });
    });
    // slots vazios de técnicas/manobras → abre picker
    root.querySelectorAll("[data-pick-tecnica-slot]").forEach(slot => {
      slot.addEventListener("click", async () => {
        openTecnicasModal();
      });
    });
    // slots vazios de Segredos → abre picker
    root.querySelectorAll("[data-pick-segredo-slot]").forEach(slot => {
      slot.addEventListener("click", async () => {
        openSegredosModal();
      });
    });
    // slot preenchido de Segredo → expand/collapse descrição
    root.querySelectorAll("[data-segredo-slot]").forEach(slot => {
      slot.addEventListener("click", (e) => {
        if (e.target.closest("[data-segredo-remove]")) return;
        const desc = slot.querySelector(".slot-desc");
        if (!desc) return;
        const collapsed = desc.dataset.collapsed === "1";
        desc.dataset.collapsed = collapsed ? "0" : "1";
        desc.style.display = collapsed ? "" : "none";
      });
    });
    // X de remover Segredo
    root.querySelectorAll("[data-segredo-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const sid = btn.dataset.segredoRemove;
        if (!sid) return;
        if (!confirm("Remover este segredo?")) return;
        await fetch(`/api/personagens/${pid}/segredos/${sid}`, { method: "DELETE" });
        await load();
      });
    });
    // slots vazios de Inimigo Favorito → abre picker
    root.querySelectorAll("[data-pick-inimigo-slot]").forEach(slot => {
      slot.addEventListener("click", async () => {
        openInimigosFavoritosModal();
      });
    });
    // X de remover Inimigo Favorito
    root.querySelectorAll("[data-inimigo-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const iid = btn.dataset.inimigoRemove;
        if (!iid) return;
        if (!confirm("Remover este inimigo favorito?")) return;
        await fetch(`/api/personagens/${pid}/inimigos-favoritos/${iid}`, { method: "DELETE" });
        await load();
      });
    });
    // slots vazios de Evolução Totêmica → abre picker filtrado por tier
    root.querySelectorAll("[data-pick-evolucao-slot]").forEach(slot => {
      slot.addEventListener("click", async () => {
        openEvolucaoTotemicaModal(slot.dataset.tierMax || "menor");
      });
    });
    // slot preenchido de Evolução → expand/collapse descrição
    root.querySelectorAll("[data-evolucao-slot]").forEach(slot => {
      slot.addEventListener("click", (e) => {
        if (e.target.closest("[data-evolucao-remove]")) return;
        const desc = slot.querySelector(".slot-desc");
        if (!desc) return;
        const collapsed = desc.dataset.collapsed === "1";
        desc.dataset.collapsed = collapsed ? "0" : "1";
        desc.style.display = collapsed ? "" : "none";
      });
    });
    // X de remover Evolução Totêmica
    root.querySelectorAll("[data-evolucao-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const eid = btn.dataset.evolucaoRemove;
        if (!eid) return;
        if (!confirm("Remover esta evolução totêmica?")) return;
        await fetch(`/api/personagens/${pid}/evolucoes-totemicas/${eid}`, { method: "DELETE" });
        await load();
      });
    });
    // Estilo de Ki — pick / expand / remove
    root.querySelectorAll("[data-pick-estilo-ki-slot]").forEach(slot => {
      slot.addEventListener("click", async () => { openEstiloKiModal(); });
    });
    root.querySelectorAll("[data-estilo-ki-slot]").forEach(slot => {
      slot.addEventListener("click", (e) => {
        if (e.target.closest("[data-estilo-ki-remove]")) return;
        const desc = slot.querySelector(".slot-desc");
        if (!desc) return;
        const collapsed = desc.dataset.collapsed === "1";
        desc.dataset.collapsed = collapsed ? "0" : "1";
        desc.style.display = collapsed ? "" : "none";
      });
    });
    root.querySelectorAll("[data-estilo-ki-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const eid = btn.dataset.estiloKiRemove;
        if (!eid) return;
        if (!confirm("Remover este estilo de ki?")) return;
        await fetch(`/api/personagens/${pid}/estilos-ki/${eid}`, { method: "DELETE" });
        await load();
      });
    });
    // Segredos Místicos — pick / expand / remove
    root.querySelectorAll("[data-pick-segredo-mistico-slot]").forEach(slot => {
      slot.addEventListener("click", async () => { openSegredoMisticoModal(); });
    });
    root.querySelectorAll("[data-segredo-mistico-slot]").forEach(slot => {
      slot.addEventListener("click", (e) => {
        if (e.target.closest("[data-segredo-mistico-remove]")) return;
        const desc = slot.querySelector(".slot-desc");
        if (!desc) return;
        const c = desc.dataset.collapsed === "1";
        desc.dataset.collapsed = c ? "0" : "1";
        desc.style.display = c ? "" : "none";
      });
    });
    root.querySelectorAll("[data-segredo-mistico-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const sid = btn.dataset.segredoMisticoRemove;
        if (!sid) return;
        if (!confirm("Remover este segredo místico?")) return;
        await fetch(`/api/personagens/${pid}/segredos-misticos/${sid}`, { method: "DELETE" });
        await load();
      });
    });
    // Botões "+ Idioma"/"+ Ferramenta" da section Aprendidos
    root.querySelectorAll("[data-aprend-add]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const tipo = btn.dataset.aprendAdd;  // 'idioma' ou 'ferramenta'
        const catalog = await fetchCatalogo(tipo);
        const ja = new Set(
          (state.idiomas || [])
            .filter(i => i.Tipo === tipo)
            .map(i => (i.Nome || "").toLowerCase())
        );
        const options = catalog
          .filter(n => !ja.has(n.toLowerCase()))
          .map(n => ({ Nome: n }));
        options.push({ Nome: "__custom__", __label: "+ Outro (digitar nome)…" });
        if (!options.length) { alert(`Sem ${tipo}s disponíveis.`); return; }
        openPicker({
          title: `Aprender ${tipo}`,
          options,
          renderOption: (o) => o.__label
            ? `<i>${escapeHtmlBare(o.__label)}</i>`
            : `<b>${escapeHtmlBare(o.Nome)}</b>`,
          onPick: async (o) => {
            let nome = o.Nome;
            if (nome === "__custom__") {
              nome = (prompt(`Digite o nome do ${tipo}:`) || "").trim();
              if (!nome) return;
            }
            await fetch(`/api/personagens/${pid}/aprendidos`, {
              method: "POST", headers: {"Content-Type":"application/json"},
              body: JSON.stringify({ tipo, nome }),
            });
            await load();
          },
        });
      });
    });
    // X de remover entrada de "Aprendidos"
    root.querySelectorAll("[data-aprend-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const iid = btn.dataset.aprendRemove;
        if (!iid) return;
        if (!confirm("Remover este aprendizado?")) return;
        await fetch(`/api/personagens/${pid}/idiomas/${iid}`, { method: "DELETE" });
        await load();
      });
    });
    // (fetchCatalogo agora vive no escopo wrapper — visível também por pickBackground.)

    // X de remover qualquer pick (vem antes do click no slot pra evitar bubble)
    root.querySelectorAll("[data-pick-slot-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const kind = btn.dataset.kind;
        const origem = btn.dataset.origem;
        const slot = btn.dataset.slot;
        if (!kind || !origem || slot === undefined) return;
        let url;
        if (kind === "pericia" || kind === "expertise") {
          // ambos usam TB_PersonagemEscolhaPericia; distinguidos por Tipo
          url = `/api/personagens/${pid}/escolhas-pericia/${encodeURIComponent(origem)}/${slot}`;
        } else if (kind === "idioma" || kind === "ferramenta") {
          url = `/api/personagens/${pid}/escolhas-idioma/${encodeURIComponent(origem)}/${slot}`;
        } else {
          // tipo genérico → TB_PersonagemEscolhaTag
          url = `/api/personagens/${pid}/escolhas-tag/${encodeURIComponent(origem)}/${encodeURIComponent(kind)}/${slot}`;
        }
        await fetch(url, { method: "DELETE" });
        await load();
      });
    });

    // Slot vazio (ou click no filled fora do X) → abre picker apropriado
    root.querySelectorAll("[data-pick-slot]").forEach(slot => {
      slot.addEventListener("click", async (e) => {
        if (e.target.closest("[data-pick-slot-remove]")) return;
        // Impede que o click bubble pro tier-slot pai (que abriria o picker
        // racial/essência/classe). Pick-slot inline (ex: pick:talento-geral:1
        // dentro do card do Multi-talentoso) deve ser auto-suficiente.
        e.stopPropagation();
        const kind = slot.dataset.kind;
        const origem = slot.dataset.origem;
        const slotIdx = parseInt(slot.dataset.slot, 10);

        if (kind === "pericia" || kind === "expertise") {
          // pick:pericia:N → escolhe perícias pra proficiência (filtra perícias SEM prof)
          // pick:expertise:N → escolhe perícias pra expertise (filtra perícias JÁ proficientes)
          // Mesmo storage (TB_PersonagemEscolhaPericia), distinguidos por Tipo no POST.
          const isExpertise = kind === "expertise";
          const tipoPick = isExpertise ? "expertise" : "proficiencia";
          const jaEscolhidas = new Set(
            (state.escolhas_pericia || [])
              .filter(es => es.Origem === origem && es.SlotIndex !== slotIdx)
              .map(es => es.Id_Pericia)
          );
          const filterRaw = slot.dataset.filterList || "";
          const allowList = filterRaw
            ? new Set(filterRaw.split("|").map(s => s.trim().toLowerCase()).filter(Boolean))
            : null;
          const candidates = (state.pericias || []).filter(p => {
            if (jaEscolhidas.has(p.Id_Pericia)) return false;
            if (isExpertise) {
              if (!p.Proficiente) return false;
              if (p.Expertise) return false;
            } else {
              if (p.Proficiente || p.Expertise) return false;
            }
            if (allowList && !allowList.has((p.Nome || "").trim().toLowerCase())) return false;
            return true;
          });
          if (!candidates.length) {
            alert(isExpertise
              ? "Não há perícias proficientes disponíveis para expertise."
              : "Não há perícias disponíveis.");
            return;
          }
          openPicker({
            title: `Escolher ${isExpertise ? "expertise" : "perícia"} (slot ${slotIdx+1} de ${origem})`,
            options: candidates,
            renderOption: (p) => {
              const sufix = isExpertise ? " — prof. atual" : "";
              return `<b>${escapeHtmlBare(p.Nome)}</b> <small>(${p.Atributo})${sufix}</small>`;
            },
            onPick: async (p) => {
              await fetch(`/api/personagens/${pid}/escolhas-pericia`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ origem, slot: slotIdx, id_pericia: p.Id_Pericia, tipo: tipoPick }),
              });
              await load();
            },
          });
        } else if (kind === "texto") {
          // Escolha finita: filter vira lista de sugestões.
          // - Se HÁ filter → modo ESTRITO (apenas as opções do filter, sem "Outro")
          // - Se NÃO há filter → modo livre (só "+ Outro (digitar)" com maxlen)
          // Regra do projeto: tag presente define o comportamento, sem campo extra.
          // data-pick-descricoes: opcional, lookup {opcao: texto} pra mostrar info
          // sob cada opção no picker (ex: cada Lua + magias que concede).
          const filterRaw = slot.dataset.filterList || "";
          const sugestoes = filterRaw ? filterRaw.split("|").map(s => s.trim()).filter(Boolean) : [];
          const strict = sugestoes.length > 0;
          const maxlen = parseInt(slot.dataset.maxlen, 10) || 30;
          let descricoesLookup = {};
          try {
            descricoesLookup = JSON.parse(slot.dataset.pickDescricoes || "{}") || {};
          } catch {}
          const jaEscolhidos = new Set(
            (state.escolhas_tag || [])
              .filter(es => es.Origem === origem && es.Tipo === kind && es.SlotIndex !== slotIdx)
              .map(es => (es.Valor || "").toLowerCase())
          );
          const options = sugestoes
            .filter(s => !jaEscolhidos.has(s.toLowerCase()))
            .map(s => ({ Nome: s, __info: descricoesLookup[s] || "" }));
          if (!strict) {
            options.push({ Nome: "__custom__", __label: `+ Outro (digitar, max ${maxlen})…` });
          }
          openPicker({
            title: `Escolher (slot ${slotIdx+1} de ${origem})`,
            options,
            renderOption: (o) => {
              if (o.__label) return `<i>${escapeHtmlBare(o.__label)}</i>`;
              const info = o.__info
                ? `<div class="picker-desc">${escapeHtmlBare(o.__info)}</div>`
                : "";
              return `<b>${escapeHtmlBare(o.Nome)}</b>${info}`;
            },
            onPick: async (o) => {
              let valor = o.Nome;
              if (valor === "__custom__") {
                valor = (prompt(`Digite (até ${maxlen} caracteres):`) || "").trim();
                if (!valor) return;
                if (valor.length > maxlen) valor = valor.slice(0, maxlen);
              }
              await fetch(`/api/personagens/${pid}/escolhas-tag`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  origem, tipo: kind, slot_index: slotIdx, valor,
                }),
              });
              await load();
            },
          });
        } else if (kind === "idioma" || kind === "ferramenta") {
          // união(catálogo DB, idiomas/ferramentas já no DB do personagem) — endpoint faz upsert
          const catalog = await fetchCatalogo(kind);
          const existing = (state.idiomas || [])
            .filter(x => x.Tipo === kind)
            .map(x => x.Nome)
            .filter(Boolean);
          // exclui Comum (idioma default) — não pode ser escolhido como pick
          const banned = new Set(["comum", "common"]);
          const jaEscolhidosOutros = new Set(
            (state.escolhas_idioma || [])
              .filter(es => es.Origem === origem && es.Tipo === kind && es.SlotIndex !== slotIdx)
              .map(es => (es.Nome || '').toLowerCase())
          );
          const allNames = new Set();
          for (const n of catalog) allNames.add(n);
          for (const n of existing) allNames.add(n);
          const options = Array.from(allNames)
            .filter(n => !banned.has(n.toLowerCase()) && !jaEscolhidosOutros.has(n.toLowerCase()))
            .sort((a,b) => a.localeCompare(b, "pt"))
            .map(n => ({ Nome: n }));
          // sempre adiciona "+ Outro (digitar)" como última opção
          options.push({ Nome: "__custom__", __label: "+ Outro (digitar nome)…" });
          openPicker({
            title: `Escolher ${kind} (slot ${slotIdx+1} de ${origem})`,
            options,
            renderOption: (o) => o.__label ? `<i>${escapeHtmlBare(o.__label)}</i>` : `<b>${escapeHtmlBare(o.Nome)}</b>`,
            onPick: async (o) => {
              let nome = o.Nome;
              if (nome === "__custom__") {
                nome = (prompt(`Digite o nome do ${kind}:`) || "").trim();
                if (!nome) return;
              }
              await fetch(`/api/personagens/${pid}/escolhas-idioma`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ origem, slot: slotIdx, tipo: kind, nome }),
              });
              await load();
            },
          });
        } else if (kind === "estilo-danca") {
          // Estilos de Dança (Bardo da Dança) — pool = estilos_danca_catalogo
          // (reuso TB_EstiloKi.Catalogo='ki', já pré-carregado no /full).
          // NÃO está em TB_OpcaoJogo, então não dá pra usar /api/opcoes.
          const jaEscolhidos = new Set(
            (state.escolhas_tag || [])
              .filter(es => es.Origem === origem && es.Tipo === "estilo-danca" && es.SlotIndex !== slotIdx)
              .map(es => (es.Valor || "").toLowerCase())
          );
          const candidates = (state.estilos_danca_catalogo || []).filter(o =>
            !jaEscolhidos.has((o.Nome || "").toLowerCase())
          );
          if (!candidates.length) {
            alert("Sem Estilos de Dança disponíveis (todos já escolhidos).");
            return;
          }
          openPicker({
            title: `Escolher Estilo de Dança (slot ${slotIdx+1})`,
            options: candidates,
            renderOption: (o) => {
              // Lê custo "Ki" como "Inspiração Bárdica" (cosmético)
              const custo = o.NivelMinimo ? `<small> — ${o.NivelMinimo} Insp. Bárdica</small>` : "";
              const txt = (o.Descricao || "")
                .replace(/(\d+)\s*ponto[s]? de Ki/gi, "$1 uso de Inspiração Bárdica")
                .replace(/\bKi\b/g, "Inspiração Bárdica");
              const desc = txt ? `<div class="picker-desc">${escapeHtmlBare(String(txt).slice(0, 220))}${txt.length > 220 ? "…" : ""}</div>` : "";
              return `<b>${escapeHtmlBare(o.Nome)}</b>${custo}${desc}`;
            },
            onPick: async (o) => {
              await fetch(`/api/personagens/${pid}/escolhas-tag`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  origem, tipo: "estilo-danca", slot_index: slotIdx, valor: o.Nome,
                }),
              });
              await load();
            },
          });
        } else if (kind === "infusao-artificer") {
          // Infusões de Artificer — pool = infusoes_artificer_catalogo (pré-carregado).
          // Cada slot recebe (a) uma infusão filtrada por NivelMinimo <= nível
          // do Artífice, ou (b) um item mágico Replicado (selecionado/escrito
          // da página de equipamentos). Replica é tratada como infusão.
          const artC = (state.classes || []).find(c =>
            (c.SlugClasse || c.NomeClasse || "").toLowerCase().includes("artif"));
          const nivelArt = artC ? (artC.Nivel || 0) : (state.nivel_total || 0);
          const jaEscolhidas = new Set(
            (state.escolhas_tag || [])
              .filter(es => es.Tipo === "infusao-artificer" &&
                            !(es.Origem === origem && es.SlotIndex === slotIdx))
              .map(es => (es.Valor || "").toLowerCase())
          );
          const REPLICAR = { __replicar: true, Nome: "🔧 Replicar Item Mágico…" };
          const candidates = [REPLICAR].concat(
            (state.infusoes_artificer_catalogo || []).filter(o =>
              (o.NivelMinimo || 1) <= nivelArt &&
              !jaEscolhidas.has((o.Nome || "").toLowerCase())
            )
          );
          openPicker({
            title: `Escolher Infusão (slot ${slotIdx+1}) — Artífice Nv ${nivelArt}`,
            options: candidates,
            renderOption: (o) => {
              if (o.__replicar) {
                return `<b><i>${escapeHtmlBare(o.Nome)}</i></b><div class="picker-desc">Substitui uma infusão por um item mágico da página de equipamentos (Comum Nv2, Incomum Nv6, Raro Nv14; sem consumíveis).</div>`;
              }
              const restr = (o.NivelMinimo || 1) > 1 ? `<small> — Nv ${o.NivelMinimo}+</small>` : "";
              const txt = o.Descricao || "";
              const desc = txt ? `<div class="picker-desc">${escapeHtmlBare(String(txt).slice(0, 200))}${txt.length > 200 ? "…" : ""}</div>` : "";
              return `<b>${escapeHtmlBare(o.Nome)}</b>${restr}${desc}`;
            },
            onPick: async (o) => {
              if (o.__replicar) {
                // 2º picker: itens da página de equipamentos (busca + digitar livre)
                let itens = [];
                try {
                  itens = await fetch(`/api/items?limit=200`).then(r => r.ok ? r.json() : []);
                } catch {}
                const opts = (Array.isArray(itens) ? itens : []).map(it => ({
                  Nome: it.NomeTraduzido || it.Nome, _raw: it,
                }));
                opts.unshift({ Nome: "__custom__", __label: "+ Digitar nome do item…" });
                openPicker({
                  title: "Replicar Item Mágico — selecione da página de equipamentos",
                  options: opts,
                  renderOption: (it) => it.__label
                    ? `<i>${escapeHtmlBare(it.__label)}</i>`
                    : `<b>${escapeHtmlBare(it.Nome)}</b>`,
                  onPick: async (it) => {
                    let nome = it.Nome;
                    if (nome === "__custom__") {
                      nome = (prompt("Nome do item mágico replicado:") || "").trim();
                      if (!nome) return;
                    }
                    await fetch(`/api/personagens/${pid}/escolhas-tag`, {
                      method: "POST", headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ origem, tipo: "infusao-artificer", slot_index: slotIdx, valor: `Replicar: ${nome}` }),
                    });
                    await load();
                  },
                });
                return;
              }
              await fetch(`/api/personagens/${pid}/escolhas-tag`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ origem, tipo: "infusao-artificer", slot_index: slotIdx, valor: o.Nome }),
              });
              await load();
            },
          });
        } else {
          // ===== TIPO GENÉRICO (estilo-de-luta, maestria-arma, talento-geral, etc.) =====
          // Fonte de candidatos: GET /api/opcoes?tipo=<kind>. Filter via data-filter-list.
          const filterRaw = slot.dataset.filterList || "";
          const allowList = filterRaw
            ? new Set(filterRaw.split("|").map(s => s.trim().toLowerCase()).filter(Boolean))
            : null;
          // já-escolhidos em outros slots da mesma origem+tipo (pra não repetir)
          const jaEscolhidos = new Set(
            (state.escolhas_tag || [])
              .filter(es => es.Origem === origem && es.Tipo === kind && es.SlotIndex !== slotIdx)
              .map(es => (es.Valor || "").toLowerCase())
          );
          fetch(`/api/opcoes?tipo=${encodeURIComponent(kind)}`)
            .then(r => r.ok ? r.json() : [])
            .then(opcoes => {
              const candidates = (opcoes || []).filter(o => {
                if (jaEscolhidos.has((o.Nome || "").toLowerCase())) return false;
                if (allowList && !allowList.has((o.Nome || "").toLowerCase())) return false;
                return true;
              });
              if (!candidates.length) {
                alert(`Sem opções disponíveis pra "${kind}" (catálogo vazio ou todas já escolhidas).`);
                return;
              }
              openPicker({
                title: `Escolher ${kind} (slot ${slotIdx+1} de ${origem})`,
                options: candidates,
                renderOption: (o) => {
                  const desc = o.Descricao ? `<div class="picker-desc">${escapeHtmlBare(String(o.Descricao).slice(0, 220))}${(o.Descricao||"").length > 220 ? "…" : ""}</div>` : "";
                  return `<b>${escapeHtmlBare(o.Nome)}</b>${desc}`;
                },
                onPick: async (o) => {
                  await fetch(`/api/personagens/${pid}/escolhas-tag`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      origem, tipo: kind, slot_index: slotIdx, valor: o.Nome,
                    }),
                  });
                  await load();
                },
              });
            })
            .catch(err => {
              console.error("erro buscando opcoes", kind, err);
              alert(`Erro ao buscar catálogo de "${kind}".`);
            });
        }
      });
    });
    // slots preenchidos de técnicas → click toggle expand description
    root.querySelectorAll("[data-tecnica-slot]").forEach(slot => {
      slot.addEventListener("click", (e) => {
        if (e.target.closest("[data-tecnica-remove]")) return;
        const desc = slot.querySelector(".slot-desc");
        if (desc) {
          const c = desc.dataset.collapsed === "1";
          desc.dataset.collapsed = c ? "0" : "1";
        }
      });
    });
    // Técnicas de Furtividade (pool aberto, read-only): mesmo toggle expand/collapse
    root.querySelectorAll("[data-tf-slot]").forEach(slot => {
      slot.addEventListener("click", () => {
        const desc = slot.querySelector(".slot-desc");
        if (desc) {
          const c = desc.dataset.collapsed === "1";
          desc.dataset.collapsed = c ? "0" : "1";
        }
      });
    });
    // X button → remove
    root.querySelectorAll("[data-tecnica-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const tid = btn.dataset.tecnicaRemove;
        if (!tid) return;
        if (!confirm("Remover esta manobra?")) return;
        await fetch(`/api/personagens/${pid}/tecnicas/${tid}`, { method: "DELETE" });
        await load();
      });
    });

    // slot de Talento de Origem (principal, extra de Raízes, racial de traço)
    const ORIGEM_FIELD = {
      principal: "Id_TalentoOrigem",
      extra:     "Id_TalentoOrigemExtra",
      racial:    "Id_TalentoOrigemRacial",
    };
    const ORIGEM_LABEL = {
      principal: "Talento de Origem",
      extra:     "Talento Extra (Raízes)",
      racial:    "Talento de Origem (racial)",
    };
    root.querySelectorAll("[data-pick-talento-origem-slot]").forEach(slot => {
      slot.addEventListener("click", async (e) => {
        // Defesa em profundidade: ignora cliques que vieram de slots/badges internos
        // (pick:texto, pick:talento-geral inline, aumento-pick, etc.) — esses já têm
        // handlers próprios + stopPropagation.
        if (e.target.closest("[data-pick-slot]") || e.target.closest("[data-pick-slot-remove]")) return;
        if (e.target.closest("[data-aumento-pick]") || e.target.closest("[data-vontade-pick]")) return;
        const kind = slot.dataset.kind || "principal";
        const fieldName = ORIGEM_FIELD[kind] || "Id_TalentoOrigem";
        if (slot.classList.contains("feat-card")) {
          // já preenchido — confirma remover OU re-pick
          const choice = confirm(`Remover ${ORIGEM_LABEL[kind] || "Talento"}? OK pra remover, Cancel pra trocar.`);
          if (choice) {
            await api.patch({ [fieldName]: null });
            await load();
          } else {
            await pickTalentoOrigem(kind);
          }
          return;
        }
        await pickTalentoOrigem(kind);
      });
    });

    // Sub-slot Talento de Origem dentro de instância de Segredo Místico (Aprendizado dos Antigos).
    // Cada instância (psm.Id) tem seu próprio talento associado — endpoint dedicado.
    root.querySelectorAll("[data-pick-talento-origem-segredo]").forEach(slot => {
      slot.addEventListener("click", async (e) => {
        e.stopPropagation();
        const sid = slot.dataset.sid;
        if (!sid) return;
        if (slot.classList.contains("feat-card")) {
          const choice = confirm("Remover Talento de Origem deste Segredo? OK pra remover, Cancel pra trocar.");
          if (choice) {
            await fetch(`/api/personagens/${pid}/segredos-misticos/${sid}/talento-origem`, {
              method: "POST", headers: {"Content-Type":"application/json"},
              body: JSON.stringify({ id_talento_origem: null }),
            });
            await load();
          } else {
            await pickTalentoOrigemSegredo(sid);
          }
          return;
        }
        await pickTalentoOrigemSegredo(sid);
      });
    });

    // Magias: adicionar (texto livre), remover (X), toggle preparada
    root.querySelectorAll("[data-magia-add]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const lv = parseInt(btn.dataset.magiaAdd, 10);
        const nome = prompt(`Nova magia ${lv === 0 ? "(Truque)" : `de Nível ${lv}`}:`);
        if (!nome || !nome.trim()) return;
        await fetch(`/api/personagens/${pid}/magias`, {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ nivel: lv, nome: nome.trim(), preparada: 1 }),
        });
        await load();
      });
    });
    root.querySelectorAll("[data-magia-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const mid = btn.dataset.magiaRemove;
        if (!mid) return;
        if (!confirm("Remover esta magia?")) return;
        await fetch(`/api/personagens/${pid}/magias/${mid}`, { method: "DELETE" });
        await load();
      });
    });
    root.querySelectorAll("[data-magia-toggle]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const mid = btn.dataset.magiaToggle;
        const wasPrep = btn.dataset.prep === "1";
        await fetch(`/api/personagens/${pid}/magias/${mid}`, {
          method: "PUT",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ preparada: wasPrep ? 0 : 1 }),
        });
        await load();
      });
    });

    // slot vazio de maestria → cascade picker
    root.querySelectorAll("[data-pick-maestria-slot]").forEach(slot => {
      slot.addEventListener("click", async () => {
        const slotIdx = parseInt(slot.dataset.slotIndex, 10);
        await pickMaestriaArma(slotIdx);
      });
    });
    // slot preenchido de maestria → click toggle expand
    root.querySelectorAll("[data-maestria-slot]").forEach(slot => {
      slot.addEventListener("click", (e) => {
        if (e.target.closest("[data-maestria-remove]")) return;
        const desc = slot.querySelector(".slot-desc");
        if (desc) {
          const c = desc.dataset.collapsed === "1";
          desc.dataset.collapsed = c ? "0" : "1";
        }
      });
    });
    // X button → remove maestria
    root.querySelectorAll("[data-maestria-remove]").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const slotIdx = parseInt(btn.dataset.maestriaRemove, 10);
        if (!Number.isFinite(slotIdx)) return;
        if (!confirm("Remover essa maestria?")) return;
        await fetch(`/api/personagens/${pid}/maestrias-armas/${slotIdx}`, { method: "DELETE" });
        await load();
      });
    });

    // slots de opcao de habilidade (picker catalogo-backed)
    // cards de habilidade clicáveis — apenas arquétipo (subclasse picker).
    // OpcaoTipoJSON-based pickers foram removidos em R3 — tag-based via [data-pick-slot].
    root.querySelectorAll(".feat-card[data-has-choice='1']").forEach(elem => {
      elem.addEventListener("click", async () => {
        if (elem.dataset.kind !== "arquetipo") return;
        return pickSubclasse();      // cascata: abre picker das subclasses
      });
    });

    // Aumento de Atributo: clique em botão = adiciona à seleção; clique em badge = limpa tudo.
    root.querySelectorAll("[data-aumento-pick]").forEach(elem => {
      elem.addEventListener("click", async (e) => {
        e.stopPropagation();
        e.preventDefault();
        const tid = elem.dataset.tid;
        if (!tid) return;
        const card = elem.closest("[data-pick-tier]");
        if (card?.dataset.locked === "1") {
          alert("Slot locked — bonus não aplica até o personagem atingir esse nível.");
          return;
        }
        const tal = (state.talentos || []).find(t => String(t.Id_Talento) === String(tid));
        const picks = tal?.AumentoSpec?.picks || 1;
        const escolhidas = (tal?.AumentoAtributo || "").toLowerCase().split(",").filter(Boolean);

        let novaCSV = null;
        const attr = elem.dataset.attr;
        if (attr) {
          // botão clicado — adiciona ao CSV se há slots livres (repetir é OK)
          if (escolhidas.length >= picks) {
            alert(`Limite de ${picks} atributo(s) atingido. Clique num badge pra trocar.`);
            return;
          }
          novaCSV = [...escolhidas, attr].join(",");
        } else {
          // badge clicada — confirma limpar (depois usuário escolhe de novo)
          if (!confirm("Limpar a(s) escolha(s) de atributo deste talento?")) return;
          novaCSV = null;
        }

        await fetch(`/api/personagens/${pid}/talentos/${tid}/aumento-atributo`, {
          method: "PUT",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ atributo: novaCSV }),
        });
        await load();
      });
    });

    // save-prof-vontade picker inline — botão attr → grava; badge → limpa.
    // Reusa rota PUT /talentos/<tid>/aumento-atributo gravando short-attr ('int','car','sab').
    root.querySelectorAll("[data-vontade-pick]").forEach(elem => {
      elem.addEventListener("click", async (e) => {
        e.stopPropagation();
        e.preventDefault();
        const tid = elem.dataset.tid;
        if (!tid) return;
        const card = elem.closest("[data-pick-tier]");
        if (card?.dataset.locked === "1") {
          alert("Slot locked — escolha quando o slot ativar.");
          return;
        }
        const attr = elem.dataset.attr;
        const novaCSV = attr ? attr : (confirm("Limpar a escolha de save-prof?") ? null : undefined);
        if (novaCSV === undefined) return;
        await fetch(`/api/personagens/${pid}/talentos/${tid}/aumento-atributo`, {
          method: "PUT",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ atributo: novaCSV }),
        });
        await load();
      });
    });

    // Botão X de remover talento (explícito — não dispara picker)
    root.querySelectorAll("[data-tier-remove]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();
        const card = btn.closest("[data-pick-tier]");
        const talId = card?.dataset.talid;
        if (!talId) return;
        if (!confirm("Remover este talento?")) return;
        fetch(`/api/personagens/${pid}/talentos/${talId}`, { method: "DELETE" })
          .then(() => load());
      });
    });

    root.querySelectorAll("[data-pick-tier]").forEach(elem => {
      elem.addEventListener("click", (e) => {
        if (e.target.closest("[data-tier-remove]")) return;
        // Defesa em profundidade: se o click veio de um pick-slot interno
        // (ex: pick:talento-geral:1 dentro de Multi-talentoso), não dispara
        // o picker do tier — o inner handler já tratou + stopPropagation.
        if (e.target.closest("[data-pick-slot]") || e.target.closest("[data-pick-slot-remove]")) return;
        // Ignora cliques em badges/picker inline de Aumento de Atributo e save-prof-vontade.
        if (e.target.closest("[data-aumento-pick]") || e.target.closest("[data-vontade-pick]")) return;
        e.stopPropagation();
        const cat  = elem.dataset.pickTier;
        const tier = parseInt(elem.dataset.tier, 10);
        const idClasse = elem.dataset.idClasse ? parseInt(elem.dataset.idClasse, 10) : null;
        const locked = elem.dataset.locked === "1";
        if (locked) {
          alert("Este slot ainda não está desbloqueado (nível da classe insuficiente).");
          return;
        }
        if (cat === "classe") return pickTalentoClasse(tier, idClasse);
        pickTalentoRacEss(tier);
      });
    });
  }

  // ---------- slot Raça/Essência (combinado) ----------
  async function pickTalentoRacEss(tier) {
    const r = await fetch(`/api/personagens/${pid}/talentos-raciais-disponiveis`).then(r => r.json());
    // mostra talentos do tier vindos de QUALQUER fonte (raça ou essência do personagem)
    const talentos = (r.talentos || []).filter(t => t.NivelMinimo === tier);
    if (!talentos.length) {
      alert(`Sem talentos Nv ${tier}+ disponíveis para suas tags: ${(r.tags_personagem||[]).join(", ")}.`);
      return;
    }
    openPicker({
      title: `Talento de Raça/Essência — Nv ${tier}+`,
      options: talentos,
      renderOption: (t) => `
        <b>${t.Nome}</b>
        <div><small style="color:#555"><span style="background:${t.Fonte==="humano"?"#2e8b5b":"#8b2e26"};color:#fff;padding:1px 6px;border-radius:3px;font-size:9px;text-transform:uppercase;">${t.Fonte}</span> · Pré-req: ${t.PreReqTexto || "—"}</small></div>
        <div><small>${(t.Descricao || "").slice(0, 260)}${(t.Descricao || "").length > 260 ? "…" : ""}</small></div>`,
      onPick: async (t) => {
        const categoria = ["humano","anao","elfo","gnomo","halfling","meio-elfo","meio-orc","draconato"].includes(t.Fonte) ? "raca" : "essencia";
        await fetch(`/api/personagens/${pid}/talentos-raciais`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ id_talento: t.Id_TalentoRacial, categoria }),
        });
        await load();
      },
    });
  }

  // ---------- avaliação de pré-requisito de talento ----------
  // Retorna {ok, missing[]} onde missing é uma lista de strings descrevendo o que falta.
  // Cada "grupo" do prereq é OR-interno (Atrib1 OU Atrib2). Múltiplos grupos são AND.
  function evaluatePrereq(talent, persState) {
    const text = (talent.PreReqTexto || "").trim();
    if (!text) return { ok: true, missing: [] };
    const ATR_MAP = {
      "forca": "Forca", "força": "Forca",
      "destreza": "Destreza",
      "constituicao": "Constituicao", "constituição": "Constituicao",
      "inteligencia": "Inteligencia", "inteligência": "Inteligencia",
      "sabedoria": "Sabedoria",
      "carisma": "Carisma",
    };
    let t = text.replace(/^Pr[ée]\s*-?\s*requisitos?:?\s*/i, "");
    const parts = t.split(/,\s+/);
    const missing = [];
    for (const part of parts) {
      const lower = part.toLowerCase();
      // pula "Nível X+" (sempre cumprido se talento aparece — gate de slot já filtrou)
      if (/n[íi]vel\s+\d+/i.test(part) && !/atributo\s+de\s+conjura/i.test(part)) continue;
      // Atributo: "Força 13+" ou "Força 13+ ou Destreza 13+"
      const atrMatches = [...part.matchAll(/(Força|Destreza|Constituição|Inteligência|Sabedoria|Carisma|Forca|Inteligencia|Constituicao)\s+(\d+)\+?/gi)];
      if (atrMatches.length) {
        const reqs = atrMatches.map(m => {
          const norm = m[1].toLowerCase()
            .replace(/[áàã]/g, "a").replace(/[éê]/g, "e").replace(/í/g, "i")
            .replace(/[óô]/g, "o").replace(/ú/g, "u").replace(/ç/g, "c");
          return { attr: ATR_MAP[norm] || ATR_MAP[m[1].toLowerCase()] || m[1], attrLabel: m[1], min: parseInt(m[2], 10) };
        });
        const ok = reqs.some(r => (persState.attribs[r.attr] || 0) >= r.min);
        if (!ok) missing.push(reqs.map(r => `${r.attrLabel} ${r.min}+`).join(" ou "));
        continue;
      }
      // Marca Superior / Marca Anômala Maior (pra Marca Potente)
      if (/marca\s+(arcana\s+)?superior|marca\s+an[oô]mala\s+maior/i.test(lower)) {
        if (!persState.temMarcaSuperior) missing.push("Marca Superior ou Marca Anômala Maior");
        continue;
      }
      // Marca Arcana / Marca Anômala (genérica)
      if (/marca\s+arcana|marca\s+an[oô]mala/i.test(lower)) {
        if (!persState.temMarca) missing.push("uma Marca Arcana ou Anômala");
        continue;
      }
      // Conjuração / Magia de Pacto
      if (/(capacidade\s+de\s+)?conjura[çc][ãa]o\b/i.test(lower) || /magia\s+de\s+pacto/i.test(lower)) {
        if (!persState.isCaster) missing.push("Conjuração ou Magia de Pacto");
        continue;
      }
      // Iniciado <de/no/na> ...
      const mIni = part.match(/iniciado\s+(?:no|na|do|da)\s+([^,.]+)/i);
      if (mIni) {
        const labelExig = mIni[0].trim();
        const tokenExig = mIni[1].toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
          .replace(/[^a-z0-9 ]+/g, "").trim().split(" ")[0];
        const ok = [...persState.iniciados].some(s => s.includes(tokenExig));
        if (!ok) missing.push(labelExig);
        continue;
      }
    }
    return { ok: missing.length === 0, missing };
  }

  // Constrói estado de pré-requisitos do personagem (uma vez por picker open).
  function buildPersStatePrereq() {
    const attribs = state.atributos_efetivos?.valores || state.personagem?.atributos || {};
    const isCaster =
      (state.classe?.Conjuracao && state.classe.Conjuracao !== "none") ||
      (state.subclasse?.Conjuracao === "third");
    const slugs = [];
    if (state.talento_origem?.Slug) slugs.push(state.talento_origem.Slug.toLowerCase());
    if (state.talento_origem_extra?.Slug) slugs.push(state.talento_origem_extra.Slug.toLowerCase());
    const temMarca = slugs.some(s => s.startsWith("marca-"));
    const temMarcaSuperior = (state.talentos || []).some(t =>
      t.Categoria === "classe"
      && /marca\s+arcana\s+superior|marca\s+an[oô]mala\s+maior/i.test(t.Nome || "")
    );
    // iniciados: tokens (1ª palavra após "iniciado") dos talentos de origem + class talents
    const iniciados = new Set();
    const tryAddIniciado = (slug) => {
      if (!slug) return;
      const m = slug.toLowerCase().match(/iniciado-(?:na|no|da|do)?-?([a-z]+)/);
      if (m) iniciados.add(m[1]);
    };
    tryAddIniciado(state.talento_origem?.Slug);
    tryAddIniciado(state.talento_origem_extra?.Slug);
    (state.talentos || []).forEach(t => {
      if (/iniciado/i.test(t.Nome || "")) {
        const m = (t.Nome || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
          .match(/iniciado\s+(?:na|no|da|do)?\s*([a-z]+)/);
        if (m) iniciados.add(m[1]);
      }
    });
    return { attribs, isCaster, temMarca, temMarcaSuperior, iniciados };
  }

  // ---------- slot Classe (catálogo TB_OpcaoJogo Tipo='talento-geral') ----------
  async function pickTalentoClasse(tier, idClasse) {
    let opcoes;
    try {
      opcoes = await fetch("/api/opcoes?tipo=talento-geral").then(r => r.json());
    } catch (e) { alert("Erro: " + e); return; }

    // tags do personagem para destacar quais prereqs ele atende.
    // Usa atributos_efetivos (com bg + ASI) pra avaliar prereqs como for13.
    const atr = state.atributos_efetivos?.valores || state.personagem?.atributos || {};
    const personagemTags = new Set();
    if ((atr.Forca       || 0) >= 13) personagemTags.add("for13");
    if ((atr.Destreza    || 0) >= 13) personagemTags.add("dex13");
    if ((atr.Constituicao|| 0) >= 13) personagemTags.add("con13");
    if ((atr.Inteligencia|| 0) >= 13) personagemTags.add("int13");
    if ((atr.Sabedoria   || 0) >= 13) personagemTags.add("sab13");
    if ((atr.Carisma     || 0) >= 13) personagemTags.add("car13");
    // conjuração: se tem any spell list ou auto_efeitos truque
    const isCaster = state.classe?.Conjuracao && state.classe.Conjuracao !== "none";
    if (isCaster || state.subclasse?.Conjuracao === "third") personagemTags.add("conjuracao");
    personagemTags.add(`nv${state.personagem?.Nivel || 1}`);
    // gate por nivel do slot (sempre)
    personagemTags.add(`nv${tier}`);

    // filtra: NivelMinimo <= tier (disponíveis para este slot)
    const candidatos = opcoes.filter(o => (o.NivelMinimo || 1) <= tier);
    if (!candidatos.length) {
      alert(`Sem talentos disponíveis para Nv ${tier}.`);
      return;
    }
    // ordena: "Aumento de Atributo" sempre primeiro (opção ASI canônica), resto alfabético
    candidatos.sort((a, b) => {
      const aIsAsi = (a.Slug || "") === "aumento-de-atributo-1-1";
      const bIsAsi = (b.Slug || "") === "aumento-de-atributo-1-1";
      if (aIsAsi && !bIsAsi) return -1;
      if (bIsAsi && !aIsAsi) return 1;
      return (a.Nome || "").localeCompare(b.Nome || "", "pt-BR");
    });

    const renderTag = (t, ok) => {
      const bg = ok ? "#2e8b5b" : "#a86060";
      return `<span style="background:${bg};color:#fff;padding:0 5px;border-radius:3px;font-size:9px;text-transform:uppercase;margin-right:3px;">${escapeHtmlBare(t)}</span>`;
    };

    // Avalia prereq de cada candidato uma vez (cache)
    const persState = buildPersStatePrereq();
    const prereqStatus = new Map();
    candidatos.forEach(o => prereqStatus.set(o.Id_Opcao, evaluatePrereq(o, persState)));

    openPicker({
      title: `Talento de Classe — Nv ${tier} (${state.classe?.Nome || ""})`,
      options: candidatos,
      renderOption: (o) => {
        const status = prereqStatus.get(o.Id_Opcao) || { ok: true, missing: [] };
        let tags = [];
        try { tags = JSON.parse(o.TagsJSON || "[]"); } catch (e) { tags = []; }
        const prereqTags = tags.filter(t => /^(for|dex|con|int|sab|car)\d+$/.test(t) || t === "conjuracao" || t === "magia-de-pacto" || t.startsWith("iniciado-") || t.startsWith("marca-"));
        const prereqBadges = prereqTags.length
          ? prereqTags.map(t => renderTag(t, personagemTags.has(t))).join("")
          : `<span style="color:#888;font-size:10px">sem prereq</span>`;
        const missingHint = status.ok
          ? ""
          : `<div style="color:#a86060;font-size:10px;font-weight:600;margin:2px 0">⚠ Faltam: ${status.missing.map(m => escapeHtmlBare(m)).join(", ")}</div>`;
        const desc = (o.Descricao || "").slice(0, 240);
        const wrapperStyle = status.ok ? "" : "opacity:0.5;background:#f0ebd8";
        return `<div style="${wrapperStyle}">
          <b>${escapeHtmlBare(o.Nome)}</b>
          <div style="margin:2px 0">${prereqBadges}</div>
          ${missingHint}
          <div><small>${escapeHtmlBare(desc)}${(o.Descricao || "").length > 240 ? "…" : ""}</small></div>
        </div>`;
      },
      onPick: async (o) => {
        const status = prereqStatus.get(o.Id_Opcao) || { ok: true, missing: [] };
        if (!status.ok) {
          const aviso = `Você não tem o mínimo para pegar este talento.\n\nFalta: ${status.missing.join(", ")}\n\nPegar mesmo assim?`;
          if (!confirm(aviso)) return;
        }
        await fetch(`/api/personagens/${pid}/talento-manual`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            categoria: "classe",
            nivel: tier,
            id_classe: idClasse,
            nome: o.Nome,
            detalhes: o.Descricao || "",
          }),
        });
        await load();
      },
    });
  }

  async function onPick(kind, ds) {
    if (kind === "raca")       return pickRaca();
    if (kind === "classe")     return pickClasse();
    if (kind === "subclasse")  return pickSubclasse();
    if (kind === "nivel")      return pickNivel();
    if (kind === "attr")       return pickAttr(ds.attr);
    if (kind === "pers")       return pickPers(ds.tipo);
    if (kind === "nome")       return pickNome();
    if (kind === "background") return pickBackground();
  }

  // ---------- modal de TÉCNICAS: cascata com catálogo TB_Manobra ----------
  async function openTecnicasModal() {
    const r = await fetch(`/api/personagens/${pid}/manobras-disponiveis`).then(x => x.json());
    if (r.error) { alert(r.error); return; }
    if (!r.classe) { alert("Escolha uma classe primeiro."); return; }

    openPicker({
      title: `Manobras (${r.classe}) — Grau máx ${r.grau_max} · Nv ${r.nivel}`,
      options: r.manobras,
      renderOption: (m) => `
        <b>${m.Nome}</b>
        <div><small style="color:${m.ja_escolhida ? "#2e8b5b" : "#666"}">
          ${m.ja_escolhida ? "✓ já adquirida" : `grau ${m.Grau} · ${m.TagsJSON.join(", ")}`}
        </small></div>
        ${m.Flavor ? `<div><small style="font-style:italic;color:#777">${m.Flavor}</small></div>` : ""}
        <div><small>${(m.Descricao || "").slice(0, 220)}${(m.Descricao || "").length > 220 ? "…" : ""}</small></div>`,
      onPick: async (m) => {
        if (m.ja_escolhida) { alert("Você já conhece essa manobra."); return; }
        await fetch(`/api/personagens/${pid}/tecnicas`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_manobra: m.Id_Manobra }),
        });
        await load();
      },
    });
  }

  // ---------- modal de SEGREDOS DE CAÇADOR: cascata com TB_Segredo ----------
  async function openSegredosModal() {
    const r = await fetch(`/api/personagens/${pid}/segredos-disponiveis`).then(x => x.json());
    if (r.error) { alert(r.error); return; }
    if (!r.segredos || !r.segredos.length) { alert("Nenhum segredo disponível."); return; }

    openPicker({
      title: `Segredos de Caçador (${r.total} no catálogo)`,
      options: r.segredos,
      renderOption: (s) => `
        <b>${s.Nome}</b>
        <div><small style="color:${s.ja_escolhido ? "#2e8b5b" : "#666"}">
          ${s.ja_escolhido ? "✓ já adquirido" : `${s.Linha} · Custo ${s.Custo}${s.Acao ? " · " + s.Acao : ""}`}
        </small></div>
        ${s.Flavor ? `<div><small style="font-style:italic;color:#777">${s.Flavor.slice(0, 200)}</small></div>` : ""}
        <div><small>${(s.Descricao || "").slice(0, 260)}${(s.Descricao || "").length > 260 ? "…" : ""}</small></div>`,
      onPick: async (s) => {
        if (s.ja_escolhido) { alert("Você já conhece esse segredo."); return; }
        await fetch(`/api/personagens/${pid}/segredos`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_segredo: s.Id_Segredo }),
        });
        await load();
      },
    });
  }

  // ---------- modal de SEGREDOS MÍSTICOS: filtra por NivelMin + GateTag (manifestação) ----------
  async function openSegredoMisticoModal() {
    const r = await fetch(`/api/personagens/${pid}/segredos-misticos-disponiveis`).then(x => x.json());
    if (r.error) { alert(r.error); return; }
    if (!r.segredos || !r.segredos.length) { alert("Catálogo vazio."); return; }
    // Filtra: só mostra os disponíveis (nivel_ok && gate_ok && !ja_escolhido).
    // Mas exibe ja_escolhidos como tinted pra dar contexto; bloqueados (sem nivel ou gate) como locked.
    openPicker({
      title: `Segredos Místicos (Místico Nv ${r.mistico_nivel})`,
      options: r.segredos,
      renderOption: (s) => {
        const tags = [];
        if (s.ja_escolhido && s.repetivel) tags.push('<small style="color:#2e8b5b">✓ adquirido (♻ repetível — pode pegar de novo)</small>');
        else if (s.ja_escolhido) tags.push('<small style="color:#2e8b5b">✓ já adquirido</small>');
        else if (!s.nivel_ok) tags.push(`<small style="color:#aa3">🔒 requer Místico Nv ${s.NivelMin}</small>`);
        else if (!s.gate_ok) tags.push(`<small style="color:#aa3">🔒 requer ${s.GateTag}</small>`);
        else if (s.repetivel) tags.push('<small style="color:#666">disponível · ♻ repetível</small>');
        else tags.push('<small style="color:#666">disponível</small>');
        return `
          <b>${s.Nome}</b>
          <div><small style="color:#888">${escapeHtmlBare(s.Secao)}${s.NivelMin > 1 ? ` · Nv ${s.NivelMin}+` : ""}</small></div>
          <div>${tags.join(" · ")}</div>
          <div><small>${(s.Descricao || "").slice(0, 280)}${(s.Descricao || "").length > 280 ? "…" : ""}</small></div>`;
      },
      onPick: async (s) => {
        if (s.ja_escolhido && !s.repetivel) { alert("Você já tem esse segredo."); return; }
        if (!s.disponivel) {
          if (!confirm(`Não atende pré-requisito (${!s.nivel_ok ? "nível" : "gate"}). Adicionar mesmo assim?`)) return;
        }
        await fetch(`/api/personagens/${pid}/segredos-misticos`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_segredo: s.Id_Segredo }),
        });
        await load();
      },
    });
  }

  // ---------- modal de ESTILOS DE KI / KENSEI: lista flat com 9 estilos ----------
  // Backend filtra catálogo por tag 'kensei-estilos' (sub Kensei vê só Kensei).
  async function openEstiloKiModal() {
    const r = await fetch(`/api/personagens/${pid}/estilos-ki-disponiveis`).then(x => x.json());
    if (r.error) { alert(r.error); return; }
    if (!r.estilos || !r.estilos.length) { alert("Catálogo vazio."); return; }
    const titulo = r.catalogo === "kensei" ? "Estilos Kensei" : "Estilos de Ki";
    openPicker({
      title: `${titulo} (${r.total} no catálogo)`,
      options: r.estilos,
      renderOption: (e) => `
        <b>${e.Nome}</b>
        <div><small style="color:${e.ja_escolhido ? "#2e8b5b" : "#666"}">
          ${e.ja_escolhido ? "✓ já adquirido" : `Custo ${e.CustoKi} Ki`}
        </small></div>
        <div><small>${(e.Descricao || "").slice(0, 280)}${(e.Descricao || "").length > 280 ? "…" : ""}</small></div>`,
      onPick: async (e) => {
        if (e.ja_escolhido) { alert("Você já tem esse estilo."); return; }
        await fetch(`/api/personagens/${pid}/estilos-ki`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_estilo: e.Id_Estilo }),
        });
        await load();
      },
    });
  }

  // ---------- modal de EVOLUÇÃO TOTÊMICA: filtra por tier do slot ----------
  // tierMax: "menor" -> só Menor; "maior" -> Menor ou Maior.
  async function openEvolucaoTotemicaModal(tierMax) {
    const r = await fetch(`/api/personagens/${pid}/evolucoes-totemicas-disponiveis`).then(x => x.json());
    if (r.error) { alert(r.error); return; }
    const tiersOK = (tierMax === "maior") ? new Set(["menor", "maior"]) : new Set(["menor"]);
    const filtered = (r.evolucoes || []).filter(e => tiersOK.has((e.Tier || "").toLowerCase()));
    if (!filtered.length) { alert("Sem evoluções disponíveis."); return; }
    openPicker({
      title: `Evolução Totêmica (Tier ≤ ${tierMax})`,
      options: filtered,
      renderOption: (e) => `
        <b>${e.Nome}</b>
        <div><small style="color:${e.ja_escolhida ? "#2e8b5b" : "#666"}">
          ${e.ja_escolhida ? "✓ já adquirida" : `${e.Tier}${e.repetivel ? " · repetível" : ""}`}
        </small></div>
        <div><small>${(e.Descricao || "").slice(0, 280)}${(e.Descricao || "").length > 280 ? "…" : ""}</small></div>`,
      onPick: async (e) => {
        if (e.ja_escolhida) { alert("Você já tem essa evolução."); return; }
        let variante = null;
        if (e.Slug === "resistencia-elemental") {
          const elementos = ["Ácido", "Elétrico", "Fogo", "Frio", "Trovão"];
          variante = (prompt(`Tipo de dano (${elementos.join(", ")}):`, "Fogo") || "").trim();
          if (!variante) return;
        }
        await fetch(`/api/personagens/${pid}/evolucoes-totemicas`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_evolucao: e.Id_Evolucao, variante }),
        });
        await load();
      },
    });
  }

  // ---------- modal de INIMIGO FAVORITO: lista flat com 12 tipos ----------
  async function openInimigosFavoritosModal() {
    const r = await fetch(`/api/personagens/${pid}/inimigos-favoritos-disponiveis`).then(x => x.json());
    if (r.error) { alert(r.error); return; }
    if (!r.inimigos || !r.inimigos.length) { alert("Catálogo vazio."); return; }
    openPicker({
      title: `Inimigo Favorito (${r.total} tipos)`,
      options: r.inimigos,
      renderOption: (i) => `
        <b>${i.Nome}</b>
        <div><small style="color:${i.ja_escolhido ? "#2e8b5b" : "#666"}">
          ${i.ja_escolhido ? "✓ já escolhido" : "Tipo de criatura"}
        </small></div>`,
      onPick: async (i) => {
        if (i.ja_escolhido) { alert("Você já escolheu esse inimigo."); return; }
        await fetch(`/api/personagens/${pid}/inimigos-favoritos`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_inimigo_favorito: i.Id_InimigoFavorito }),
        });
        await load();
      },
    });
  }

  // ---------- picker de Talento de Origem (principal | extra) ----------
  // Regra: Marcas Arcanas (e Marca Anômala) são mutuamente exclusivas.
  // Se o personagem já tem uma Marca em qualquer slot (principal ou extra),
  // o picker do OUTRO slot exclui Marcas — exceto a já escolhida pra reabrir
  // pra trocar.
  async function pickTalentoOrigem(kind = "principal") {
    let opcoes;
    try {
      opcoes = await fetch("/api/opcoes?tipo=talento-origem").then(r => r.json());
    } catch (e) { alert("Erro: " + e); return; }
    if (!opcoes.length) {
      alert("Catálogo de Talentos de Origem vazio.");
      return;
    }

    const isMarca = (slug) => !!slug && slug.startsWith("marca-");
    const FIELD = {
      principal: "Id_TalentoOrigem",
      extra:     "Id_TalentoOrigemExtra",
      racial:    "Id_TalentoOrigemRacial",
    };
    const SLOT_STATE = {
      principal: state.talento_origem,
      extra:     state.talento_origem_extra,
      racial:    state.talento_origem_racial,
    };
    const fieldName = FIELD[kind] || "Id_TalentoOrigem";
    const slotAtual = SLOT_STATE[kind];
    // Marcas são exclusivas entre os 3 slots: se qualquer OUTRO slot tem Marca, exclui Marcas aqui.
    const outrosSlots = Object.entries(SLOT_STATE)
      .filter(([k, _]) => k !== kind)
      .map(([_, s]) => s)
      .filter(s => s && isMarca(s.Slug));
    const marcaNoutro = outrosSlots[0] || null;
    const filtered = marcaNoutro
      ? opcoes.filter(o => !isMarca(o.Slug))
      : opcoes;

    filtered.sort((a, b) => (a.Nome || "").localeCompare(b.Nome || "", "pt-BR"));

    const TITULO = {
      principal: "Talento de Origem (escolha 1)",
      extra:     "Talento de Origem Extra (Raízes Profundas)",
      racial:    "Talento de Origem (traço racial)",
    };
    const titulo = TITULO[kind] || TITULO.principal;
    const subtitulo = marcaNoutro
      ? `<small style="color:#aa3">⚠ Marcas excluídas — você já tem '${escapeHtmlBare(marcaNoutro.Nome)}' em outro slot.</small>`
      : "";

    openPicker({
      title: titulo + (subtitulo ? "" : ""),
      options: filtered,
      renderOption: (o) => {
        const temLista = !!o.MagiaExpandidaJSON;
        const flag = temLista
          ? `<span style="background:#5d4d2a;color:#fff;padding:1px 6px;border-radius:3px;font-size:9px;text-transform:uppercase;">+ magia expandida</span>`
          : `<span style="background:#888;color:#fff;padding:1px 6px;border-radius:3px;font-size:9px;text-transform:uppercase;">só efeito</span>`;
        const isCurrent = slotAtual && o.Id_Opcao === slotAtual.Id_Opcao;
        const currentBadge = isCurrent ? `<span style="background:#2e8b5b;color:#fff;padding:1px 6px;border-radius:3px;font-size:9px;text-transform:uppercase;margin-left:4px">★ atual</span>` : "";
        const desc = (o.Descricao || "").slice(0, 220);
        return `
          <b>${escapeHtmlBare(o.Nome)}</b> ${flag}${currentBadge}
          <div><small>${escapeHtmlBare(desc)}${(o.Descricao || "").length > 220 ? "…" : ""}</small></div>`;
      },
      onPick: async (o) => {
        await api.patch({ [fieldName]: o.Id_Opcao });
        await load();
      },
    });
  }

  // Picker de Talento de Origem para uma instância específica de Segredo Místico
  // (Aprendizado dos Antigos × N). Cada instância tem 1 talento associado via
  // TB_PersonagemSegredoMisticoTalento. Marca exclusivity com os 3 slots fixos
  // (principal/extra/racial) é mantida — não pode duplicar Marca em nenhum lugar.
  async function pickTalentoOrigemSegredo(sid) {
    let opcoes;
    try {
      opcoes = await fetch("/api/opcoes?tipo=talento-origem").then(r => r.json());
    } catch (e) { alert("Erro: " + e); return; }
    if (!opcoes.length) { alert("Catálogo de Talentos de Origem vazio."); return; }

    const isMarca = (slug) => !!slug && slug.startsWith("marca-");
    // Coleta TODAS as Marcas já em uso (3 slots fixos + outros segredos)
    const marcasEmUso = new Set();
    [state.talento_origem, state.talento_origem_extra, state.talento_origem_racial].forEach(s => {
      if (s && isMarca(s.Slug)) marcasEmUso.add(s.Id_Opcao);
    });
    (state.segredos_misticos || []).forEach(seg => {
      const to = seg.talento_origem;
      if (to && isMarca(to.Slug) && String(seg.Id) !== String(sid)) {
        marcasEmUso.add(to.Id_Opcao);
      }
    });
    const segAtual = (state.segredos_misticos || []).find(s => String(s.Id) === String(sid));
    const slotAtual = segAtual?.talento_origem || null;
    const filtered = (marcasEmUso.size > 0)
      ? opcoes.filter(o => !isMarca(o.Slug) || o.Id_Opcao === slotAtual?.Id_Opcao)
      : opcoes;
    filtered.sort((a, b) => (a.Nome || "").localeCompare(b.Nome || "", "pt-BR"));

    openPicker({
      title: `Talento de Origem (via ${segAtual?.Nome || "Segredo Místico"})`,
      options: filtered,
      renderOption: (o) => {
        const isCurrent = slotAtual && o.Id_Opcao === slotAtual.Id_Opcao;
        const currentBadge = isCurrent
          ? `<span style="background:#2e8b5b;color:#fff;padding:1px 6px;border-radius:3px;font-size:9px;text-transform:uppercase;margin-left:4px">★ atual</span>`
          : "";
        const desc = (o.Descricao || "").slice(0, 220);
        return `
          <b>${escapeHtmlBare(o.Nome)}</b>${currentBadge}
          <div><small>${escapeHtmlBare(desc)}${(o.Descricao || "").length > 220 ? "…" : ""}</small></div>`;
      },
      onPick: async (o) => {
        await fetch(`/api/personagens/${pid}/segredos-misticos/${sid}/talento-origem`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ id_talento_origem: o.Id_Opcao }),
        });
        await load();
      },
    });
  }

  // ---------- picker de maestria de arma (cascade arma → maestria) ----------
  async function pickMaestriaArma(slotIndex) {
    let armas;
    try {
      armas = await fetch("/api/armas").then(r => r.json());
    } catch (e) {
      alert("Erro ao buscar armas: " + e);
      return;
    }
    if (!armas.length) {
      alert("Catálogo de armas vazio.");
      return;
    }

    // Filtro Bushidō: se este slot vem da hab Bushidō (sub Kensei), aplica restrições.
    // Nv 3-10: sem Pesada, sem Especial. Nv 11+: sem Especial (Pesada permitido).
    const slotInfo = (state.maestrias_armas_slots || []).find(s => (s.slot - 1) === slotIndex);
    const isBushido = slotInfo && slotInfo.origem === "Bushidō";
    if (isBushido) {
      // pega nivel da classe Monge no char
      const monge = (state.classes || []).find(c =>
        (c.SlugClasse || "").toLowerCase() === "monge" ||
        (c.NomeClasse || "").toLowerCase() === "monge"
      );
      const nvMonge = monge ? (monge.Nivel || 0) : 0;
      const hasProp = (a, prop) => (a.Propriedades || "").toLowerCase().includes(prop.toLowerCase());
      const before = armas.length;
      armas = armas.filter(a => {
        if (hasProp(a, "Especial")) return false;       // sempre proibido
        if (nvMonge < 11 && hasProp(a, "Pesada")) return false;  // só permitido a partir Nv 11
        // só simples ou marciais (não fogo, etc)
        const cat = (a.Categoria || "").toLowerCase();
        if (!cat.startsWith("simples") && !cat.startsWith("marcial")) return false;
        return true;
      });
      console.log(`[Bushidō] filter Nv ${nvMonge}: ${before} → ${armas.length} armas válidas`);
      if (!armas.length) {
        alert("Filtro Bushidō: sem armas válidas no catálogo.");
        return;
      }
    }

    // categoria → label PT
    const catLabel = {
      "simples-corpo": "Simples (Corpo)",
      "simples-distancia": "Simples (Distância)",
      "marcial-corpo": "Marcial (Corpo)",
      "marcial-distancia": "Marcial (Distância)",
      "fogo": "Arma de Fogo",
    };

    const tituloFiltro = isBushido ? " [Bushidō: simples/marcial, sem Especial" + ((slotInfo && (state.classes || []).find(c => c.NomeClasse === "Monge")?.Nivel < 11) ? ", sem Pesada]" : "]") : "";
    openPicker({
      title: `Maestria de Armas — Slot ${slotIndex + 1}: escolha a arma${tituloFiltro}`,
      options: armas,
      renderOption: (a) => {
        const maesTxt = (a.Maestrias || []).map(m => m.ingles ? `${m.nome} (${m.ingles})` : m.nome).join(", ");
        return `
          <b>${escapeHtmlBare(a.Nome)}</b>
          <div><small style="color:#666">
            <span style="background:#5d4d2a;color:#fff;padding:1px 6px;border-radius:3px;font-size:9px;text-transform:uppercase;">${escapeHtmlBare(catLabel[a.Categoria] || a.Categoria)}</span>
            · ${escapeHtmlBare(a.Dano || "")} · ${escapeHtmlBare(a.Propriedades || "Nenhuma")}
          </small></div>
          <div><small style="color:#8b4513"><b>Maestrias:</b> ${escapeHtmlBare(maesTxt)}</small></div>`;
      },
      onPick: async (a) => {
        // depois de escolher arma, abre picker secundário com as maestrias permitidas
        const armaMaes = a.Maestrias || [];
        if (!armaMaes.length) {
          alert("Esta arma não tem maestrias listadas.");
          return;
        }
        // resolve cada maestria.nome para o registro de TB_Maestria
        const todasMaestrias = await fetch("/api/maestrias").then(r => r.json());
        const matched = armaMaes.map(am => {
          const m = todasMaestrias.find(x => x.Nome === am.nome);
          return m ? { ...m, _arma_label: am.nome + (am.ingles ? ` (${am.ingles})` : "") } : null;
        }).filter(Boolean);

        if (!matched.length) {
          alert("Nenhuma das maestrias da arma foi encontrada no catálogo TB_Maestria. Reimport pode estar pendente.");
          return;
        }

        openPicker({
          title: `${a.Nome}: escolha 1 maestria`,
          options: matched,
          renderOption: (m) => `
            <b>${escapeHtmlBare(m.Nome)}${m.NomeIngles ? ` <small style="color:#888">(${escapeHtmlBare(m.NomeIngles)})</small>` : ""}</b>
            <div><small>${escapeHtmlBare(m.Efeito).slice(0, 280)}${(m.Efeito || "").length > 280 ? "…" : ""}</small></div>`,
          onPick: async (m) => {
            const r = await fetch(`/api/personagens/${pid}/maestrias-armas`, {
              method: "POST",
              headers: {"Content-Type": "application/json"},
              body: JSON.stringify({
                id_arma: a.Id_Arma,
                id_maestria: m.Id_Maestria,
                slot_index: slotIndex,
              }),
            }).then(r => r.json());
            if (r.error) { alert(r.error); return; }
            await load();
          },
        });
      },
    });
  }

  // ---------- helper de escape ----------
  function escapeHtmlBare(s) {
    if (s == null) return "";
    return String(s).replace(/[&<>"']/g, c => ({
      "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
    }[c]));
  }

  // ---------- modal de Background ----------
  function pickBackground() {
    const p = state.personagem;
    const atualBonus = p.BackgroundBonusJSON ? JSON.parse(p.BackgroundBonusJSON) : {};
    const atualItems = (state.idiomas || []).filter(i => i.Origem === "background");
    const ATRS = [["Forca","Força"],["Destreza","Destreza"],["Constituicao","Constituição"],
                  ["Inteligencia","Inteligência"],["Sabedoria","Sabedoria"],["Carisma","Carisma"]];

    const back = document.createElement("div");
    back.className = "picker-backdrop";
    back.innerHTML = `
      <div class="picker bg-picker">
        <div class="picker-head">Background do Personagem</div>
        <div class="picker-list bg-body">
          <label class="bg-row"><span>Nome do Background</span>
            <input type="text" id="bg-nome" value="${(p.BackgroundNome||"").replace(/"/g,"&quot;")}" placeholder="ex.: Arqueólogo, Soldado, Eremita…">
          </label>

          <div class="bg-mode-row">
            <label><input type="radio" name="bgmode" value="111" ${sumVals(atualBonus)===3 && Object.values(atualBonus).every(v=>v<=1) ? "checked":""}> +1 +1 +1 (3 atributos diferentes)</label>
            <label><input type="radio" name="bgmode" value="21"  ${Object.values(atualBonus).includes(2) ? "checked":""}> +2 +1 (2 atributos)</label>
          </div>

          <div class="bg-bonus" id="bg-bonus"></div>

          <div class="bg-items-label">Escolha 2: ferramentas ou idiomas (a, b ou c)</div>
          <div class="bg-items" id="bg-items">
            ${[0,1].map(i => `
              <div class="bg-item-row">
                <select class="bg-item-tipo" data-slot="${i}">
                  <option value="ferramenta" ${atualItems[i]?.Tipo==="ferramenta" ? "selected":""}>Ferramenta</option>
                  <option value="idioma"     ${atualItems[i]?.Tipo==="idioma"     ? "selected":""}>Idioma</option>
                </select>
                <select class="bg-item-nome" data-slot="${i}" data-current="${(atualItems[i]?.Nome||"").replace(/"/g,"&quot;")}">
                  <option value="">— escolha —</option>
                </select>
              </div>`).join("")}
          </div>

          <div class="bg-msg" id="bg-msg"></div>
        </div>
        <div class="picker-foot">
          <button class="picker-btn" data-close>Cancelar</button>
          <button class="picker-btn bg-save" id="bg-save">Salvar</button>
        </div>
      </div>`;
    document.body.appendChild(back);

    const renderBonus = () => {
      const mode = back.querySelector("input[name=bgmode]:checked")?.value || "111";
      const wrap = back.querySelector("#bg-bonus");
      const curAtribs = Object.keys(atualBonus);
      const def = (i) => curAtribs[i] || "";
      const defV = (atr) => atualBonus[atr] || "";
      if (mode === "111") {
        wrap.innerHTML = `
          <div class="bg-bonus-label">3 atributos, +1 cada:</div>
          <div class="bg-bonus-grid">
            ${[0,1,2].map(i => `
              <select class="bg-atr" data-slot="${i}">
                <option value="">—</option>
                ${ATRS.map(([k,l]) => `<option value="${k}" ${def(i)===k?"selected":""}>${l}</option>`).join("")}
              </select>`).join("")}
          </div>`;
      } else {
        const atr2 = Object.keys(atualBonus).find(k => atualBonus[k]===2) || "";
        const atr1 = Object.keys(atualBonus).find(k => atualBonus[k]===1 && k!==atr2) || "";
        wrap.innerHTML = `
          <div class="bg-bonus-label">+2 em um atributo, +1 em outro:</div>
          <div class="bg-bonus-grid">
            <select class="bg-atr" data-slot="A">
              <option value="">— +2 —</option>
              ${ATRS.map(([k,l]) => `<option value="${k}" ${atr2===k?"selected":""}>+2 ${l}</option>`).join("")}
            </select>
            <select class="bg-atr" data-slot="B">
              <option value="">— +1 —</option>
              ${ATRS.map(([k,l]) => `<option value="${k}" ${atr1===k?"selected":""}>+1 ${l}</option>`).join("")}
            </select>
          </div>`;
      }
    };
    renderBonus();
    back.querySelectorAll("input[name=bgmode]").forEach(r => r.addEventListener("change", renderBonus));

    // Popular selects de nome (idioma/ferramenta) via DOM (createElement, não innerHTML).
    const populateBgItem = async (slot) => {
      const tipoSel = back.querySelector(`.bg-item-tipo[data-slot="${slot}"]`);
      const nomeSel = back.querySelector(`.bg-item-nome[data-slot="${slot}"]`);
      if (!tipoSel || !nomeSel) return;
      const tipo = tipoSel.value;
      const cur = nomeSel.dataset.current || "";
      const catalog = await fetchCatalogo(tipo);
      while (nomeSel.firstChild) nomeSel.removeChild(nomeSel.firstChild);
      const placeholder = document.createElement("option");
      placeholder.value = ""; placeholder.textContent = "— escolha —";
      nomeSel.appendChild(placeholder);
      let matched = false;
      for (const n of catalog) {
        const opt = document.createElement("option");
        opt.value = n; opt.textContent = n;
        if (n === cur) { opt.selected = true; matched = true; }
        nomeSel.appendChild(opt);
      }
      if (cur && !matched) {
        const opt = document.createElement("option");
        opt.value = cur; opt.textContent = `${cur} (custom)`;
        opt.selected = true;
        nomeSel.appendChild(opt);
      }
    };
    [0, 1].forEach(populateBgItem);
    back.querySelectorAll(".bg-item-tipo").forEach(sel => {
      sel.addEventListener("change", async () => {
        const slot = sel.dataset.slot;
        const nomeSel = back.querySelector(`.bg-item-nome[data-slot="${slot}"]`);
        if (nomeSel) nomeSel.dataset.current = "";
        await populateBgItem(slot);
      });
    });

    back.addEventListener("click", (e) => {
      if (e.target === back || e.target.dataset.close !== undefined) back.remove();
    });

    back.querySelector("#bg-save").addEventListener("click", async () => {
      const nome = back.querySelector("#bg-nome").value.trim();
      const mode = back.querySelector("input[name=bgmode]:checked")?.value || "111";
      const atrs = [...back.querySelectorAll(".bg-atr")];
      let bonus = {};
      if (mode === "111") {
        const picked = atrs.map(s => s.value).filter(Boolean);
        if (new Set(picked).size !== 3) return showMsg(back, "escolha 3 atributos DIFERENTES");
        picked.forEach(a => bonus[a] = 1);
      } else {
        const [a2, a1] = atrs.map(s => s.value);
        if (!a2 || !a1) return showMsg(back, "escolha os 2 atributos");
        if (a2 === a1) return showMsg(back, "atributos devem ser diferentes");
        bonus[a2] = 2; bonus[a1] = 1;
      }
      const items = [...back.querySelectorAll(".bg-item-row")].map(row => ({
        tipo: row.querySelector(".bg-item-tipo").value,
        nome: row.querySelector(".bg-item-nome").value.trim(),
      })).filter(x => x.nome);

      const r = await fetch(`/api/personagens/${pid}/background`, {
        method: "PUT", headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ nome, bonus, items }),
      });
      const j = await r.json();
      if (!r.ok) return showMsg(back, "erro: " + (j.error || r.status));
      back.remove();
      await load();
    });
  }
  function showMsg(back, m) { back.querySelector("#bg-msg").textContent = "⚠ " + m; }
  function sumVals(o) { return Object.values(o).reduce((a,b)=>a+b, 0); }

  function bgBonusText(json) {
    if (!json) return "";
    try {
      const b = JSON.parse(json);
      const parts = Object.entries(b).map(([k,v]) => `+${v} ${k.slice(0,3).toUpperCase()}`);
      return parts.length ? ` <small style="color:#8b2e26">(${parts.join(", ")})</small>` : "";
    } catch (e) { return ""; }
  }

  async function pickRaca() {
    const racas = await api.racas();
    openPicker({
      title: "Escolha a Raça",
      options: racas,
      onPick: async (r) => {
        await api.patch({ Id_Raca: r.Id_Raca, Id_Linhagem: null, Id_Essencia: null, Id_EssLinhagem: null });
        await load();
        // cascata automática: abre linhagem em seguida
        setTimeout(() => pickLinhagem(r.Slug), 120);
      },
    });
  }

  async function pickLinhagem(racaSlug) {
    const lins = await api.linhagens(racaSlug);
    openPicker({
      title: `Escolha a Linhagem (${racaSlug})`,
      options: lins,
      onPick: async (l) => {
        if (l.__marker === "essencia") {
          // abre picker de essência
          return pickEssencia();
        }
        await api.patch({ Id_Linhagem: l.Id_Linhagem, Id_Essencia: null, Id_EssLinhagem: null });
        await load();
      },
    });
  }

  async function pickEssencia() {
    const ess = await api.essencias();
    openPicker({
      title: "Escolha a Essência",
      options: ess,
      onPick: async (e) => {
        await api.patch({ Id_Essencia: e.Id_Essencia, Id_Linhagem: null, Id_EssLinhagem: null });
        await load();
        // cascata para sub-linhagem da essência
        setTimeout(() => pickEssLinhagem(e.Slug, e.Nome), 120);
      },
    });
  }

  async function pickEssLinhagem(essSlug, essNome) {
    const lins = await api.essLinhagens(essSlug);
    if (!lins.length) return;
    openPicker({
      title: `Linhagem da Essência ${essNome}`,
      options: lins,
      renderOption: (o) => `<b>${o.Nome}</b><br><small>${o.Descricao || ""}</small>`,
      onPick: async (l) => {
        await api.patch({ Id_EssLinhagem: l.Id_EssLinhagem });
        await load();
      },
    });
  }

  async function pickClasse() {
    const cls = await api.classes();
    openPicker({
      title: "Escolha a Classe",
      options: cls,
      onPick: async (c) => {
        await api.patch({ Id_Classe: c.Id_Classe, Id_Subclasse: null });
        await load();
      },
    });
  }

  async function pickSubclasse() {
    if (!state.classe) { alert("Escolha uma classe antes."); return; }
    const subs = await api.subclasses(state.classe.Slug);
    if (!subs.length) { alert("Essa classe não tem subclasses cadastradas."); return; }
    openPicker({
      title: `Subclasse de ${state.classe.Nome}`,
      options: subs,
      onPick: async (s) => { await api.patch({ Id_Subclasse: s.Id_Subclasse }); await load(); },
    });
  }

  async function pickNivel() {
    const v = prompt("Nível (1-20):", state.personagem.Nivel);
    if (v == null) return;
    const n = Math.max(1, Math.min(20, parseInt(v, 10) || 1));
    await api.patch({ Nivel: n });
    await load();
  }

  async function pickAttr(key) {
    const cur = state.personagem.atributos[key];
    const v = prompt(`${key}:`, cur);
    if (v == null) return;
    await api.patch({ [key]: parseInt(v, 10) || 10 });
    await load();
  }

  async function pickPers(tipo) {
    const cur = (state.personalidade || []).find(p => p.Tipo === tipo);
    const v = prompt(`${tipo}:`, cur?.Texto || "");
    if (v == null) return;
    await fetch(`/api/personagens/${pid}/personalidade`, {
      method: "PUT", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ tipo, texto: v }),
    });
    await load();
  }

  async function pickNome() {
    const v = prompt("Nome:", state.personagem.Nome);
    if (!v) return;
    await api.patch({ Nome: v });
    await load();
  }

  // ---------- helpers ----------
  function talentCol(title, arr, addKind) {
    const addBtn = addKind
      ? `<button class="tal-add" data-pick-talento="${addKind}" title="Adicionar talento">+</button>`
      : "";
    const items = arr.length ? arr.map(t => `
      <div class="talent-item" title="${(t.Detalhes||"").replace(/"/g,"&quot;")}">
        <span>${t.Nome}</span>
        <span class="lvl">Nv ${t.Nivel || "?"}</span>
      </div>`).join("")
      : `<div class="talent-item" style="color:#bbb">—</div>`;
    return `<div class="talent-col"><h3>${title}${addBtn}</h3>${items}</div>`;
  }

  function renderSaves(state, prof) {
    // saves_proficientes vem do backend (classe.SavesJSON ∪ save-prof:* tags das habs ativas)
    const saves = Array.isArray(state.saves_proficientes) && state.saves_proficientes.length
      ? state.saves_proficientes
      : (state.classe?.SavesJSON ? JSON.parse(state.classe.SavesJSON) : []);
    const keys = [["Força","Forca"], ["Destreza","Destreza"], ["Constituição","Constituicao"],
      ["Inteligência","Inteligencia"], ["Sabedoria","Sabedoria"], ["Carisma","Carisma"]];
    return keys.map(([label, k]) => {
      const atr = atrFinal(state, k);
      const m = mod(atr);
      const isProf = saves.includes(k);
      const bonus = m + (isProf ? prof : 0);
      const dotCls = isProf ? "dot prof" : "dot";
      return `<div class="skill"><div class="${dotCls}"></div><div class="bonus">${sgn(bonus)}</div><div>${label}</div><div class="atr"></div></div>`;
    });
  }

  load();
})();
