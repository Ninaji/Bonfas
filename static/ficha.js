/* ==========================================================
   Ficha D&D 5.5 INTERATIVA — cascata de escolhas que auto-preenche
   ========================================================== */
(function () {
  "use strict";

  const pid = parseInt(location.pathname.split("/ficha/")[1], 10);
  if (!pid) { document.body.innerHTML = "<p style='padding:40px'>Informe um ID: /ficha/&lt;id&gt;</p>"; return; }

  const root = document.getElementById("ficha-root");
  let state = null;   // resposta /full

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

  // Retorna valor final do atributo (base + bônus de background)
  function atrFinal(state, key) {
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

  // ---------- MODAL de escolha ----------
  function openPicker({ title, options, onPick, renderOption }) {
    const back = document.createElement("div");
    back.className = "picker-backdrop";
    back.innerHTML = `
      <div class="picker">
        <div class="picker-head">${title}</div>
        <div class="picker-list"></div>
        <div class="picker-foot">
          <button class="picker-btn" data-close>Cancelar</button>
        </div>
      </div>`;
    const list = back.querySelector(".picker-list");
    options.forEach(opt => {
      const item = document.createElement("button");
      item.className = "picker-item";
      item.innerHTML = renderOption
        ? renderOption(opt)
        : `<b>${opt.Nome}</b>${opt.Tagline ? `<br><small>${opt.Tagline}</small>` : ""}${opt.Descricao ? `<br><small>${opt.Descricao}</small>` : ""}`;
      item.addEventListener("click", () => { close(); onPick(opt); });
      list.appendChild(item);
    });
    back.addEventListener("click", (e) => { if (e.target === back || e.target.dataset.close !== undefined) close(); });
    document.body.appendChild(back);
    function close() { back.remove(); }
  }

  // ---------- Render principal ----------
  async function load() {
    state = await api.full();
    render();
  }

  function render() {
    const p = state.personagem;
    const atribs = p.atributos || {};
    const esc = p.escolha || {};
    const skips = [];

    const el = document.createElement("div");
    el.className = "ficha";

    // ===== HEADER =====
    const classeTit = (state.classe ? state.classe.Nome : "<i>clique para escolher</i>") + " " + (p.Nivel || 0);
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
          <div class="meta-line clickable" data-pick="classe"><span class="t">${classeTit}</span><span>CLASSE(S) & NÍVEIS</span></div>
          <div class="meta-line clickable" data-pick="subclasse"><span>${state.subclasse ? state.subclasse.Nome : "<i>subclasse…</i>"}</span><span>SUBCLASSE</span></div>
          <div class="meta-line clickable" data-pick="raca"><span>${racaTit}</span><span>RAÇA</span></div>
          <div class="meta-line clickable" data-pick="background"><span>${p.BackgroundNome || "<i>clique para escolher</i>"}${bgBonusText(p.BackgroundBonusJSON)}</span><span>BACKGROUND</span></div>
          <div class="meta-line"><span>${p.Aventuras ?? "—"}</span><span>AVENTURAS</span></div>
          <div class="meta-line"><span>${p.ProximoNivel ?? "—"}</span><span>PRÓXIMO NÍVEL</span></div>
        </div>
        <div class="f-level clickable" data-pick="nivel">
          <div class="lvnum">${p.Nivel || 0}</div>
          <div class="lvlbl">NÍVEL</div>
        </div>
      </div>`);

    // ===== MAIN =====
    // bônus de background (aplicado DEPOIS da rolagem base)
    const bgBonus = p.BackgroundBonusJSON ? JSON.parse(p.BackgroundBonusJSON) : {};
    const attrsHTML = [
      ["FOR","Forca"], ["DES","Destreza"], ["CON","Constituicao"],
      ["INT","Inteligencia"], ["SAB","Sabedoria"], ["CAR","Carisma"],
    ].map(([l, k]) => {
      const base = atribs[k];
      const bb = bgBonus[k] || 0;
      const total = (base || 0) + bb;
      const bonusMark = bb ? `<span class="bg-mark">+${bb}</span>` : "";
      return `<div class="attr clickable" data-pick="attr" data-attr="${k}">
        <div class="lbl">${l}</div>
        <div class="vals"><div class="mod">${sgn(mod(total))}</div><div class="raw">${total??'?'}${bonusMark}</div></div>
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
    const hd     = state.classe?.DadoVida;
    const conFin = atrFinal(state, "Constituicao");
    const pvMax  = calcPVMax(hd, p.Nivel || 1, mod(conFin)) ?? p.PVMaximo ?? "?";
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
            <div class="ca-circle"><div class="v">${p.CA ?? "?"}</div><div class="l">CA</div></div>
            <div class="ca-circle"><div class="v">${sgn(p.Iniciativa ?? mod(atribs.Destreza))}</div><div class="l">INIC</div></div>
            <div class="ca-circle"><div class="v">${p.Velocidade || "?"}</div><div class="l">VEL</div></div>
          </div>
          <div class="f-hp">
            <div class="big">${pvMax}</div>
            <div class="lbl">Pontos de Vida Máximos</div>
            <div class="mini"><small style="color:#888">${hd || "?"} · nv ${p.Nivel || 1} · CON ${sgn(mod(conFin))}</small></div>
            ${(state.inventario || []).filter(i => i.Sintonizado).length
                ? `<ul>${state.inventario.filter(i => i.Sintonizado).map(i => `<li>${i.Item}</li>`).join("")}</ul>
                   <div class="lbl">Itens Sintonizados</div>`
                : `<div class="lbl" style="color:#bbb">sem sintonizados</div>`}
          </div>
          <div class="f-patent">
            <div class="name"><div>${p.Patente || "—"}<small>PATENTE</small></div></div>
            <div class="icon">◈</div>
          </div>
        </div>
        <div class="f-right">
          <div class="persona-slot clickable" data-pick="pers" data-tipo="traco"><span class="tag">Traços</span>${pers.traco || "<i>clique para editar</i>"}</div>
          <div class="persona-slot clickable" data-pick="pers" data-tipo="ideal"><span class="tag">Ideias</span>${pers.ideal || "<i>clique para editar</i>"}</div>
          <div class="persona-slot clickable" data-pick="pers" data-tipo="vinculo"><span class="tag">Vínculos</span>${pers.vinculo || "<i>clique para editar</i>"}</div>
          <div class="persona-slot clickable" data-pick="pers" data-tipo="defeito"><span class="tag">Defeitos</span>${pers.defeito || "<i>clique para editar</i>"}</div>
        </div>
      </div>`);

    // ===== Features de classe (preto) + subclasse (cor do brand) + traços raciais =====
    const fmtHab = (h, origem) => {
      const hasChoice = !!h.TemEscolha;
      const nivelOK = (p.Nivel || 1) >= (h.NivelAdquirido || 1);
      const isArquetipo = /Arqu[ée]tipo/i.test(h.Nome);
      const isLista = /manobra/i.test(h.Nome);
      const vinculadas = (state.tecnicas || []).filter(t => t.Id_Habilidade === h.Id_Habilidade);
      const escolhido = isArquetipo
        ? (state.subclasse?.Nome || "")
        : isLista
          ? (vinculadas.length ? vinculadas.map(t => t.Nome).join(", ") : "")
          : (h.OpcaoEscolhida || "");

      // pin pequeno à direita do título
      let pin = "";
      if (hasChoice || isArquetipo) {
        if (!nivelOK) pin = `<span class="hab-pin locked" title="Adquire no Nv ${h.NivelAdquirido}">🔒</span>`;
        else pin = `<span class="hab-pin ${escolhido ? "ok" : "todo"}">${escolhido ? "✓" : "⚙"}</span>`;
      }

      // attrs para o handler escolher quem (arquetipo / outras)
      const kind = isArquetipo ? "arquetipo" : "default";
      const clickable = (hasChoice || isArquetipo) && nivelOK;

      return `<div class="feat-card feat-${origem} ${clickable ? "clickable" : ""} ${!nivelOK ? "hab-locked" : ""}"
                   data-hab-id="${h.Id_Habilidade||""}"
                   data-has-choice="${clickable ? 1 : 0}"
                   data-kind="${kind}">
        <div class="feat-card-head">
          <span class="feat-nome">${h.Nome}</span>
          <span class="feat-nivel">Nv ${h.NivelAdquirido || 1}</span>
          ${pin}
        </div>
        ${escolhido ? `<div class="feat-card-choice">→ <em>${escolhido}</em></div>` : ""}
        <div class="feat-card-desc">${h.Descricao || ""}</div>
      </div>`;
    };
    // features com "Manobras de Combate..." são roteadas para a seção Técnicas
    // e omitidas das colunas de classe/subclasse (evita duplicação).
    const isManobraFeature = (h) => /^Manobras de Combate/i.test(h.Nome);
    const habCls  = (state.habilidades_classe || []).filter(h => !isManobraFeature(h)).map(h => fmtHab(h, "classe")).join("");
    const habSub  = (state.habilidades_subclasse || []).filter(h => !isManobraFeature(h)).map(h => fmtHab(h, "subclasse")).join("");
    const tracosR = (state.tracos || []).map(t => `<div class="feat-item feat-raca">${t.Nome}</div>`).join("");
    el.insertAdjacentHTML("beforeend", `
      <div class="f-features f-features-grid">
        <div class="feat-col">
          <div class="feat-head">Classe${state.classe ? ` · ${state.classe.Nome}` : ""}</div>
          ${habCls || `<div class="feat-item" style="color:#bbb">—</div>`}
        </div>
        <div class="feat-col">
          <div class="feat-head">Subclasse${state.subclasse ? ` · ${state.subclasse.Nome}` : ""}</div>
          ${habSub || `<div class="feat-item" style="color:#bbb">—</div>`}
        </div>
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
    const asiNiveis = state.classe?.ASINiveisJSON ? JSON.parse(state.classe.ASINiveisJSON) : [];
    const talsClasse = (state.talentos || []).filter(t => t.Categoria === "classe");

    const tierSlot = (cat, tier, arr, rotulo) => {
      const locked = nivelAtual < tier;
      const t = arr.find(x => (x.Nivel || 1) === tier);
      const lockIcon = locked ? "🔒 " : "";
      const label = t
        ? `<span class="tal-nome">${lockIcon}${t.Nome}</span><small>${(t.Detalhes||"").slice(0,40)}</small>`
        : `<i>${lockIcon}${rotulo} — clique para ${locked ? "planejar" : "escolher"}</i>`;
      const cls = locked ? (t ? "locked filled" : "locked empty") : (t ? "filled" : "empty");
      return `<div class="tier-slot ${cls}" data-pick-tier="${cat}" data-tier="${tier}" data-talid="${t?.Id_Talento||""}" data-locked="${locked ? 1 : 0}">${label}</div>`;
    };

    // Coluna Raça+Essência (combinada)
    const colRacEss = `
      <div class="talent-col tier-col">
        <h3>Talentos de Raça / Essência</h3>
        ${TIERS_RACIAIS.map(nv => tierSlot("racess", nv, talsRacEss, `Nv ${nv}+`)).join("")}
      </div>`;

    // Coluna Classe (slots nos níveis de ASI)
    const colClasse = asiNiveis.length ? `
      <div class="talent-col tier-col">
        <h3>Talentos de Classe <small>(${state.classe?.Nome || "?"})</small></h3>
        ${asiNiveis.map(nv => tierSlot("classe", nv, talsClasse, `Nv ${nv}`)).join("")}
      </div>` : `
      <div class="talent-col tier-col">
        <h3>Talentos de Classe</h3>
        <div class="tier-slot locked">escolha uma classe primeiro</div>
      </div>`;

    el.insertAdjacentHTML("beforeend", `
      <div class="sec-grid" style="grid-template-columns:1fr 1fr;">
        ${colRacEss}
        ${colClasse}
      </div>`);

    // ===== Idiomas + Percepção =====
    const idiomas = (state.idiomas || []).filter(x => x.Tipo === "idioma").map(x => x.Nome).join(", ");
    const ferram  = (state.idiomas || []).filter(x => x.Tipo === "ferramenta").map(x => x.Nome).join(", ");
    el.insertAdjacentHTML("beforeend", `
      <div class="sec-grid" style="grid-template-columns:1fr 2fr;">
        <div class="box" style="text-align:center;">
          <h3>Percepção Passiva</h3>
          <div style="font-size:36px; font-weight:700; color:var(--accent);">${p.PercepcaoPassiva ?? "?"}</div>
        </div>
        <div class="box">
          <h3>Idiomas & Ferramentas</h3>
          <div style="font-size:12px; line-height:1.5;">
            <b>Idiomas:</b> ${idiomas || "—"}<br>
            <b>Ferramentas/Outros:</b> ${ferram || "—"}
          </div>
        </div>
      </div>`);

    // ===== Resistências (+ auto da linhagem da essência) =====
    const rs = state.resistencias || [];
    const autoResist = state.auto_efeitos?.resistencia;
    const byRes = (t) => {
      const manual = rs.filter(r => r.Tipo === t).map(r => `<div class="r">${r.DanoTipo}</div>`);
      if (t === "resistencia" && autoResist) {
        manual.push(`<div class="r auto" title="De ${state.auto_efeitos.origem}">${autoResist} <small>★</small></div>`);
      }
      return manual.join("") || `<div class="r" style="color:#ccc">—</div>`;
    };
    el.insertAdjacentHTML("beforeend", `
      <div class="resist-wrap">
        <div class="resist-box"><h4>Resistências</h4>${byRes("resistencia")}</div>
        <div class="resist-box"><h4>Imunidades</h4>${byRes("imunidade")}</div>
        <div class="resist-box"><h4>Vulnerabilidades</h4>${byRes("vulnerabilidade")}</div>
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

    // ===== Técnicas — N slots fixos (N = state.limites.manobras da tabela de progressão) =====
    const manobraFeatures = [...(state.habilidades_classe || []), ...(state.habilidades_subclasse || [])]
      .filter(isManobraFeature);
    const temManobraFeature = manobraFeatures.length > 0;
    if (temManobraFeature) {
      const limite   = parseInt(state.limites?.manobras, 10) || 0;
      const tecnicas = state.tecnicas || [];
      const atuais   = tecnicas.length;

      // gera N slots (mesmo padrão dos tier-slots de talentos raça/essência)
      const slotsHTML = Array.from({ length: limite }).map((_, i) => {
        const t = tecnicas[i];
        if (t) {
          return `<div class="tier-slot filled" data-pick-tecnica-slot data-tid="${t.Id}" title="${(t.Descricao||"").replace(/"/g,"&quot;").slice(0,250)}">
            <span class="tal-nome">${t.Nome}</span>
          </div>`;
        }
        return `<div class="tier-slot empty" data-pick-tecnica-slot><i>Manobra ${i+1} — clique para escolher</i></div>`;
      }).join("");

      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list tech-slots">
          <h3>Técnicas <small class="tech-count">${atuais}/${limite}</small></h3>
          <div class="tech-slots-grid">${slotsHTML}</div>
        </div>`);
    } else if ((state.tecnicas || []).length) {
      // fallback legado: classe sem limite calculado → apenas lista as técnicas existentes
      el.insertAdjacentHTML("beforeend", `
        <div class="tech-list">
          <h3>Técnicas</h3>
          ${state.tecnicas.map(t => `<div class="tech-item"><span class="n">${t.Nome}.</span>${t.Descricao || ""}</div>`).join("")}
        </div>`);
    }

    // ===== Magias ===== (só se classe for full/half OU subclasse for third)
    const classeConj   = state.classe?.Conjuracao;     // 'full' | 'half' | 'none'
    const subConj      = state.subclasse?.Conjuracao;  // 'third' | null
    const isSpellcaster = (classeConj === "full" || classeConj === "half" || subConj === "third");

    if (isSpellcaster) {
      const byLv = {};
      for (const m of (state.magias || [])) (byLv[m.Nivel] ||= []).push(m);
      // injeta auto-efeitos da linhagem da essência (sempre disponíveis)
      const ae = state.auto_efeitos || {};
      if (ae.truque) (byLv[0] ||= []).push({ Nome: ae.truque + " ⟵ linhagem", Preparada: 1, __auto: 1 });
      if (ae.magia_n3) (byLv[1] ||= []).push({ Nome: ae.magia_n3 + " (1×/descanso longo ⟵ linhagem)", Preparada: 1, __auto: 1 });
      // níveis exibidos baseados em tipo de caster
      const maxLv = classeConj === "full" ? 9
                  : classeConj === "half" ? 5
                  : 4;   // third
      const levels = [];
      for (let i = 0; i <= maxLv; i++) levels.push(String(i));
      const grid = levels.map(lv => {
        const list = byLv[lv] || [];
        return `
        <div class="spell-level">
          <h4>${lv === "0" ? "Truques" : `Nível ${lv}`}</h4>
          <ul>${list.length
              ? list.map(m => `<li class="${m.Preparada ? "prep" : ""}">${m.Preparada ? "☑ " : "☐ "}${m.Nome}</li>`).join("")
              : `<li style="color:#bbb; font-style:italic;">—</li>`}</ul>
        </div>`;
      }).join("");
      const tipoLabel = classeConj === "full" ? "Conjurador Pleno"
                      : classeConj === "half" ? "Meio-Conjurador"
                      : "Conjurador de Subclasse (1/3)";
      el.insertAdjacentHTML("beforeend", `
        <div class="sec-label">Magias — ${tipoLabel}</div>
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

    root.innerHTML = "";
    root.appendChild(el);
    wireClicks();
  }

  // ---------- Wiring dos cliques ----------
  function wireClicks() {
    root.querySelectorAll("[data-pick]").forEach(elem => {
      elem.addEventListener("click", () => onPick(elem.dataset.pick, elem.dataset));
    });
    // slots de técnicas/manobras — mesmo padrão dos talentos de raça/essência
    root.querySelectorAll("[data-pick-tecnica-slot]").forEach(slot => {
      slot.addEventListener("click", async () => {
        const tid = slot.dataset.tid;
        if (tid) {
          if (!confirm("Remover esta manobra?")) return;
          await fetch(`/api/personagens/${pid}/tecnicas/${tid}`, { method: "DELETE" });
          await load();
        } else {
          openTecnicasModal();
        }
      });
    });

    // cards de habilidade clicáveis (escolha embutida ou arquétipo)
    root.querySelectorAll(".feat-card[data-has-choice='1']").forEach(elem => {
      elem.addEventListener("click", async () => {
        const kind = elem.dataset.kind;
        if (kind === "arquetipo") {
          return pickSubclasse();      // cascata: abre picker das subclasses
        }
        const hid = parseInt(elem.dataset.habId, 10);
        if (!hid) return;
        const h = [...(state.habilidades_classe || []), ...(state.habilidades_subclasse || [])]
          .find(x => x.Id_Habilidade === hid);
        if (!h) return;
        const nv = state.personagem.Nivel || 1;
        if (nv < (h.NivelAdquirido || 1)) return;
        openHabModal(h);
      });
    });

    root.querySelectorAll("[data-pick-tier]").forEach(elem => {
      elem.addEventListener("click", (e) => {
        e.stopPropagation();
        const cat  = elem.dataset.pickTier;   // 'racess' | 'classe'
        const tier = parseInt(elem.dataset.tier, 10);
        const talId = elem.dataset.talid;
        if (talId) {
          if (confirm("Remover este talento?")) {
            fetch(`/api/personagens/${pid}/talentos/${talId}`, { method: "DELETE" })
              .then(() => load());
          }
          return;
        }
        if (cat === "classe") return pickTalentoClasse(tier);
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

  // ---------- slot Classe (texto livre por ora) ----------
  async function pickTalentoClasse(tier) {
    const v = prompt(`Talento de Classe — Nv ${tier}\n(use este slot para ASI ou um talento geral)`, "");
    if (!v) return;
    // salva direto em TB_PersonagemTalento via endpoint genérico (precisa criar se não existe)
    await fetch(`/api/personagens/${pid}/talento-manual`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ categoria: "classe", nivel: tier, nome: v.trim() }),
    });
    await load();
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

  // ---------- modal genérico de habilidade com escolha ----------
  function openHabModal(h) {
    // modo "lista" se o nome mencionar Manobra/Manobras → salva em TB_PersonagemTecnica
    const isLista = /manobra/i.test(h.Nome);
    const tecnicasVinculadas = (state.tecnicas || []).filter(t => t.Id_Habilidade === h.Id_Habilidade);
    const atual = h.OpcaoEscolhida || "";

    const back = document.createElement("div");
    back.className = "picker-backdrop";
    back.innerHTML = `
      <div class="picker hab-modal">
        <div class="picker-head">${h.Nome} <small style="font-weight:400">· Nv ${h.NivelAdquirido}</small></div>
        <div class="picker-list hab-body">
          <div class="hab-desc">${h.Descricao || ""}</div>
          <div class="hab-edit">
            ${isLista ? `
              <h4 class="hab-edit-h">Itens selecionados (${tecnicasVinculadas.length})</h4>
              <div class="hab-tec-list">
                ${tecnicasVinculadas.map(t => `
                  <div class="hab-tec-row">
                    <span>${t.Nome}</span>
                    <button data-del-tid="${t.Id}" class="hab-tec-del">remover</button>
                  </div>`).join("") || `<div style="color:#999; font-style:italic;">nenhum ainda</div>`}
              </div>
              <div class="hab-tec-add">
                <input type="text" id="hab-tec-nome" placeholder="Nome da manobra/item">
                <button id="hab-tec-save" class="picker-btn bg-save">+ adicionar</button>
              </div>`
            : `
              <h4 class="hab-edit-h">Sua escolha</h4>
              <textarea id="hab-text" rows="3" placeholder="digite sua escolha aqui...">${atual.replace(/"/g,"&quot;")}</textarea>
              <button id="hab-save" class="picker-btn bg-save">Salvar</button>`}
          </div>
        </div>
        <div class="picker-foot">
          <button class="picker-btn" data-close>Fechar</button>
        </div>
      </div>`;
    document.body.appendChild(back);
    back.addEventListener("click", (e) => {
      if (e.target === back || e.target.dataset.close !== undefined) back.remove();
    });

    if (isLista) {
      back.querySelector("#hab-tec-save").addEventListener("click", async () => {
        const nome = back.querySelector("#hab-tec-nome").value.trim();
        if (!nome) return;
        await fetch(`/api/personagens/${pid}/tecnicas`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ nome, id_habilidade: h.Id_Habilidade }),
        });
        back.remove();
        await load();
        // reabre o mesmo modal com a lista atualizada
        const hh = [...(state.habilidades_classe||[]), ...(state.habilidades_subclasse||[])]
          .find(x => x.Id_Habilidade === h.Id_Habilidade);
        if (hh) openHabModal(hh);
      });
      back.querySelectorAll("[data-del-tid]").forEach(btn => {
        btn.addEventListener("click", async () => {
          const tid = btn.dataset.delTid;
          await fetch(`/api/personagens/${pid}/tecnicas/${tid}`, { method: "DELETE" });
          back.remove();
          await load();
          const hh = [...(state.habilidades_classe||[]), ...(state.habilidades_subclasse||[])]
            .find(x => x.Id_Habilidade === h.Id_Habilidade);
          if (hh) openHabModal(hh);
        });
      });
    } else {
      back.querySelector("#hab-save").addEventListener("click", async () => {
        const v = back.querySelector("#hab-text").value.trim();
        await fetch(`/api/personagens/${pid}/habilidade-opcao/${h.Id_Habilidade}`, {
          method: "PUT", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ texto: v }),
        });
        back.remove();
        await load();
      });
    }
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

          <div class="bg-items-label">Escolha 2: ferramentas ou idiomas</div>
          <div class="bg-items" id="bg-items">
            ${[0,1].map(i => `
              <div class="bg-item-row">
                <select class="bg-item-tipo">
                  <option value="ferramenta" ${atualItems[i]?.Tipo==="ferramenta" ? "selected":""}>Ferramenta</option>
                  <option value="idioma"     ${atualItems[i]?.Tipo==="idioma"     ? "selected":""}>Idioma</option>
                </select>
                <input type="text" class="bg-item-nome" placeholder="digite o nome" value="${(atualItems[i]?.Nome||"").replace(/"/g,"&quot;")}">
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
    const saves = state.classe?.SavesJSON ? JSON.parse(state.classe.SavesJSON) : [];
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
