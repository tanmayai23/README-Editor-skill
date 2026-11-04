(function () {
  "use strict";

  var REPO = "tanmayai23/README-Editor-skill";
  var REPO_URL = "https://github.com/" + REPO;
  var BLOB = REPO_URL + "/blob/main/";
  var ADD_URL = BLOB + "gallery/README.md";
  // The deploy workflow copies gallery.json next to this page; the raw file is the fallback.
  var DATA_URLS = ["gallery.json", "https://raw.githubusercontent.com/" + REPO + "/main/gallery/gallery.json"];

  var state = { data: null, category: "all", query: "", preview: null, previewChosen: false };
  var $ = function (id) { return document.getElementById(id); };
  var grid = $("grid");

  // ---------- small helpers ----------
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") n.className = attrs[k];
        else if (k === "text") n.textContent = attrs[k];
        else n.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }

  function safeLink(link) {
    if (typeof link !== "string") return REPO_URL;
    if (/^https:\/\//i.test(link)) return link;
    if (/^[\w.\/#-]+$/.test(link) && link.indexOf("..") === -1) return BLOB + link;
    return REPO_URL;
  }

  function assetUrl(path) {
    if (typeof path !== "string" || !/^[\w.\/-]+$/.test(path) || path.indexOf("..") !== -1) return null;
    return state.data.assetBase + path;
  }

  function announce(text) {
    var live = $("live");
    live.textContent = "";
    setTimeout(function () { live.textContent = text; }, 30);
  }

  function copyText(text, button) {
    function done() {
      var label = button.getAttribute("data-label") || button.textContent;
      button.setAttribute("data-label", label);
      button.classList.add("done");
      if (!button.querySelector("svg")) button.textContent = "Copied";
      announce("Copied to clipboard");
      setTimeout(function () {
        button.classList.remove("done");
        if (!button.querySelector("svg")) button.textContent = label;
      }, 1600);
    }
    function fallback() {
      var ta = el("textarea", { "aria-hidden": "true" });
      ta.value = text;
      ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { announce("Copy failed. Select the text and copy it by hand."); }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  // ---------- theme ----------
  function pageTheme() {
    var t = document.documentElement.dataset.theme;
    if (t === "dark" || t === "light") return t;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function syncThemeButton() {
    var next = pageTheme() === "dark" ? "light" : "dark";
    $("theme-toggle").setAttribute("aria-label", "Switch to " + next + " theme");
  }

  $("theme-toggle").addEventListener("click", function () {
    var next = pageTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("rf-theme", next); } catch (e) {}
    syncThemeButton();
    if (!state.previewChosen) setPreview(next, false);
  });

  // ---------- preview theme ----------
  function setPreview(theme, chosen) {
    state.preview = theme;
    if (chosen) state.previewChosen = true;
    document.querySelectorAll(".seg button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-preview") === theme));
    });
    if (state.data) render();
  }

  document.querySelectorAll(".seg button").forEach(function (b) {
    b.addEventListener("click", function () { setPreview(b.getAttribute("data-preview"), true); });
  });

  // ---------- data ----------
  function load(i) {
    i = i || 0;
    grid.setAttribute("aria-busy", "true");
    renderSkeleton();
    return fetch(DATA_URLS[i], { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        if (!d || !Array.isArray(d.items) || !Array.isArray(d.categories)) throw new Error("bad data");
        state.data = d;
        grid.setAttribute("aria-busy", "false");
        renderPills();
        readHash(false);
        render();
      })
      .catch(function () {
        if (i + 1 < DATA_URLS.length) return load(i + 1);
        renderError();
      });
  }

  function categoryName(id) {
    var c = state.data.categories.filter(function (x) { return x.id === id; })[0];
    return c ? c.name : id;
  }

  // ---------- pills + hash ----------
  function renderPills() {
    var pills = $("pills");
    pills.textContent = "";
    var counts = {};
    state.data.items.forEach(function (it) { counts[it.category] = (counts[it.category] || 0) + 1; });
    var all = [{ id: "all", name: "All", emoji: "" , count: state.data.items.length }].concat(
      state.data.categories.map(function (c) { return { id: c.id, name: c.name, emoji: c.emoji, count: counts[c.id] || 0 }; }));
    all.forEach(function (c) {
      var b = el("button", { class: "pill", type: "button", "data-cat": c.id, "aria-pressed": String(state.category === c.id) }, [
        c.emoji ? el("span", { "aria-hidden": "true", text: c.emoji }) : null,
        el("span", { text: c.name }),
        el("span", { class: "count", text: String(c.count) })
      ]);
      b.addEventListener("click", function () { selectCategory(c.id, true); });
      pills.appendChild(b);
    });
  }

  function selectCategory(id, updateHash) {
    state.category = id;
    document.querySelectorAll(".pill").forEach(function (p) {
      p.setAttribute("aria-pressed", String(p.getAttribute("data-cat") === id));
    });
    if (updateHash) {
      var url = location.pathname + location.search + (id === "all" ? "#gallery" : "#" + id);
      history.replaceState(null, "", url);
    }
    render();
  }

  function readHash(scroll) {
    if (!state.data) return;
    var h = decodeURIComponent(location.hash.slice(1));
    var known = state.data.categories.some(function (c) { return c.id === h; });
    if (known) {
      selectCategory(h, false);
      if (scroll) $("gallery").scrollIntoView();
    }
  }
  window.addEventListener("hashchange", function () { readHash(true); });

  // ---------- search ----------
  $("search").addEventListener("input", function (e) {
    state.query = e.target.value.trim().toLowerCase();
    render();
  });

  // ---------- rendering ----------
  function renderSkeleton() {
    grid.textContent = "";
    for (var i = 0; i < 6; i++) {
      grid.appendChild(el("div", { class: "card skeleton", "aria-hidden": "true" }, [
        el("div", { class: "thumb" }),
        el("div", { class: "card-body" }, [el("div", { class: "bar" }), el("div", { class: "bar short" })])
      ]));
    }
  }

  function renderError() {
    grid.setAttribute("aria-busy", "false");
    grid.textContent = "";
    var retry = el("button", { class: "btn primary", type: "button", text: "Retry" });
    retry.addEventListener("click", function () { load(0); });
    grid.appendChild(el("div", { class: "empty" }, [
      el("h3", { text: "Couldn't load the gallery" }),
      el("p", { text: "Check your connection and try again, or browse the files on GitHub." }),
      el("div", { class: "hero-ctas" }, [retry, el("a", { class: "btn", href: REPO_URL, text: "Open the repo" })])
    ]));
    $("result-count").textContent = "";
  }

  function matches(it) {
    if (state.category !== "all" && it.category !== state.category) return false;
    if (!state.query) return true;
    return (String(it.title) + " " + String(it.description)).toLowerCase().indexOf(state.query) !== -1;
  }

  function render() {
    var items = state.data.items.filter(matches);
    grid.textContent = "";

    if (state.category === "community" && !state.query && items.length === 0) {
      grid.appendChild(el("div", { class: "empty" }, [
        el("h3", { text: "Be the first." }),
        el("p", { text: "Made a README with readme-forge? Add it to the gallery." }),
        el("div", { class: "hero-ctas" }, [el("a", { class: "btn primary", href: ADD_URL, text: "Add your README" })])
      ]));
      $("result-count").textContent = "No community READMEs yet.";
      return;
    }

    if (items.length === 0) {
      var clear = el("button", { class: "btn", type: "button", text: "Clear search" });
      clear.addEventListener("click", function () { $("search").value = ""; state.query = ""; render(); $("search").focus(); });
      grid.appendChild(el("div", { class: "empty" }, [
        el("h3", { text: "No results" }),
        el("p", { text: "Nothing matches “" + state.query + "”" + (state.category !== "all" ? " in " + categoryName(state.category) : "") + "." }),
        el("div", { class: "hero-ctas" }, [clear])
      ]));
      $("result-count").textContent = "0 results";
      return;
    }

    $("result-count").textContent = items.length + (items.length === 1 ? " item" : " items");
    items.forEach(function (it) { grid.appendChild(it.image ? imageCard(it) : textCard(it)); });
  }

  function copyButton(text, label) {
    var b = el("button", { class: "copy-icon", type: "button", title: "Copy command", "aria-label": "Copy command for " + label }, [
      svgCopy(), el("span", { text: "Copy" })
    ]);
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      copyText(text, b);
      var span = b.querySelector("span");
      span.textContent = "Copied";
      setTimeout(function () { span.textContent = "Copy"; }, 1600);
    });
    return b;
  }

  function svgCopy() {
    var ns = "http://www.w3.org/2000/svg";
    var s = document.createElementNS(ns, "svg");
    s.setAttribute("viewBox", "0 0 16 16"); s.setAttribute("width", "14"); s.setAttribute("height", "14"); s.setAttribute("aria-hidden", "true");
    var p = document.createElementNS(ns, "path");
    p.setAttribute("fill", "currentColor");
    p.setAttribute("d", "M0 6.75C0 5.78.78 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .14.11.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25ZM5 1.75C5 .78 5.78 0 6.75 0h7.5C15.22 0 16 .78 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .14.11.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z");
    s.appendChild(p);
    return s;
  }

  function thumb(it, theme) {
    var src = assetUrl(it.image && it.image[theme]);
    var box = el("div", { class: "thumb " + theme });
    if (src) {
      box.appendChild(el("img", {
        src: src, loading: "lazy", decoding: "async",
        alt: it.title + " " + (it.category === "banners" ? "banner" : "preview") + ", " + theme + " variant: " + it.description
      }));
    }
    if (it.animated) box.appendChild(el("span", { class: "badge", text: /\.gif$/i.test(src || "") ? "GIF" : "Animated" }));
    return box;
  }

  function imageCard(it) {
    var open = el("button", { class: "card-open", type: "button", "aria-label": "Open " + it.title }, [
      thumb(it, state.preview),
      el("div", { class: "card-body" }, [
        el("div", { class: "card-title", text: it.title }),
        el("div", { class: "card-desc", text: it.description })
      ])
    ]);
    open.addEventListener("click", function () { openDetail(it); });
    var foot = el("div", { class: "card-foot" }, [
      it.source === "community" && it.author
        ? el("span", { class: "cat-tag", text: "by " + it.author.name })
        : el("span", { class: "cat-tag", text: categoryName(it.category) }),
      it.command ? copyButton(it.command, it.title) : null
    ]);
    return el("article", { class: "card" }, [open, foot]);
  }

  function textCard(it) {
    var open = el("button", { class: "card-open", type: "button", "aria-label": "Open " + it.title }, [
      el("div", { class: "card-body" }, [
        el("span", { class: "text-mark", "aria-hidden": "true", text: "👤" }),
        el("div", { class: "card-title", text: it.title }),
        el("div", { class: "card-desc", text: it.description })
      ])
    ]);
    open.addEventListener("click", function () { openDetail(it); });
    var body = el("div", { class: "card-body", style: "padding-top:0" }, [
      it.command ? el("code", { class: "mini-cmd", text: it.command }) : null
    ]);
    var foot = el("div", { class: "card-foot" }, [
      el("a", { class: "card-link", href: safeLink(it.link), text: "View template" }),
      it.command ? copyButton(it.command, it.title) : null
    ]);
    return el("article", { class: "card text" }, [open, body, foot]);
  }

  // ---------- detail dialog ----------
  var dialog = $("detail");
  function openDetail(it) {
    $("detail-title").textContent = it.title;
    var body = $("detail-body");
    body.textContent = "";
    if (it.image) {
      body.appendChild(el("div", { class: "variants" }, ["dark", "light"].map(function (t) {
        return el("div", { class: "variant" }, [thumb(it, t), el("span", { text: t === "dark" ? "Dark theme" : "Light theme" })]);
      })));
    }
    body.appendChild(el("p", { class: "detail-desc", text: it.description }));
    if (it.source === "community" && it.author && /^[A-Za-z0-9-]{1,39}$/.test(it.author.github || "")) {
      body.appendChild(el("a", { class: "author", href: "https://github.com/" + it.author.github }, [
        el("img", { src: "https://github.com/" + it.author.github + ".png?size=64", alt: "" }),
        el("span", { text: "by " + it.author.name })
      ]));
    }
    if (it.command) {
      var cmdId = "detail-cmd";
      var copy = el("button", { class: "copy", type: "button", text: "Copy" });
      copy.addEventListener("click", function () { copyText(it.command, copy); });
      body.appendChild(el("div", { class: "install" }, [el("code", { id: cmdId, text: it.command }), copy]));
    }
    body.appendChild(el("div", { class: "detail-links" }, [
      el("a", { class: "btn", href: safeLink(it.link), text: "Open on GitHub" })
    ]));
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }
  $("detail-close").addEventListener("click", function () { dialog.close(); });
  dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });

  // ---------- static copy buttons ----------
  document.querySelectorAll("[data-copy-from]").forEach(function (b) {
    b.addEventListener("click", function () { copyText($(b.getAttribute("data-copy-from")).textContent, b); });
  });

  // ---------- stars ----------
  fetch("https://api.github.com/repos/" + REPO)
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (d) {
      if (typeof d.stargazers_count !== "number") return;
      var n = d.stargazers_count;
      var text = n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\.0$/, "") + "k" : String(n);
      var c = $("star-count");
      c.textContent = text;
      c.hidden = false;
      c.parentElement.setAttribute("aria-label", "Star readme-forge on GitHub, " + n + " stars");
    })
    .catch(function () {});

  // ---------- floating button hides over the footer ----------
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      $("float-add").classList.toggle("hide", entries[0].isIntersecting);
    }).observe($("footer"));
  }

  // ---------- start ----------
  syncThemeButton();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    syncThemeButton();
    if (!state.previewChosen) setPreview(pageTheme(), false);
  });
  setPreview(pageTheme(), false);
  load(0);
})();
