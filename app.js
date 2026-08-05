    // Reliably jump to a same-page anchor. `scroll-behavior: smooth` on <html>
    // doesn't always complete the browser's native hash-scroll — on initial page
    // load in particular, it can silently no-op. Anything that needs to land on
    // a section (sidebar links, search results) goes through this instead.
    function rbaJumpToHash(hash) {
      const id = hash.replace(/^#/, '');
      if (!id) return;
      const el = document.getElementById(id);
      if (!el) return;
      // The `behavior` option alone doesn't reliably beat the CSS scroll-behavior
      // rule in every engine, so force it via inline style for this one jump.
      const root = document.documentElement;
      const prevBehavior = root.style.scrollBehavior;
      root.style.scrollBehavior = 'auto';
      el.scrollIntoView({ block: 'start' });
      root.style.scrollBehavior = prevBehavior;
    }
    if (location.hash) {
      const hashToJump = location.hash;
      // Let any (possibly broken) native browser attempt at the hash-scroll
      // happen and finish first, so ours is the one that actually sticks.
      window.addEventListener('load', () => {
        setTimeout(() => {
          rbaJumpToHash(hashToJump);
          const link = document.querySelector('.sidebar-link[href="' + hashToJump + '"]');
          if (link) {
            document.querySelectorAll('.sidebar-link--active').forEach((l) => l.classList.remove('sidebar-link--active'));
            link.classList.add('sidebar-link--active');
            if (window.rbaExpandActiveNavGroup) window.rbaExpandActiveNavGroup();
          }
        }, 150);
      });
    }

    // Scroll the sidebar so the active group (or scroll-spy'd link) sits just below
    // the top of the nav's own scroll area. The component groups are separate pages
    // and the sidebar is its own scroll container, so a normal navigation would reset
    // it to the top and drop the user far from the group they just opened. Returns the
    // active element (so the drawer can focus it) or null. No-op when the sidebar isn't
    // its own scroller (stacked no-JS mobile).
    function rbaRevealActiveNav() {
      const sidebar = document.querySelector('.sidebar');
      if (!sidebar) return null;
      if (window.rbaExpandActiveNavGroup) window.rbaExpandActiveNavGroup();
      const active = sidebar.querySelector('.sidebar-group--active') ||
                     sidebar.querySelector('.sidebar-link--active');
      if (!active) return null;
      if (sidebar.scrollHeight - sidebar.clientHeight > 4) {
        const delta = active.getBoundingClientRect().top - sidebar.getBoundingClientRect().top;
        sidebar.scrollTop = Math.max(0, sidebar.scrollTop + delta - 16);
      }
      return active;
    }

    // Sidebar scroll-spy · highlight the section closest to (and above) the viewport top
    (function () {
      const links = Array.from(document.querySelectorAll('.sidebar-link[href^="#"]'));
      if (!links.length) return;
      const linkBy = Object.fromEntries(links.map(l => [l.getAttribute('href').substring(1), l]));
      const sections = links
        .map(l => document.getElementById(l.getAttribute('href').substring(1)))
        .filter(Boolean);
      if (!sections.length) return;

      // Sort by document position so iteration matches scroll order
      sections.sort((a, b) =>
        (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1
      );

      let currentId = null;
      function setActive(id) {
        if (id === currentId) return;
        currentId = id;
        links.forEach(l => l.classList.remove('sidebar-link--active'));
        if (linkBy[id]) linkBy[id].classList.add('sidebar-link--active');
      }

      function update() {
        // If we can't scroll further (or are within ~120 px of the bottom),
        // force the last section active so the tail of the page isn't stuck.
        const nearBottom = (window.scrollY + window.innerHeight) >= (document.documentElement.scrollHeight - 120);
        if (nearBottom) {
          setActive(sections[sections.length - 1].id);
          return;
        }
        // "Active" = last section whose top has scrolled above the upper third of the viewport.
        const threshold = Math.max(120, window.innerHeight * 0.3);
        let bestId = sections[0].id;
        for (const s of sections) {
          if (s.getBoundingClientRect().top - threshold <= 0) {
            bestId = s.id;
          } else {
            break;
          }
        }
        setActive(bestId);
      }

      let scheduled = false;
      function onScroll() {
        if (scheduled) return;
        scheduled = true;
        requestAnimationFrame(() => {
          scheduled = false;
          update();
        });
      }
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', onScroll, { passive: true });

      // Snap immediately on click, and drive the scroll ourselves — see
      // rbaJumpToHash above for why the native hash-scroll can't be trusted.
      links.forEach(l => {
        l.addEventListener('click', (e) => {
          const id = l.getAttribute('href').substring(1);
          setActive(id);
          e.preventDefault();
          rbaJumpToHash('#' + id);
          history.pushState(null, '', '#' + id);
        });
      });

      update();
    })();

    // Sidebar groups · expand/collapse, one open/closed state per group, remembered
    // across page loads. A group starts expanded if it contains the current page's
    // active link/section (so navigating in never lands on a collapsed target) or if
    // the user previously left it open — collapsed otherwise. Scroll-spy's continuous
    // updates deliberately do NOT re-trigger this (see setActive above) — only page
    // load and explicit navigation force a group open, so scrolling never fights a
    // group the user just closed by hand.
    (function () {
      const STORAGE_PREFIX = 'rba-nav-open:';
      const groups = document.querySelectorAll('.sidebar-section[data-nav-group]');

      function setCollapsed(section, header, collapsed, persist) {
        section.setAttribute('data-collapsed', collapsed ? 'true' : 'false');
        header.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
        if (persist) {
          try { localStorage.setItem(STORAGE_PREFIX + section.getAttribute('data-nav-group'), collapsed ? '0' : '1'); } catch (e) {}
        }
      }

      groups.forEach(section => {
        const key = section.getAttribute('data-nav-group');
        const header = section.querySelector('.sidebar-section-header');
        const body = section.querySelector('.sidebar-section-body');
        if (!header || !body) return;

        let stored = null;
        try { stored = localStorage.getItem(STORAGE_PREFIX + key); } catch (e) {}
        const hasActive = !!section.querySelector('.sidebar-link--active, .sidebar-group--active');
        const startCollapsed = stored !== null ? stored === '0' : !hasActive;
        setCollapsed(section, header, startCollapsed, false);

        header.addEventListener('click', () => {
          setCollapsed(section, header, section.getAttribute('data-collapsed') !== 'true', true);
        });
      });

      // Exposed so rbaRevealActiveNav (and the hash-jump above) can force a group
      // open without touching localStorage — correcting DISPLAY for the page you're
      // actually on, not overriding what the user chose to leave closed elsewhere.
      window.rbaExpandActiveNavGroup = function () {
        const active = document.querySelector('.sidebar-link--active, .sidebar-group--active');
        if (!active) return;
        const section = active.closest('.sidebar-section[data-nav-group]');
        if (!section || section.getAttribute('data-collapsed') !== 'true') return;
        const header = section.querySelector('.sidebar-section-header');
        section.setAttribute('data-collapsed', 'false');
        if (header) header.setAttribute('aria-expanded', 'true');
      };
    })();

    // Theme toggle · light / dark, persisted across pages
    (function () {
      const KEY = 'rba-theme';
      const root = document.documentElement;
      const toggle = document.getElementById('theme-toggle');
      function apply(theme) {
        if (theme === 'dark') root.setAttribute('data-theme', 'dark');
        else root.removeAttribute('data-theme');
        if (toggle) {
          toggle.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
          // Both options are drawn in the track and the active one is styled off
          // [data-theme] in CSS, so nothing here swaps glyphs — the only job left
          // is keeping the switch's accessible name in step with what's shown.
          toggle.setAttribute('aria-label', theme === 'dark' ? 'Dark mode' : 'Light mode');
        }
        document.querySelectorAll('.theme-label').forEach(el => {
          el.textContent = theme === 'dark' ? 'Dark theme' : 'Light theme';
        });
      }
      let saved = null;
      try { saved = localStorage.getItem(KEY); } catch (e) {}
      let systemPrefersDark = false;
      try { systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches; } catch (e) {}
      apply(saved || (root.getAttribute('data-theme') === 'dark' || systemPrefersDark ? 'dark' : 'light'));
      if (toggle) {
        toggle.addEventListener('click', () => {
          const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
          apply(next);
          try { localStorage.setItem(KEY, next); } catch (e) {}
        });
      }
    })();

    // Responsive navigation · below the system's lg (1024) breakpoint the sidebar
    // becomes an off-canvas drawer (the Sheet pattern: scrim + side panel) opened
    // from a compact sticky bar. Everything here is additive — the [data-nav]
    // attribute is what switches the CSS on, so if this never runs the sidebar
    // just stacks above the content and stays usable.
    (function () {
      const sidebar = document.querySelector('.sidebar');
      const layout = document.querySelector('.app-layout');
      if (!sidebar || !layout) return;
      if (!sidebar.id) sidebar.id = 'sidebar-nav';

      const bar = document.createElement('header');
      bar.className = 'mobile-bar';
      bar.innerHTML =
        '<button type="button" class="mobile-bar-trigger" aria-expanded="false" aria-controls="' + sidebar.id + '" aria-label="Open navigation">' +
          '<span class="material-symbols-rounded" aria-hidden="true">menu</span>' +
        '</button>' +
        '<span class="mobile-bar-title">RBA</span>' +
        '<span class="mobile-bar-meta">Design System · <span class="js-version">v1.2</span></span>';
      layout.parentNode.insertBefore(bar, layout);

      const scrim = document.createElement('div');
      scrim.className = 'nav-scrim';
      document.body.appendChild(scrim);

      const trigger = bar.querySelector('.mobile-bar-trigger');
      const icon = trigger.querySelector('.material-symbols-rounded');
      let lastFocus = null;

      const isDrawerMode = () => window.matchMedia('(max-width: 1023.98px)').matches;
      const isOpen = () => sidebar.classList.contains('sidebar--open');

      function focusables() {
        // offsetParent!==null alone isn't enough: a collapsed sidebar section
        // uses grid-template-rows:0fr + overflow:hidden (see styles.css), which
        // clips content to zero height without display:none — its links keep a
        // non-null offsetParent and stay natively tabbable even though nothing
        // is visible. Exclude anything inside a section collapsed this way.
        return Array.from(sidebar.querySelectorAll('a[href], button:not([disabled]), input, [tabindex]:not([tabindex="-1"])'))
          .filter(el => el.offsetParent !== null && !el.closest('.sidebar-section[data-collapsed="true"]'));
      }

      function open() {
        lastFocus = document.activeElement;
        sidebar.classList.add('sidebar--open');
        scrim.classList.add('nav-scrim--visible');
        trigger.setAttribute('aria-expanded', 'true');
        trigger.setAttribute('aria-label', 'Close navigation');
        icon.textContent = 'close';
        document.body.style.overflow = 'hidden';
        // Land on the current section: reveal the active group and focus it, so the
        // focus trap has a target without .focus() scrolling the drawer back to the top.
        const active = rbaRevealActiveNav();
        if (active && active.focus) {
          active.focus();
          rbaRevealActiveNav(); // re-correct: focus() may nudge the scroll position
        } else {
          const f = focusables();
          if (f.length) f[0].focus();
        }
      }

      function close(returnFocus) {
        sidebar.classList.remove('sidebar--open');
        scrim.classList.remove('nav-scrim--visible');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-label', 'Open navigation');
        icon.textContent = 'menu';
        document.body.style.overflow = '';
        if (returnFocus !== false && lastFocus && lastFocus.focus) lastFocus.focus();
      }

      trigger.addEventListener('click', () => { isOpen() ? close() : open(); });
      scrim.addEventListener('click', () => close());

      // Following a link should reveal the destination, not leave the drawer over it.
      sidebar.addEventListener('click', (e) => {
        if (e.target.closest('a') && isDrawerMode() && isOpen()) close(false);
      });

      document.addEventListener('keydown', (e) => {
        if (!isOpen()) return;
        if (e.key === 'Escape') { e.stopPropagation(); close(); return; }
        if (e.key !== 'Tab') return;
        // Keep focus inside the drawer while it's acting as a modal surface.
        const f = focusables();
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }, true);

      // Crossing back above lg (window resize, tablet rotation) must never leave
      // the page scroll-locked or the drawer half-open. matchMedia fires exactly
      // on the breakpoint crossing; a bare resize listener proved unreliable and
      // could strand the desktop page with body overflow:hidden.
      const mq = window.matchMedia('(max-width: 1023.98px)');
      const syncToBreakpoint = () => { if (!mq.matches) close(false); };
      if (mq.addEventListener) mq.addEventListener('change', syncToBreakpoint);
      else if (mq.addListener) mq.addListener(syncToBreakpoint);
      window.addEventListener('resize', syncToBreakpoint);

      document.documentElement.setAttribute('data-nav', 'drawer');
    })();

    // Sidebar continuity across pages · on the desktop column, keep the active group
    // in view instead of resetting to the top of the nav (the mobile drawer handles
    // this itself, on open, in the drawer IIFE above).
    rbaRevealActiveNav();                                 // sync — set before first paint to avoid a jump
    window.addEventListener('load', rbaRevealActiveNav);  // re-run once web fonts settle row heights

    // Search · Cmd/Ctrl+K palette across every section of the system
    (function () {
      // Six sections, six entries. The keywords field is what makes this useful for
      // people who don't know our vocabulary — someone hunting the deck template
      // searches "powerpoint", not "templates".
      const INDEX = [
        { title: 'Colors',            category: 'Foundations', page: 'index.html',     anchor: '#colors',   keywords: 'palette hex swatch red midnight navy aqua blue grey gradient token' },
        { title: 'Typography',        category: 'Foundations', page: 'index.html',     anchor: '#type',     keywords: 'font fonts typeface montserrat libre caslon serif sans type scale heading body' },
        { title: 'Logos',             category: 'Foundations', page: 'index.html',     anchor: '#logo',     keywords: 'logo mark wordmark monogram clear space reversed svg' },
        { title: 'Icons',             category: 'Library',     page: 'icons.html',     anchor: '',          keywords: 'icon iconography glyph symbol svg download library' },
        { title: 'Brand images',      category: 'Library',     page: 'images.html',    anchor: '',          keywords: 'photo photography image picture illustration stock download' },
        { title: 'Templates & decks', category: 'Library',     page: 'templates.html', anchor: '',          keywords: 'powerpoint pptx deck slides word docx template letterhead document download' },
      ];

      const overlay = document.getElementById('search-overlay');
      const input = document.getElementById('search-input');
      const results = document.getElementById('search-results');
      const trigger = document.getElementById('search-trigger');
      if (!overlay || !input || !results) return;

      let activeIndex = -1;
      let filtered = [];
      let previouslyFocused = null;

      function currentPage() {
        const p = location.pathname.split('/').pop();
        return p === '' ? 'index.html' : p;
      }

      function setActive(i) {
        activeIndex = i;
        Array.from(results.children).forEach((el, idx) => {
          const isActive = idx === i;
          el.classList.toggle('search-result-item--active', isActive);
          if (el.id) el.setAttribute('aria-selected', String(isActive));
        });
        const el = results.children[i];
        if (el) {
          el.scrollIntoView({ block: 'nearest' });
          input.setAttribute('aria-activedescendant', el.id);
        } else {
          input.removeAttribute('aria-activedescendant');
        }
      }

      function go(item) {
        close();
        if (item.page === currentPage()) {
          // Already here — an empty anchor (e.g. the page's own index entry)
          // means there's nothing left to do but close, not reload the page
          // we're already on.
          if (item.anchor) {
            rbaJumpToHash(item.anchor);
            history.pushState(null, '', item.anchor);
          }
        } else {
          location.href = item.page + item.anchor;
        }
      }

      function render(list) {
        filtered = list;
        results.innerHTML = '';
        if (!list.length) {
          results.innerHTML = '<p class="search-empty">No matches.</p>';
          activeIndex = -1;
          input.removeAttribute('aria-activedescendant');
          return;
        }
        list.forEach((item, i) => {
          const row = document.createElement('button');
          row.type = 'button';
          row.className = 'search-result-item';
          row.id = 'search-result-' + i;
          row.setAttribute('role', 'option');
          row.setAttribute('aria-selected', 'false');
          row.setAttribute('tabindex', '-1');
          row.innerHTML =
            '<span class="search-result-title"></span><span class="search-result-category"></span>';
          row.querySelector('.search-result-title').textContent = item.title;
          row.querySelector('.search-result-category').textContent = item.category;
          row.addEventListener('mouseenter', () => setActive(i));
          row.addEventListener('click', () => go(item));
          results.appendChild(row);
        });
        setActive(0);
      }

      function filter(query) {
        const q = query.trim().toLowerCase();
        if (!q) return render(INDEX);
        // Keywords are searched but never displayed — they exist so "pptx" finds
        // Templates and "hex" finds Colors, without cluttering the result rows.
        render(INDEX.filter((i) =>
          i.title.toLowerCase().includes(q) ||
          i.category.toLowerCase().includes(q) ||
          (i.keywords || '').includes(q)
        ));
      }

      function open() {
        previouslyFocused = document.activeElement;
        overlay.hidden = false;
        input.value = '';
        input.setAttribute('aria-expanded', 'true');
        render(INDEX);
        document.body.style.overflow = 'hidden';
        requestAnimationFrame(() => input.focus());
      }
      function close() {
        overlay.hidden = true;
        input.setAttribute('aria-expanded', 'false');
        input.removeAttribute('aria-activedescendant');
        document.body.style.overflow = '';
        if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
          previouslyFocused.focus();
        }
        previouslyFocused = null;
      }

      if (trigger) trigger.addEventListener('click', open);
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
      });
      input.addEventListener('input', () => filter(input.value));
      input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setActive(Math.min(activeIndex + 1, filtered.length - 1));
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setActive(Math.max(activeIndex - 1, 0));
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (filtered[activeIndex]) go(filtered[activeIndex]);
        } else if (e.key === 'Tab') {
          // Result rows aren't tab-stops (arrow keys drive selection), so the
          // input is the only focusable element in the dialog — trap Tab here
          // rather than letting it escape to the page underneath.
          e.preventDefault();
        } else if (e.key === 'Escape') {
          close();
        }
      });
      document.addEventListener('keydown', (e) => {
        const isTypingField = /^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName);
        if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
          e.preventDefault();
          overlay.hidden ? open() : close();
        } else if (e.key === '/' && !isTypingField) {
          e.preventDefault();
          open();
        } else if (e.key === 'Escape' && !overlay.hidden) {
          close();
        }
      });
    })();

    // Clipboard helper + toast · shared by code blocks and token swatches.
    function rbaToast(message) {
      let toast = document.getElementById('rba-toast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'rba-toast';
        toast.className = 'rba-toast';
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        document.body.appendChild(toast);
      }
      toast.textContent = message;
      // force reflow so re-triggering restarts the transition
      void toast.offsetWidth;
      toast.classList.add('rba-toast--visible');
      clearTimeout(toast._rbaTimer);
      toast._rbaTimer = setTimeout(() => {
        toast.classList.remove('rba-toast--visible');
      }, 1800);
    }
    function rbaCopy(text, message) {
      const done = () => rbaToast(message || 'Copied');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(() => rbaCopyFallback(text, done));
      } else {
        rbaCopyFallback(text, done);
      }
    }
    function rbaCopyFallback(text, done) {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.top = '-9999px';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      try { document.execCommand('copy'); } catch (e) { /* no-op */ }
      document.body.removeChild(ta);
      done();
    }
    // Click-to-copy on tonal-ramp token swatches · copies the displayed hex.
    (function () {
      document.querySelectorAll('.palette-swatch').forEach((swatch) => {
        const hexEl = swatch.querySelector('.palette-swatch-hex');
        if (!hexEl) return;
        const hex = hexEl.textContent.trim();
        swatch.setAttribute('role', 'button');
        swatch.setAttribute('tabindex', '0');
        swatch.setAttribute('aria-label', 'Copy ' + hex);
        const copy = () => rbaCopy(hex, 'Copied ' + hex);
        swatch.addEventListener('click', copy);
        swatch.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); copy(); }
        });
      });
    })();

    // Version + last-updated · single source of truth. Bump RBA_VERSION on each
    // release; the updated date is derived from the page's own last-modified
    // timestamp so it never needs manual editing.
    (function () {
      const RBA_VERSION = '1.0';

      document.querySelectorAll('.js-version').forEach(el => {
        el.textContent = 'v' + RBA_VERSION;
      });

      const updatedEls = document.querySelectorAll('.js-updated');
      if (updatedEls.length) {
        const d = new Date(document.lastModified);
        if (!isNaN(d.getTime())) {
          const pad = n => String(n).padStart(2, '0');
          const stamp = pad(d.getMonth() + 1) + '.' + pad(d.getDate()) + '.' + d.getFullYear();
          updatedEls.forEach(el => { el.textContent = stamp; });
        }
      }
    })();

    // Bundle build date · the zip bundles under downloads/ are pre-built and committed,
    // because a static host can't zip on request. That makes staleness the one real
    // failure mode, so the date the bundles were last built is shown next to every
    // "download all" button rather than left implicit. tools/build-bundles.sh rewrites
    // the line below when it runs — keep it on one line, in this exact shape.
    const RBA_BUNDLE_BUILT = '2026-08-05';
    (function () {
      document.querySelectorAll('.js-bundle-date').forEach(el => {
        el.textContent = RBA_BUNDLE_BUILT;
      });
    })();

    // Asset library · renders the icon and image grids from an inlined JSON manifest,
    // then filters them by free text and category.
    //
    // The manifest is inlined in a <script type="application/json"> rather than fetched
    // so the page works when opened straight off disk — a fetch() of a local file is
    // blocked by the file:// origin rules, which would leave the grid permanently empty
    // for anyone who downloaded the repo instead of visiting the hosted site.
    //
    // Adding an asset is therefore two steps and no more: drop the file in assets/, add
    // its row to the manifest. Nothing here is generated at build time.
    (function () {
      const GRIDS = [
        { grid: 'icon-grid',  manifest: 'icon-manifest',  noun: 'icon',  render: iconTile },
        { grid: 'image-grid', manifest: 'image-manifest', noun: 'image', render: imageTile },
      ];

      // Icons are painted with a CSS mask, not an <img>. An <img> can't inherit
      // currentColor, so a single monochrome file could not follow the theme — it would
      // need a second, light-mode copy of every icon. The mask paints --icon's alpha
      // with the tile's own color instead, so one file serves both themes and stays
      // separately downloadable.
      function iconTile(item) {
        const cell = document.createElement('div');
        cell.className = 'glyph-cell';
        cell.setAttribute('data-file', item.file);
        cell.setAttribute('data-name', item.name);
        const glyph = document.createElement('span');
        glyph.className = 'glyph-cell-glyph';
        glyph.style.setProperty('--icon', 'url("' + item.file + '")');
        glyph.setAttribute('role', 'img');
        glyph.setAttribute('aria-label', item.name);
        const name = document.createElement('span');
        name.className = 'glyph-cell-name';
        name.textContent = item.name;
        const copy = document.createElement('button');
        copy.type = 'button';
        copy.className = 'glyph-cell-copy js-copy-svg';
        copy.setAttribute('data-file', item.file);
        copy.textContent = 'Copy SVG';
        cell.append(glyph, name, copy);
        if (item.placeholder) cell.setAttribute('data-placeholder', 'true');
        return cell;
      }

      function imageTile(item) {
        const card = document.createElement('div');
        card.className = 'photo-card';
        const frame = document.createElement('div');
        frame.className = 'photo-card-img';
        const img = document.createElement('img');
        img.src = item.file;
        img.alt = item.alt || item.name;
        img.loading = 'lazy';
        frame.appendChild(img);
        const label = document.createElement('div');
        label.className = 'photo-card-label';
        label.textContent = item.name;
        const meta = document.createElement('div');
        meta.className = 'photo-card-meta';
        meta.textContent = [item.format, item.dimensions, item.size].filter(Boolean).join(' · ');
        card.append(frame, label, meta);
        if (item.placeholder) card.setAttribute('data-placeholder', 'true');
        return card;
      }

      GRIDS.forEach(cfg => {
        const grid = document.getElementById(cfg.grid);
        const dataEl = document.getElementById(cfg.manifest);
        if (!grid || !dataEl) return;               // no-ops on every other page

        let items = [];
        try {
          items = (JSON.parse(dataEl.textContent) || {}).items || [];
        } catch (e) {
          grid.innerHTML = '<p class="lib-empty">The manifest for this page could not be read. ' +
                           'View source and check the <code>#' + cfg.manifest + '</code> block.</p>';
          return;
        }

        const scope = grid.closest('.lib-scope') || document;
        const search = scope.querySelector('.lib-search-input');
        const chips = scope.querySelector('.lib-filter');
        const count = scope.querySelector('.lib-count');

        // One chip per category actually present, so the filter can never offer an
        // option that matches nothing.
        const categories = [];
        items.forEach(i => { if (i.category && categories.indexOf(i.category) < 0) categories.push(i.category); });
        let activeCat = 'all';

        if (chips) {
          const mk = (value, label, pressed) => {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'lib-filter-btn';
            b.setAttribute('data-filter', value);
            b.setAttribute('aria-pressed', pressed ? 'true' : 'false');
            b.textContent = label;
            return b;
          };
          chips.appendChild(mk('all', 'All', true));
          categories.forEach(c => chips.appendChild(mk(c, c, false)));
          chips.addEventListener('click', ev => {
            const btn = ev.target.closest('.lib-filter-btn');
            if (!btn) return;
            activeCat = btn.getAttribute('data-filter');
            chips.querySelectorAll('.lib-filter-btn').forEach(b => {
              b.setAttribute('aria-pressed', String(b === btn));
            });
            apply();
          });
        }

        function matches(item, q) {
          if (activeCat !== 'all' && item.category !== activeCat) return false;
          if (!q) return true;
          const hay = [item.name, item.category, (item.tags || []).join(' ')].join(' ').toLowerCase();
          return hay.indexOf(q) > -1;
        }

        function apply() {
          const q = search ? search.value.trim().toLowerCase() : '';
          let shown = 0;
          Array.from(grid.children).forEach((el, i) => {
            const hit = matches(items[i], q);
            el.hidden = !hit;
            if (hit) shown++;
          });
          if (count) {
            count.textContent = shown === items.length
              ? shown + ' ' + cfg.noun + (shown === 1 ? '' : 's')
              : shown + ' of ' + items.length + ' ' + cfg.noun + (items.length === 1 ? '' : 's');
          }
          let empty = grid.nextElementSibling;
          if (empty && empty.classList.contains('lib-empty')) empty.hidden = shown > 0;
        }

        const frag = document.createDocumentFragment();
        items.forEach(item => frag.appendChild(cfg.render(item)));
        grid.appendChild(frag);

        if (search) {
          search.addEventListener('input', apply);
          // Escape clears rather than blurring — the filter is the page's primary
          // control here, so getting back to "everything" should not cost a reach
          // for the mouse.
          search.addEventListener('keydown', ev => {
            if (ev.key === 'Escape' && search.value) { search.value = ''; apply(); }
          });
        }
        apply();
      });
    })();

    // Copy SVG · reads an icon's source file and puts its markup on the clipboard, for
    // pasting straight into a template or a codebase.
    //
    // This one genuinely needs a served origin: fetching a local file from a file://
    // page is blocked, and there is no workaround that doesn't mean inlining every
    // icon's markup into the page. So rather than fail on click, the buttons remove
    // themselves when the page isn't served — the download route still works, and an
    // absent button is honest where a broken one is not.
    (function () {
      const btns = document.querySelectorAll('.js-copy-svg');
      if (!btns.length) return;

      const canFetch = location.protocol === 'http:' || location.protocol === 'https:';
      if (!canFetch || !navigator.clipboard) {
        btns.forEach(b => b.remove());
        return;
      }

      document.addEventListener('click', ev => {
        const btn = ev.target.closest('.js-copy-svg');
        if (!btn) return;
        ev.preventDefault();
        ev.stopPropagation();
        const file = btn.getAttribute('data-file');
        if (!file) return;
        fetch(file)
          .then(r => { if (!r.ok) throw new Error(r.status); return r.text(); })
          .then(text => rbaCopy(text, 'SVG copied'))
          .catch(() => rbaToast("Couldn't read that file"));
      });
    })();

    // Asset downloads · injects a hover "download" button onto every asset tile, so a
    // logo colorway, an icon, or a photograph can be pulled straight off the page.
    //   - Inline SVG (the logo colorways) is serialized to a standalone file: <use>
    //     refs are inlined from their <symbol>, and the tile's computed color plus
    //     --mark-fill are baked on as literals so the file is correct when opened
    //     outside a browser.
    //   - File-backed assets (icons, photography) download their source file
    //     directly. Those tiles also carry a plain <a download> link, so the button
    //     here is a convenience, not the only route.
    (function () {
      const SVGNS = 'http://www.w3.org/2000/svg';
      const XLINK = 'http://www.w3.org/1999/xlink';
      const slug = s => (s || '').toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

      function trigger(href, name, revoke) {
        const a = document.createElement('a');
        a.href = href; a.download = name;
        document.body.appendChild(a); a.click(); a.remove();
        if (revoke) setTimeout(() => URL.revokeObjectURL(href), 1500);
      }

      function serialize(svg) {
        const clone = svg.cloneNode(true);
        clone.querySelectorAll('use').forEach(u => {
          const href = (u.getAttribute('href') || u.getAttributeNS(XLINK, 'href') || '').trim();
          const ref = href && document.querySelector(href);
          if (!ref) return;
          const g = document.createElementNS(SVGNS, 'g');
          Array.from(ref.childNodes).forEach(n => g.appendChild(n.cloneNode(true)));
          u.replaceWith(g);
        });
        const cs = getComputedStyle(svg);
        const mf = cs.getPropertyValue('--mark-fill').trim();
        let style = 'color:' + cs.color + ';';
        if (mf) style += '--mark-fill:' + mf + ';';
        clone.setAttribute('xmlns', SVGNS);
        clone.removeAttribute('class');
        clone.setAttribute('style', style);
        // The monogram path carries its own inline `fill: var(--mark-fill, …)` from the
        // source symbol. Setting the custom property on the root is enough for a
        // browser, but many standalone SVG consumers (Preview, older design tools,
        // thumbnailers) don't resolve CSS custom properties at all — they fall through
        // to the static fallback, so every colorway but the default would download with
        // the wrong monogram color. Bake the resolved literal in place of the var()
        // reference so the file renders correctly with zero custom-property support.
        clone.querySelectorAll('[style*="--mark-fill"]').forEach(el => {
          let s = el.getAttribute('style');
          // Always resolve to a literal — even when mf is empty, substitute var()'s own
          // fallback text rather than leaving the reference in place. A renderer with no
          // var() support doesn't know to apply that fallback; it just drops the
          // declaration and the path renders black.
          s = s.replace(/var\(--mark-fill\s*(?:,\s*([^)]+))?\)/g, (_, fallback) => mf || fallback || '#C8252D');
          el.setAttribute('style', s);
        });
        const out = '<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(clone);
        return URL.createObjectURL(new Blob([out], { type: 'image/svg+xml' }));
      }

      function attach(host, name, srcFn) {
        if (!host || host.querySelector(':scope > .asset-dl')) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'asset-dl';
        btn.innerHTML = '<span class="material-symbols-rounded" aria-hidden="true">download</span>';
        btn.setAttribute('aria-label', 'Download ' + name);
        btn.title = 'Download ' + name;
        btn.addEventListener('click', ev => {
          ev.preventDefault(); ev.stopPropagation();
          const src = srcFn();
          if (src.file) trigger(src.file, name);
          else if (src.svg) trigger(serialize(src.svg), name, true);
        });
        host.appendChild(btn);
      }

      // Logo colorways → serialized colored SVG (colorway read off the modifier class)
      document.querySelectorAll('.logo-card').forEach(card => {
        const svg = card.querySelector('svg.brand-logo');
        if (!svg) return;
        const cls = Array.from(svg.classList).find(c => c.indexOf('brand-logo--') === 0);
        const v = cls ? cls.slice('brand-logo--'.length) : 'mark';
        attach(card, 'rba-logo-' + v + '.svg', () => ({ svg }));
      });
      // Icons → the source SVG file. The glyph is painted with a CSS mask rather than
      // an <img>, so the filename comes off the tile's data-file instead of a src.
      document.querySelectorAll('.glyph-cell').forEach((cell, i) => {
        const file = cell.getAttribute('data-file');
        if (!file) return;
        attach(cell, file.split('/').pop() || ('rba-icon-' + (i + 1) + '.svg'), () => ({ file }));
      });
      // Photography → the source image file
      document.querySelectorAll('.photo-card').forEach(card => {
        const img = card.querySelector('img');
        if (!img) return;
        const file = img.getAttribute('src');
        attach(card.querySelector('.photo-card-img') || card, file.split('/').pop(), () => ({ file }));
      });
    })();
