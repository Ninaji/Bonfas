/* ==========================================================
   Bonfas — Widget de Ficha de Equipamento
   Uso (em qualquer página):

     <link rel="stylesheet" href="/static/equipment.css">
     <div id="equip"></div>
     <script src="/static/equipment.js"></script>
     <script>
       EquipmentSheet.mount('#equip', {
         characterId: 'char-001',
         silhouette:  '/static/Aventureiro.png',
         apiBase:     '/api',       // opcional — persiste no servidor
         storage:     'local'       // 'local' | 'server' | 'none'
       });
     </script>
   ========================================================== */
(function (global) {
  "use strict";

  // ---------- Definição dos slots (imagem 1) ----------
  // cada slot: { key, titulo, tipos, linhas, coluna: 'L' | 'R' }
  const SLOTS = [
    // anchor = ponto no corpo (x,y) em fração (0..1) da silhueta
    { key: "rosto",   titulo: "Rosto",   col: "L", linhas: 2, anchor: [0.50, 0.12],
      tipos: "Lentes, Máscaras, Óculos, Óculos de proteção." },
    { key: "pescoco", titulo: "Pescoço", col: "L", linhas: 2, anchor: [0.50, 0.19],
      tipos: "Amuletos, Insígnias, Broches, Medalhas, Colares, Pingentes, Periaptos, Cachecóis." },
    { key: "corpo",   titulo: "Corpo",   col: "L", linhas: 2, anchor: [0.40, 0.32],
      tipos: "Armaduras." },
    { key: "bracos",  titulo: "Braços",  col: "L", linhas: 2, anchor: [0.23, 0.38],
      tipos: "Braçadeiras, Pulseiras, Braceletes." },
    { key: "cintura", titulo: "Cintura", col: "L", linhas: 2, anchor: [0.48, 0.50],
      tipos: "Cintos, Cinturões, Faixas." },
    { key: "pes",     titulo: "Pés",     col: "L", linhas: 2, anchor: [0.42, 0.96],
      tipos: "Botas, Sandálias, Sapatos, Chinelos, Pantufas." },

    { key: "cabeca",  titulo: "Cabeça",  col: "R", linhas: 2, anchor: [0.50, 0.04],
      tipos: "Tiaras, Coroas, Chapéus, Faixas de cabeça, Elmos, Capacetes." },
    { key: "costas",  titulo: "Costas",  col: "R", linhas: 2, anchor: [0.75, 0.24],
      tipos: "Asas, Capas, Mantos, Xales." },
    { key: "torso",   titulo: "Torso",   col: "R", linhas: 2, anchor: [0.58, 0.29],
      tipos: "Camisas, Túnicas, Coletes, Roupas." },
    { key: "maos",    titulo: "Mãos",    col: "R", linhas: 2, anchor: [0.78, 0.50],
      tipos: "Manoplas, Luvas." },
    { key: "aneis",   titulo: "Anéis",   col: "R", linhas: 2, anchor: [0.72, 0.55],
      tipos: "Anéis." },
    // Pele — slot para tatuagens; não aponta para o corpo (anchor: null)
    { key: "pele",    titulo: "Pele",    col: "R", linhas: 4, anchor: null,
      tipos: "Tatuagens." },
  ];

  // ---------- Mochila — 5 colunas balanceadas ----------
  // Todas as seções da mochila são DINÂMICAS: começam com 1 linha vazia
  // e crescem automaticamente conforme o usuário preenche.
  const BAG_COLS = [
    [
      { key: "armas",       titulo: "Armas e Escudos",         bag: "armas" },
      { key: "varinhas",    titulo: "Varinhas e Cajados",      bag: "varinhas" },
      { key: "empunhados",  titulo: "Objetos Empunhados",      bag: "empunhados" },
    ],
    [
      { key: "armaduras",   titulo: "Armaduras",               bag: "armaduras" },
      { key: "torso_bag",   titulo: "Torso",                   bag: "torso_bag" },
      { key: "costas_bag",  titulo: "Costas",                  bag: "costas_bag" },
      { key: "cintura_bag", titulo: "Cintura",                 bag: "cintura_bag" },
    ],
    [
      { key: "cabeca_bag",  titulo: "Cabeça",                  bag: "cabeca_bag" },
      { key: "rosto_bag",   titulo: "Rosto",                   bag: "rosto_bag" },
      { key: "pescoco_bag", titulo: "Pescoço",                 bag: "pescoco_bag" },
      { key: "bracos_bag",  titulo: "Braços",                  bag: "bracos_bag" },
    ],
    [
      { key: "maos_bag",    titulo: "Mãos",                    bag: "maos_bag" },
      { key: "pes_bag",     titulo: "Pés",                     bag: "pes_bag" },
      { key: "aneis_bag",   titulo: "Anéis",                   bag: "aneis_bag" },
      { key: "tatuagens",   titulo: "Tatuagens",               bag: "tatuagens" },
    ],
    [
      { key: "flutuando",   titulo: "Flutuando perto de você", bag: "flutuando" },
      { key: "municao",     titulo: "Munição",                 bag: "municao" },
      { key: "edificacao",  titulo: "Edificações",             bag: "edificacao" },
    ],
  ];

  // ---------- Tipos de dano não-físico (D&D 5e) ----------
  const DAMAGE_TYPES = [
    { en: "Acid",      pt: "Ácido" },
    { en: "Cold",      pt: "Frio" },
    { en: "Fire",      pt: "Fogo" },
    { en: "Force",     pt: "Força" },
    { en: "Lightning", pt: "Relâmpago" },
    { en: "Necrotic",  pt: "Necrótico" },
    { en: "Poison",    pt: "Veneno" },
    { en: "Psychic",   pt: "Psíquico" },
    { en: "Radiant",   pt: "Radiante" },
    { en: "Thunder",   pt: "Trovão" },
  ];

  // Items que exigem escolha de tipo de dano (sub-cascata)
  const DMG_TYPE_FRAGMENTS = [
    "Dragon Vessel",
    "Dragon's Wrath Weapon",
    "Dragon-Touched Focus",
    "Scaled Ornament",
  ];
  // Regex de "genéricos de resistência" — pega "<X> of Resistance"
  // mas NÃO pega variantes que já contêm o tipo de dano no nome.
  const RESIST_BASE_RE = /\bof Resistance\b/i;
  const RESIST_TYPED_RE = /\b(Acid|Cold|Fire|Force|Lightning|Necrotic|Poison|Psychic|Radiant|Thunder|Spell|Magic)\s+Resistance\b/i;

  function needsDamageType(item) {
    const n = item && item.Nome ? item.Nome : "";
    if (RESIST_BASE_RE.test(n) && !RESIST_TYPED_RE.test(n)) return true;
    return DMG_TYPE_FRAGMENTS.some(f => n.includes(f));
  }

  // ---------- util ----------
  const h = (tag, cls, txt) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (txt !== undefined) el.textContent = txt;
    return el;
  };

  function makeRowBase(rowClass, val, sint, onChange) {
    const row = h("div", rowClass);
    const inp = h("input");
    inp.type = "text"; inp.value = val || "";
    inp.setAttribute("autocomplete", "off");
    inp.setAttribute("placeholder", " ");    // habilita :placeholder-shown p/ detectar vazio

    if (val) inp.title = val;                 // tooltip mostra nome inteiro ao hover
    const onInput = (ev) => {
      // mantém o tooltip sincronizado com o valor atual
      inp.title = inp.value || "";
      onChange(ev);
    };
    inp.addEventListener("input", onInput);

    const box = h("div", "eq-sint");
    const chk = h("input");
    chk.type = "checkbox"; chk.checked = !!sint;
    chk.addEventListener("change", onChange);
    box.appendChild(chk);

    row.append(inp, box);
    return { row, inp, chk };
  }
  const makeRow    = (v, s, cb) => makeRowBase("eq-row", v, s, cb);
  const makeBagRow = (v, s, cb) => makeRowBase("eq-bag-row", v, s, cb);

  // ---------- Widget ----------
  class EquipmentSheet {
    constructor(host, opts) {
      this.host = host;
      this.opts = Object.assign({
        characterId: "default",
        silhouette:  "/static/Aventureiro.png",
        apiBase:     null,
        storage:     "local",   // local | server | none
      }, opts || {});
      this.state = { slots: {}, bag: {}, meta: { characterId: this.opts.characterId } };
      this._saveTimer = null;
    }

    async init() {
      await this.load();
      this.render();
    }

    storageKey() { return "bonfas.equip." + this.opts.characterId; }

    async load() {
      let loaded = null;
      try {
        if (this.opts.storage === "server" && this.opts.apiBase) {
          const r = await fetch(`${this.opts.apiBase}/equipamento/${encodeURIComponent(this.opts.characterId)}`);
          const js = await r.json();
          if (js && js.data) loaded = js.data;
        } else if (this.opts.storage === "local") {
          const raw = localStorage.getItem(this.storageKey());
          if (raw) loaded = JSON.parse(raw);
        }
      } catch (e) { console.warn("equip load falhou:", e); }
      // mescla com o estado vazio para garantir que todas as chaves
      // (incluindo novas seções adicionadas depois) tenham linhas
      this.state = this._mergeState(loaded);
    }

    _mergeState(loaded) {
      const base = this._emptyState();
      if (!loaded) return base;

      // slots (corpo) — tamanho fixo por sl.linhas: preserva dados,
      // completa/trunca para a contagem atual
      const mergeFixed = (baseArr, got) => {
        if (!Array.isArray(got)) return baseArr;
        const out = [];
        for (let i = 0; i < baseArr.length; i++) {
          out.push(got[i] ? { ...baseArr[i], ...got[i] } : baseArr[i]);
        }
        return out;
      };
      // bag (mochila) — tamanho dinâmico: mantém apenas linhas não-vazias
      // do usuário (remove os vazios padding do modelo antigo de linhas fixas)
      const mergeDynamic = (got) => {
        if (!Array.isArray(got) || !got.length) return [{ item: "", sint: false }];
        const filled = got.filter(r => r && r.item).map(r => ({ item: "", sint: false, ...r }));
        return filled.length ? filled : [{ item: "", sint: false }];
      };

      for (const k in base.slots) base.slots[k] = mergeFixed(base.slots[k], loaded.slots?.[k]);
      for (const k in base.bag)   base.bag[k]   = mergeDynamic(loaded.bag?.[k]);
      // invariante: sempre 1 linha vazia ao final de cada seção da mochila
      for (const k in base.bag)   this._ensureTrailingEmpty(base.bag[k]);

      base.meta = loaded.meta || base.meta;
      return base;
    }

    _emptyState() {
      const s = { slots: {}, bag: {}, meta: { characterId: this.opts.characterId } };
      SLOTS.forEach(sl => {
        s.slots[sl.key] = Array.from({ length: sl.linhas }, () => ({ item: "", sint: false }));
      });
      // Mochila começa com UMA linha vazia por seção
      BAG_COLS.flat().forEach(sec => {
        s.bag[sec.key] = [{ item: "", sint: false }];
      });
      return s;
    }

    // invariante: garante exatamente 1 linha vazia ao final da lista
    _ensureTrailingEmpty(rowsData) {
      if (!rowsData.length || rowsData[rowsData.length - 1].item) {
        rowsData.push({ item: "", sint: false });
      }
    }

    save() {
      clearTimeout(this._saveTimer);
      this._saveTimer = setTimeout(async () => {
        try {
          if (this.opts.storage === "local") {
            localStorage.setItem(this.storageKey(), JSON.stringify(this.state));
          } else if (this.opts.storage === "server" && this.opts.apiBase) {
            await fetch(`${this.opts.apiBase}/equipamento/${encodeURIComponent(this.opts.characterId)}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(this.state),
            });
          }
          this._status(`Salvo ${new Date().toLocaleTimeString()}`);
        } catch (e) { console.warn("equip save falhou:", e); }
      }, 300);
    }

    _status(msg) {
      if (this._statusEl) this._statusEl.textContent = msg;
    }

    // ---------------- render ----------------
    render() {
      const root = h("div", "eq-widget");
      root.appendChild(this._toolbar());
      root.appendChild(this._slotsSection());
      root.appendChild(this._bagSection());
      this.host.innerHTML = "";
      this.host.appendChild(root);
    }

    _toolbar() {
      const bar = h("div", "eq-toolbar");
      const stat = h("span", "muted", `Personagem: ${this.opts.characterId}`);
      this._statusEl = h("span", "muted", "");
      const clr = h("button", null, "Limpar");
      clr.addEventListener("click", () => {
        if (!confirm("Limpar toda a ficha de equipamento?")) return;
        this.state = this._emptyState();
        this.save();
        this.render();
      });
      const exp = h("button", null, "Exportar JSON");
      exp.addEventListener("click", () => {
        const blob = new Blob([JSON.stringify(this.state, null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `equipamento-${this.opts.characterId}.json`;
        a.click();
      });
      bar.append(stat, this._statusEl, exp, clr);
      return bar;
    }

    // --- imagem 1: silhueta com slots ---
    _slotsSection() {
      const wrap = h("div");
      wrap.appendChild(this._title("ESPAÇOS DE EQUIPAMENTO"));

      const grid = h("div", "eq-slots");
      this._grid = grid;
      const colL = h("div", "eq-col");
      this._colL = colL;
      const sil  = h("div", "eq-silhouette");
      this._silhouetteEl = sil;
      const img  = h("img");
      img.src = this.opts.silhouette; img.alt = "";
      this._silhouetteImg = img;
      img.addEventListener("load", () => this._drawConnectors());
      sil.appendChild(img);
      const colR = h("div", "eq-col");

      this._slotEls = new Map();
      SLOTS.forEach(sl => {
        const box = this._slotBox(sl);
        this._slotEls.set(sl.key, box);
        (sl.col === "L" ? colL : colR).appendChild(box);
      });

      // SVG overlay para linhas conectoras
      const svgNS = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(svgNS, "svg");
      svg.setAttribute("class", "eq-connectors");
      this._svg = svg;

      grid.append(colL, sil, colR, svg);
      wrap.appendChild(grid);

      // reagir a mudanças de tamanho
      if (this._ro) this._ro.disconnect();
      this._ro = new ResizeObserver(() => this._layout());
      this._ro.observe(grid);
      this._ro.observe(colL);
      requestAnimationFrame(() => this._layout());
      return wrap;
    }

    _layout() {
      this._resizeSilhouette();
      this._drawConnectors();
    }

    _resizeSilhouette() {
      if (!this._silhouetteImg || !this._colL) return;
      const img = this._silhouetteImg;
      if (!img.naturalWidth || !img.naturalHeight) return;
      const leftH = this._colL.getBoundingClientRect().height;
      // 100px acima da cabeça + 100px abaixo dos pés
      const target = Math.max(300, leftH - 200);
      img.style.height = target + "px";
      img.style.width = (target * img.naturalWidth / img.naturalHeight) + "px";
    }

    _drawConnectors() {
      if (!this._svg || !this._grid || !this._silhouetteImg) return;
      const g = this._grid.getBoundingClientRect();
      const silBox = this._silhouetteImg.getBoundingClientRect();
      if (silBox.width === 0 || silBox.height === 0) return;

      const svg = this._svg;
      svg.setAttribute("viewBox", `0 0 ${g.width} ${g.height}`);
      svg.setAttribute("width", g.width);
      svg.setAttribute("height", g.height);
      while (svg.firstChild) svg.removeChild(svg.firstChild);

      const svgNS = "http://www.w3.org/2000/svg";
      const mk = (tag, attrs) => {
        const el = document.createElementNS(svgNS, tag);
        for (const k in attrs) el.setAttribute(k, attrs[k]);
        return el;
      };

      // lista por coluna — cada slot recebe um offset único para que
      // duas lanes verticais nunca se sobreponham
      const leftSlots  = SLOTS.filter(s => s.col === "L");
      const rightSlots = SLOTS.filter(s => s.col === "R");
      const SPACING = 10;

      SLOTS.forEach(sl => {
        if (!sl.anchor) return;              // slot sem linha conectora
        const box = this._slotEls.get(sl.key);
        if (!box) return;
        const b = box.getBoundingClientRect();

        const isL  = sl.col === "L";
        const colArr = isL ? leftSlots : rightSlots;
        const idx  = colArr.indexOf(sl);
        const n    = colArr.length;
        // offset simétrico em torno do ponto médio (ex.: n=6 → [-25,-15,-5,5,15,25])
        const offset = (idx - (n - 1) / 2) * SPACING;

        const exitX = (isL ? b.right : b.left) - g.left;
        const exitY = b.top + 12 - g.top;

        const tx = silBox.left + sl.anchor[0] * silBox.width  - g.left;
        const ty = silBox.top  + sl.anchor[1] * silBox.height - g.top;

        // bend aproximadamente no meio do caminho, mas com offset único por slot
        const midX = (exitX + tx) / 2 + offset;

        const d = `M ${exitX} ${exitY} L ${midX} ${exitY} L ${midX} ${ty} L ${tx} ${ty}`;
        svg.appendChild(mk("path", { d }));
        svg.appendChild(mk("circle", { cx: tx, cy: ty, r: 3 }));
        svg.appendChild(mk("circle", { cx: exitX, cy: exitY, r: 2 }));
      });
    }

    _slotBox(sl) {
      const box = h("div", "eq-slot");

      const head = h("div", "eq-slot-head");
      head.append(h("div", null, "Item"), h("div", null, "Sint."));
      box.appendChild(head);

      const rowsData = this.state.slots[sl.key] || [];
      rowsData.forEach((data) => {
        const onChange = (ev) => {
          const t = ev.target;
          if (t.type === "checkbox") data.sint = t.checked;
          else { data.item = t.value; delete data.itemId; delete data.slotFicha; }
          this.save();
        };
        const { row, inp } = makeRow(data.item, data.sint, onChange);
        this._attachAutocomplete(inp, { slot: sl.key }, data);
        box.appendChild(row);
      });

      box.appendChild(h("div", "eq-slot-label", sl.titulo));
      box.appendChild(h("div", "eq-slot-hint", sl.tipos));
      return box;
    }

    // --- imagem 2: mochila de equipamentos ---
    _bagSection() {
      const wrap = h("div", "eq-bag-wrap");
      wrap.appendChild(this._title("MOCHILA DE EQUIPAMENTOS"));

      const grid = h("div", "eq-bag");
      BAG_COLS.forEach(col => {
        const c = h("div", "eq-bag-col");
        col.forEach(sec => c.appendChild(this._bagSection1(sec)));
        grid.appendChild(c);
      });
      wrap.appendChild(grid);
      return wrap;
    }

    _bagSection1(sec) {
      const s = h("div", "eq-bag-section");
      const head = h("div", "eq-bag-head");
      head.append(h("div", null, sec.titulo), h("div", null, "Sint."));
      s.appendChild(head);

      const rowsData = this.state.bag[sec.key] || (this.state.bag[sec.key] = []);
      this._ensureTrailingEmpty(rowsData);

      // Fecha-se sobre rowsData + s para poder adicionar novas linhas do DOM
      // sem reconstruir a seção inteira (preserva foco do usuário).
      const grow = () => {
        if (rowsData.length && rowsData[rowsData.length - 1].item) {
          const next = { item: "", sint: false };
          rowsData.push(next);
          addDomRow(next);
        }
      };

      const addDomRow = (data) => {
        const onChange = (ev) => {
          const t = ev.target;
          if (t.type === "checkbox") {
            data.sint = t.checked;
          } else {
            data.item = t.value;
            if (!t.value) { delete data.itemId; delete data.slotFicha; delete data.damageType; }
          }
          grow();
          this.save();
        };
        const { row, inp } = makeBagRow(data.item, data.sint, onChange);
        this._attachAutocomplete(inp, { bag: sec.bag }, data, grow);
        s.appendChild(row);
      };

      rowsData.forEach(addDomRow);
      return s;
    }

    // --------------- Autocomplete / cascata de itens ---------------
    _attachAutocomplete(inp, filter, rowData, onAfterPick) {
      if (!this.opts.apiBase) return;        // só funciona com API
      const open = () => this._openAC(inp, filter, rowData, onAfterPick);
      inp.addEventListener("focus", () => {
        try { inp.setSelectionRange(0, 0); inp.scrollLeft = 0; } catch (_) {}
        inp.classList.add("eq-focused");
        open();
      });
      inp.addEventListener("input", open);
      inp.addEventListener("click", open);
      inp.addEventListener("blur", () => {
        inp.classList.remove("eq-focused");
        setTimeout(() => this._closeAC(inp), 180);
      });
      inp.addEventListener("keydown", (e) => this._acKey(e));
    }

    _ensureACEl() {
      if (this._acEl) return this._acEl;
      const el = h("div", "eq-ac");
      document.body.appendChild(el);
      this._acEl = el;
      return el;
    }

    _closeAC(inp) {
      if (!this._acEl) return;
      if (inp && this._acActive && this._acActive.inp !== inp) return;
      this._acEl.style.display = "none";
      this._acActive = null;
    }

    async _openAC(inp, filter, rowData, onAfterPick) {
      const ac = this._ensureACEl();
      this._acActive = { inp, filter, rowData, onAfterPick };
      const r = inp.getBoundingClientRect();
      ac.style.left = (r.left + window.scrollX) + "px";
      ac.style.top  = (r.bottom + window.scrollY + 2) + "px";
      ac.style.minWidth = Math.max(280, r.width) + "px";
      ac.style.display = "block";
      ac.innerHTML = '<div class="eq-ac-loading">carregando…</div>';

      const params = new URLSearchParams();
      params.set("q", inp.value || "");
      if (filter.slot) params.set("slot", filter.slot);
      if (filter.bag)  params.set("bag", filter.bag);
      params.set("limit", "40");

      try {
        const res = await fetch(`${this.opts.apiBase}/items?${params}`);
        const items = await res.json();
        if (!this._acActive || this._acActive.inp !== inp) return;
        this._renderAC(items, filter, inp, rowData);
      } catch (e) {
        ac.innerHTML = '<div class="eq-ac-empty">erro ao buscar</div>';
      }
    }

    _renderAC(results, filter, inp, rowData) {
      const ac = this._acEl;
      ac.innerHTML = "";

      // Seção 1 — "No inventário" (só para slots do corpo)
      if (filter.slot) {
        const owned = this._inventoryItemsForSlot(filter.slot);
        if (owned.length) {
          const sec = h("div", "eq-ac-section");
          sec.appendChild(h("div", "eq-ac-head", "No seu inventário"));
          owned.forEach(it => sec.appendChild(this._acRow(it, inp, rowData, true)));
          ac.appendChild(sec);
        }
      }

      // Seção 2 — Catálogo
      const sec2 = h("div", "eq-ac-section");
      sec2.appendChild(h("div", "eq-ac-head", filter.slot ? "Catálogo" : "Itens disponíveis"));
      if (!results.length) {
        sec2.appendChild(h("div", "eq-ac-empty", "Nenhum item encontrado"));
      } else {
        results.forEach(it => sec2.appendChild(this._acRow(it, inp, rowData, false)));
      }
      ac.appendChild(sec2);
    }

    _acRow(item, inp, rowData, owned) {
      const row = h("div", "eq-ac-row");
      const hasPt = !!(item.NomeTraduzido && item.NomeTraduzido.trim()
                       && item.NomeTraduzido !== item.Nome);
      const title = hasPt ? item.NomeTraduzido : item.Nome;

      // linha 1: nome principal (PT se existir, senão o original)
      const nameDiv = h("div", "eq-ac-name");
      nameDiv.textContent = title;
      if (owned) {
        const badge = h("span", "eq-ac-owned", "possuo");
        nameDiv.appendChild(document.createTextNode(" "));
        nameDiv.appendChild(badge);
      }
      row.appendChild(nameDiv);

      // linha 2: nome original em inglês — só quando há tradução diferente
      if (hasPt) row.appendChild(h("div", "eq-ac-orig", item.Nome));

      // linha 3: slot / dano
      const meta = (item.SlotNome || "") + (item.Damage ? " • " + item.Damage : "");
      if (meta.trim()) row.appendChild(h("div", "eq-ac-sub", meta));

      row.addEventListener("mousedown", (e) => {
        e.preventDefault();
        const onAfterPick = this._acActive && this._acActive.onAfterPick;
        if (needsDamageType(item)) {
          this._showDamageCascade(item, inp, rowData, onAfterPick);
          return;
        }
        rowData.item      = title;
        rowData.itemId    = item.Id_Item;
        rowData.slotFicha = item.SlotFicha;
        rowData.slotNome  = item.SlotNome;
        delete rowData.damageType;
        inp.value = title;
        inp.title = title;
        this.save();
        this._closeAC();
        if (onAfterPick) onAfterPick();
      });
      return row;
    }

    _showDamageCascade(item, inp, rowData, onAfterPick) {
      const ac = this._ensureACEl();
      ac.innerHTML = "";
      const hasPt = !!(item.NomeTraduzido && item.NomeTraduzido !== item.Nome);
      const baseTitle = hasPt ? item.NomeTraduzido : item.Nome;

      // breadcrumb / voltar
      const back = h("div", "eq-ac-back");
      back.textContent = "‹ " + baseTitle;
      back.addEventListener("mousedown", (e) => {
        e.preventDefault();
        if (this._acActive) this._openAC(this._acActive.inp, this._acActive.filter, this._acActive.rowData, this._acActive.onAfterPick);
      });
      ac.appendChild(back);

      ac.appendChild(h("div", "eq-ac-head", "Escolha o tipo de dano"));

      DAMAGE_TYPES.forEach(d => {
        const row = h("div", "eq-ac-row");
        row.appendChild(h("div", "eq-ac-name", d.pt));
        row.appendChild(h("div", "eq-ac-orig", d.en));
        row.addEventListener("mousedown", (e) => {
          e.preventDefault();
          const finalTitle = `${baseTitle} (${d.pt})`;
          rowData.item       = finalTitle;
          rowData.itemId     = item.Id_Item;
          rowData.slotFicha  = item.SlotFicha;
          rowData.slotNome   = item.SlotNome;
          rowData.damageType = d.en;
          inp.value = finalTitle;
          inp.title = finalTitle;
          this.save();
          this._closeAC();
          if (onAfterPick) onAfterPick();
        });
        ac.appendChild(row);
      });
    }

    _inventoryItemsForSlot(slotFicha) {
      const out = [];
      for (const key in this.state.bag) {
        (this.state.bag[key] || []).forEach(r => {
          if (r.itemId && r.slotFicha === slotFicha) {
            out.push({
              Id_Item: r.itemId,
              Nome: r.item,
              NomeTraduzido: r.item,
              SlotFicha: r.slotFicha,
              SlotNome: r.slotNome || "",
            });
          }
        });
      }
      return out;
    }

    _acKey(e) {
      if (!this._acEl || this._acEl.style.display === "none") return;
      const rows = [...this._acEl.querySelectorAll(".eq-ac-row")];
      if (!rows.length) return;
      let idx = rows.findIndex(r => r.classList.contains("active"));
      if (e.key === "ArrowDown")      { e.preventDefault(); idx = (idx + 1) % rows.length; }
      else if (e.key === "ArrowUp")   { e.preventDefault(); idx = (idx - 1 + rows.length) % rows.length; }
      else if (e.key === "Enter" && idx >= 0) { e.preventDefault(); rows[idx].dispatchEvent(new MouseEvent("mousedown")); return; }
      else if (e.key === "Escape")    { this._closeAC(); return; }
      else return;
      rows.forEach(r => r.classList.remove("active"));
      if (rows[idx]) { rows[idx].classList.add("active"); rows[idx].scrollIntoView({ block: "nearest" }); }
    }

    _title(txt) { return h("div", "eq-title", txt); }
  }

  // API pública
  const api = {
    mount(selector, opts) {
      const host = typeof selector === "string" ? document.querySelector(selector) : selector;
      if (!host) throw new Error("EquipmentSheet.mount: host não encontrado");
      const w = new EquipmentSheet(host, opts);
      w.init();
      return w;
    },
    SLOTS, BAG_COLS,
  };

  global.EquipmentSheet = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : this);
