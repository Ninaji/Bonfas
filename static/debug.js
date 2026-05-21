/* ============================================================================
   Bonfas Debug — TagsJSON editor (5 entidades + modal de add).
   Estado: chip-list por bloco com edit local; PUT só ao clicar em "Salvar".
   ============================================================================ */
"use strict";

// ---------------------------------------------------------------- canonics
const ELEMENTOS = [
  "Ácido", "Concussão", "Cortante", "Energia", "Fogo", "Frio",
  "Necrótico", "Perfurante", "Psíquico", "Radiante", "Raio",
  "Trovejante", "Veneno",
];
const CONDICOES = [
  "Agarrado", "Amedrontado", "Atordoado", "Caído", "Cego",
  "Enfeitiçado", "Envenenado", "Exaustão", "Incapacitado",
  "Inconsciente", "Invisível", "Paralisado", "Petrificado",
  "Restringido", "Surdo",
];
const ATRIBUTOS = ["Forca", "Destreza", "Constituicao", "Inteligencia", "Sabedoria", "Carisma"];

function tagToString(t) {
  if (typeof t === "string") return t;
  if (t && typeof t.tag === "string") {
    let s = t.tag;
    // n_por_nivel — exibe como tag:nv(1=3,4=4,...) pra leitura rápida
    if (t.n_por_nivel && typeof t.n_por_nivel === "object") {
      const pares = Object.entries(t.n_por_nivel)
        .map(([k, v]) => `${k}=${v}`)
        .sort((a, b) => parseInt(a) - parseInt(b))
        .join(",");
      if (pares) s = `${s}:nv(${pares})`;
    }
    const flt = Array.isArray(t.filter) ? t.filter : null;
    if (flt && flt.length) s = `${s}=${flt.join("|")}`;
    return s;
  }
  return String(t);
}

function tagClassFor(s) {
  if (s.startsWith("pick:"))                    return "pick";
  if (s.startsWith("expertise:"))               return "exp";
  if (s.startsWith("prof:"))                    return "prof";
  if (s.startsWith("save-prof"))                return "save";
  if (s.startsWith("resist:"))                  return "resist";
  if (s.startsWith("immune:"))                  return "immune";
  if (s.startsWith("vuln:"))                    return "vuln";
  if (s.startsWith("cond-immune:"))             return "immune";
  if (s.startsWith("adv-cond:"))                return "save";
  if (s.match(/^(andar|voar|nadar|cavar):/))    return "move";
  return "";
}

function isCanonicalWarn(s) {
  const body = s.split("=", 1)[0];
  if (body.startsWith("resist:") || body.startsWith("immune:") || body.startsWith("vuln:")) {
    const v = body.split(":")[1];
    return ELEMENTOS.includes(v) ? null : `'${v}' não é elemento canônico`;
  }
  if (body.startsWith("cond-immune:") || body.startsWith("adv-cond:")) {
    const v = body.split(":")[1];
    return CONDICOES.includes(v) ? null : `'${v}' não é condição canônica`;
  }
  return null;
}

// ---------------------------------------------------------------- DOM utils
function el(tag, props = {}, ...children) {
  const e = document.createElement(tag);
  for (const k in props) {
    if (k === "class")        e.className = props[k];
    else if (k === "dataset") Object.assign(e.dataset, props[k]);
    else if (k.startsWith("on")) e.addEventListener(k.slice(2).toLowerCase(), props[k]);
    else                      e[k] = props[k];
  }
  children.flat().forEach(c => {
    if (c == null || c === "") return;
    e.append(c?.nodeType ? c : document.createTextNode(String(c)));
  });
  return e;
}

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

// ---------------------------------------------------------------- block
function renderBlock({ table, id, title, nivel, raw }) {
  let tags = [];
  try {
    tags = raw ? (JSON.parse(raw) || []) : [];
  } catch { tags = []; }

  const blk = el("div", { class: "block", dataset: { table, id: String(id) } });

  const titleNode = el("div", { class: "block-title" });
  if (nivel != null) titleNode.append(el("span", { class: "nivel" }, `Nv ${nivel}`));
  titleNode.append(document.createTextNode(title));

  const head = el("div", { class: "block-head" },
    titleNode,
    el("div", { class: "block-id" }, `${table} · ${id}`),
  );

  const chips = el("div", { class: "tag-list" });

  function rerenderChips() {
    clearChildren(chips);
    if (!tags.length) {
      chips.append(el("span", { class: "chip-empty" }, "(sem tags)"));
      return;
    }
    tags.forEach((t, idx) => {
      const s = tagToString(t);
      const warn = isCanonicalWarn(s);
      const cls = `chip ${tagClassFor(s)} ${warn ? "warn" : ""}`.trim();
      const chip = el("span", { class: cls, title: warn || "" },
        s,
        el("span", {
          class: "x",
          onclick: () => { tags.splice(idx, 1); rerenderChips(); markDirty(); },
        }, "×"),
      );
      chips.append(chip);
    });
  }

  const flash = el("span", { class: "flash" });
  function markDirty() {
    flash.textContent = "modificado";
    flash.className = "flash warn";
  }

  let rawEditor = null;
  function openRawEditor() {
    if (rawEditor) { rawEditor.remove(); rawEditor = null; return; }
    rawEditor = el("textarea", {
      class: "json-edit",
      value: JSON.stringify(tags, null, 2),
      oninput: ev => {
        try {
          tags = JSON.parse(ev.target.value) || [];
          ev.target.classList.remove("dirty");
          rerenderChips();
          markDirty();
        } catch { ev.target.classList.add("dirty"); }
      },
    });
    blk.append(rawEditor);
  }

  async function save() {
    flash.textContent = "salvando…";
    flash.className = "flash";
    try {
      const r = await fetch(`/api/debug/tags/${table}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags: JSON.stringify(tags) }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || r.statusText);
      flash.textContent = j.warnings?.length
        ? `salvo (warnings: ${j.warnings.length})`
        : "salvo ✓";
      flash.className = `flash ${j.warnings?.length ? "warn" : ""}`;
      if (j.warnings?.length) console.warn("debug-tags warnings:", j.warnings);
    } catch (e) {
      flash.textContent = `erro: ${e.message}`;
      flash.className = "flash err";
    }
  }

  const actions = el("div", { class: "block-actions" },
    el("button", { class: "tiny",
      onclick: () => openAddTagModal(t => { tags.push(t); rerenderChips(); markDirty(); }),
    }, "+ Tag"),
    el("button", { class: "tiny", onclick: openRawEditor }, "Editar JSON cru"),
    el("button", { class: "tiny primary", onclick: save }, "Salvar"),
    flash,
  );

  rerenderChips();
  blk.append(head, chips, actions);
  return blk;
}

// ---------------------------------------------------------------- group
function renderGroup({ title, meta, table, id, raw, children, startCollapsed = false }) {
  const grp = el("div", { class: "group" + (startCollapsed ? " collapsed" : "") });
  const header = el("div", { class: "group-header" },
    el("div", { class: "title" }, title),
    el("div", { class: "meta" }, meta || ""),
  );
  header.addEventListener("click", () => grp.classList.toggle("collapsed"));
  grp.append(header);

  const body = el("div", { class: "group-body" });
  if (table && id != null) {
    body.append(renderBlock({ table, id, title: `(linha-mãe) ${title}`, raw }));
  }
  children?.forEach(child => child && body.append(child));
  grp.append(body);
  return grp;
}

function section(title, blocks) {
  if (!blocks.length) return null;
  const s = el("div", { class: "subgroup-section" });
  if (title) s.append(el("h4", {}, title));
  blocks.forEach(b => s.append(b));
  return s;
}

// ---------------------------------------------------------------- renderers
function renderClasses(data) {
  const root = el("div");
  data.groups.forEach(c => {
    const habsBase = (c.habs_base || []).map(h => renderBlock({
      table: "TB_ClasseHabilidade", id: h.Id_Habilidade,
      title: h.Nome + (h.OpcaoTipoJSON ? "  ⊕ tem escolha" : ""),
      nivel: h.NivelAdquirido, raw: h.TagsJSON,
    }));
    const subsRendered = (c.subclasses || []).map(s => {
      const habs = (s.habs || []).map(h => renderBlock({
        table: "TB_ClasseHabilidade", id: h.Id_Habilidade,
        title: h.Nome + (h.OpcaoTipoJSON ? "  ⊕ tem escolha" : ""),
        nivel: h.NivelAdquirido, raw: h.TagsJSON,
      }));
      return renderGroup({
        title: `Subclasse · ${s.Nome}`, meta: `${habs.length} habs`,
        table: "TB_Subclasse", id: s.Id_Subclasse, raw: s.TagsJSON,
        children: habs.length ? [section("Habilidades", habs)] : [],
        startCollapsed: true,
      });
    });
    const children = [];
    const sectHabs = section("Habilidades de classe (sem subclasse)", habsBase);
    if (sectHabs) children.push(sectHabs);
    if (subsRendered.length) children.push(section("Subclasses", subsRendered));
    root.append(renderGroup({
      title: c.Nome, meta: `${(c.habs_base||[]).length} habs · ${(c.subclasses||[]).length} subs`,
      table: "TB_Classe", id: c.Id_Classe, raw: c.TagsJSON,
      children, startCollapsed: true,
    }));
  });
  return root;
}

function renderTalentos(data) {
  const root = el("div");
  const byFonte = {};
  (data.racial || []).forEach(t => { (byFonte[t.Fonte || "?"] ||= []).push(t); });
  Object.keys(byFonte).sort().forEach(fonte => {
    const blocks = byFonte[fonte].map(t => renderBlock({
      table: "TB_TalentoRacial", id: t.Id_TalentoRacial,
      title: t.Nome, nivel: t.NivelMinimo, raw: t.TagsJSON,
    }));
    root.append(renderGroup({
      title: `Talentos raciais · ${fonte}`, meta: `${blocks.length}`,
      children: [section("", blocks)].filter(Boolean),
      startCollapsed: true,
    }));
  });
  const blocksOG = (data.origem_e_geral || []).map(t => renderBlock({
    table: "TB_OpcaoJogo", id: t.Id_Opcao,
    title: `${t.Nome}  · ${t.Tipo}`, raw: t.TagsJSON,
  }));
  if (blocksOG.length) {
    root.append(renderGroup({
      title: "Talentos de Origem / Gerais", meta: `${blocksOG.length}`,
      children: [section("", blocksOG)],
      startCollapsed: true,
    }));
  }
  return root;
}

function renderRacas(data) {
  const root = el("div");
  data.groups.forEach(r => {
    const tracosBase = (r.tracos_base || []).map(t => renderBlock({
      table: "TB_TracoRacial", id: t.Id_Traco,
      title: t.Nome, nivel: t.NivelRequisito, raw: t.TagsJSON,
    }));
    const talentosRaciais = (r.talentos_raciais || []).map(t => renderBlock({
      table: "TB_TalentoRacial", id: t.Id_TalentoRacial,
      title: t.Nome, nivel: t.NivelMinimo, raw: t.TagsJSON,
    }));
    const linhagens = (r.linhagens || []).map(li => {
      const tcs = (li.tracos || []).map(t => renderBlock({
        table: "TB_TracoRacial", id: t.Id_Traco,
        title: t.Nome, nivel: t.NivelRequisito, raw: t.TagsJSON,
      }));
      return renderGroup({
        title: `Linhagem · ${li.Nome}`, meta: `${tcs.length} traços`,
        table: "TB_Linhagem", id: li.Id_Linhagem, raw: li.TagsJSON,
        children: tcs.length ? [section("Traços", tcs)] : [],
        startCollapsed: true,
      });
    });
    const children = [];
    const sBase = section("Traços de raça (base)", tracosBase);
    if (sBase) children.push(sBase);
    const sTal = section("Talentos raciais", talentosRaciais);
    if (sTal) children.push(sTal);
    if (linhagens.length) children.push(section("Linhagens", linhagens));
    root.append(renderGroup({
      title: r.Nome,
      meta: `${(r.tracos_base||[]).length} traços base · ${(r.talentos_raciais||[]).length} talentos · ${(r.linhagens||[]).length} linhagens`,
      table: "TB_Raca", id: r.Id_Raca, raw: r.TagsJSON,
      children, startCollapsed: false,
    }));
  });
  return root;
}

function renderEssencias(data) {
  const root = el("div");
  data.groups.forEach(e => {
    const tracosBase = (e.tracos_base || []).map(t => renderBlock({
      table: "TB_TracoRacial", id: t.Id_Traco,
      title: t.Nome, nivel: t.NivelRequisito, raw: t.TagsJSON,
    }));
    const talentosRaciais = (e.talentos_raciais || []).map(t => renderBlock({
      table: "TB_TalentoRacial", id: t.Id_TalentoRacial,
      title: t.Nome, nivel: t.NivelMinimo, raw: t.TagsJSON,
    }));
    const subs = (e.sublinhagens || []).map(sl => {
      const tcs = (sl.tracos || []).map(t => renderBlock({
        table: "TB_TracoRacial", id: t.Id_Traco,
        title: t.Nome, nivel: t.NivelRequisito, raw: t.TagsJSON,
      }));
      // post-R4: Elemento/TruqueNome viraram tags (resist:*, truque-inato:*).
      // Meta vem das tags pra preview rápido.
      let _meta_parts = [];
      try {
        const tags = JSON.parse(sl.TagsJSON || "[]") || [];
        for (const t of tags) {
          if (typeof t !== "string") continue;
          if (t.startsWith("resist:")) _meta_parts.push("elem: " + t.split(":")[1]);
          if (t.startsWith("truque-inato:")) _meta_parts.push("truque: " + t.split(":")[1]);
        }
      } catch {}
      const meta = _meta_parts.join(" · ");
      return renderGroup({
        title: `Sub-linhagem · ${sl.Nome}`, meta: `${tcs.length} traços · ${meta}`,
        table: "TB_EssenciaLinhagem", id: sl.Id_EssLinhagem, raw: sl.TagsJSON,
        children: tcs.length ? [section("Traços", tcs)] : [],
        startCollapsed: true,
      });
    });
    const children = [];
    const sBase = section("Traços de essência (base)", tracosBase);
    if (sBase) children.push(sBase);
    const sTal = section("Talentos raciais", talentosRaciais);
    if (sTal) children.push(sTal);
    if (subs.length) children.push(section("Sub-linhagens", subs));
    root.append(renderGroup({
      title: e.Nome,
      meta: `${(e.tracos_base||[]).length} traços base · ${(e.talentos_raciais||[]).length} talentos · ${(e.sublinhagens||[]).length} sub-linhagens`,
      table: "TB_Essencia", id: e.Id_Essencia, raw: e.TagsJSON,
      children, startCollapsed: false,
    }));
  });
  return root;
}

function renderItems(data) {
  const root = el("div");
  const bySlot = {};
  (data.items || []).forEach(it => { (bySlot[it.SlotNome || "(sem slot)"] ||= []).push(it); });
  Object.keys(bySlot).sort().forEach(slot => {
    const blocks = bySlot[slot].map(it => renderBlock({
      table: "TB_Item", id: it.Id_Item,
      title: (it.NomeTraduzido && it.NomeTraduzido !== it.Nome)
        ? `${it.Nome}  ·  ${it.NomeTraduzido}` : it.Nome,
      raw: it.TagsJSON,
    }));
    root.append(renderGroup({
      title: slot, meta: `${blocks.length} itens`,
      children: [section("", blocks)],
      startCollapsed: true,
    }));
  });
  return root;
}

const RENDERERS = {
  classes:   renderClasses,
  talentos:  renderTalentos,
  racas:     renderRacas,
  essencias: renderEssencias,
  items:     renderItems,
};

// ---------------------------------------------------------------- modal
let modalCb = null;
const modal      = document.getElementById("addTagModal");
const elPrefix   = document.getElementById("addTagPrefix");
const elValue    = document.getElementById("addTagValue");
const elFilter   = document.getElementById("addTagFilter");
const elProg     = document.getElementById("addTagProgressao");
const elPreview  = document.getElementById("addTagPreview");
const elHint     = document.getElementById("addTagValueHint");
const elOk       = document.getElementById("addTagOk");

function openAddTagModal(cb) {
  modalCb = cb;
  elPrefix.value = "prof";
  elValue.value = "";
  elFilter.value = "";
  elProg.value = "";
  updatePreview();
  modal.classList.remove("hidden");
  setTimeout(() => elValue.focus(), 50);
}

// Parsea "1=3,4=4,10=5,16=6" -> {"1":3,"4":4,"10":5,"16":6}
function parseProgressao(s) {
  const out = {};
  for (const par of String(s).split(",")) {
    const [k, v] = par.split("=").map(x => x && x.trim());
    if (!k || !v) continue;
    if (!/^\d+$/.test(k) || !/^-?\d+$/.test(v)) continue;
    out[k] = parseInt(v, 10);
  }
  return out;
}

function closeModal() { modal.classList.add("hidden"); modalCb = null; }

modal.addEventListener("click", ev => {
  if (ev.target === modal || ev.target.closest("[data-close]")) closeModal();
});

[elPrefix, elValue, elFilter, elProg].forEach(node => node.addEventListener("input", updatePreview));

function updatePreview() {
  const prefix = elPrefix.value;
  const v = elValue.value.trim();
  const flt = elFilter.value.trim();
  const prog = elProg.value.trim();
  if (prefix === "resist" || prefix === "immune" || prefix === "vuln") {
    elHint.textContent = `Elementos canônicos: ${ELEMENTOS.join(", ")}`;
  } else if (prefix === "cond-immune" || prefix === "adv-cond") {
    elHint.textContent = `Condições canônicas: ${CONDICOES.join(", ")}`;
  } else if (prefix === "save-prof") {
    elHint.textContent = `Atributos: ${ATRIBUTOS.join(", ")}`;
  } else if (prefix.startsWith("pick:")) {
    elHint.textContent = "Valor é o número N de slots (ex: 2). Use Progressão se o N variar com o nível da classe.";
  } else {
    elHint.textContent = "";
  }
  if (prefix === "conjurador" || prefix === "infernal") {
    elPreview.textContent = JSON.stringify(prefix);
    return;
  }
  // Com progressão: tag base SEM o ":N" (N vem da progressão), forma SEMPRE objeto
  if (prog) {
    const npn = parseProgressao(prog);
    const obj = { tag: prefix, n_por_nivel: npn };
    if (flt) {
      obj.filter = flt.split("|").map(s => s.trim()).filter(Boolean);
    }
    elPreview.textContent = JSON.stringify(obj);
    return;
  }
  if (!v) { elPreview.textContent = '""'; return; }
  const base = `${prefix}:${v}`;
  if (flt) {
    const arr = flt.split("|").map(s => s.trim()).filter(Boolean);
    elPreview.textContent = JSON.stringify({ tag: base, filter: arr });
  } else {
    elPreview.textContent = JSON.stringify(base);
  }
}

elOk.addEventListener("click", () => {
  const prefix = elPrefix.value;
  const v = elValue.value.trim();
  const flt = elFilter.value.trim();
  const prog = elProg.value.trim();
  let tag;
  if (prefix === "conjurador" || prefix === "infernal") {
    tag = prefix;
  } else if (prog) {
    const npn = parseProgressao(prog);
    if (Object.keys(npn).length === 0) {
      alert("progressão inválida — formato esperado: 1=3,4=4,10=5,16=6");
      return;
    }
    tag = { tag: prefix, n_por_nivel: npn };
    if (flt) {
      tag.filter = flt.split("|").map(s => s.trim()).filter(Boolean);
    }
  } else {
    if (!v) { alert("informe um valor (ou uma progressão)"); return; }
    const base = `${prefix}:${v}`;
    if (flt) {
      const arr = flt.split("|").map(s => s.trim()).filter(Boolean);
      tag = { tag: base, filter: arr };
    } else {
      tag = base;
    }
  }
  modalCb?.(tag);
  closeModal();
});

// ---------------------------------------------------------------- main
async function load() {
  const m = location.pathname.match(/^\/debug\/(\w+)\/?$/);
  const entidade = m ? m[1] : "classes";
  document.querySelectorAll(".topnav nav a").forEach(a => {
    a.classList.toggle("active", a.dataset.nav === entidade);
  });
  const root = document.getElementById("debug-root");
  clearChildren(root);
  root.append(el("div", { class: "loading" }, "Carregando…"));
  try {
    const r = await fetch(`/api/debug/${entidade}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    const renderer = RENDERERS[entidade];
    if (!renderer) throw new Error(`renderer não definido para ${entidade}`);
    clearChildren(root);
    root.append(renderer(data));
  } catch (e) {
    clearChildren(root);
    root.append(el("div", { class: "loading" }, `Erro: ${e.message}`));
  }
}

load();
