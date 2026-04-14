/**
 * static/js/panel.js — Panel catálogo: vista previa de imagen (URL o archivo).
 * Plantilla: templates/panel/producto_form.html
 */
(function () {
    "use strict";

    function escUrl(u) {
        if (!u || typeof u !== "string") {
            return "";
        }
        try {
            if (u.indexOf("://") !== -1 || u.indexOf("/") === 0) {
                return u;
            }
        } catch (e) {
            return "";
        }
        return u;
    }

    function initImagenPreview() {
        var form = document.getElementById("panel-producto-form");
        if (!form) {
            return;
        }
        var urlInput = document.getElementById("id_imagen_url");
        var fileInput =
            document.getElementById("id_imagen_archivo") ||
            form.querySelector('input[type="file"][name="imagen"]');
        var img = document.getElementById("panel-imagen-preview-img");
        var box = document.getElementById("panel-imagen-preview-box");
        var toggle = document.getElementById("panel-imagen-preview-toggle");
        var card = document.getElementById("panel-imagen-preview-card");
        if (!img || !box || !toggle) {
            return;
        }

        var inicial = form.getAttribute("data-preview-inicial") || "";
        var objectUrl = null;

        function releaseObjectUrl() {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
                objectUrl = null;
            }
        }

        function setSrc(src) {
            img.removeAttribute("src");
            if (src) {
                img.src = src;
            }
        }

        function syncPreview() {
            releaseObjectUrl();
            if (fileInput && fileInput.files && fileInput.files[0]) {
                objectUrl = URL.createObjectURL(fileInput.files[0]);
                setSrc(objectUrl);
                if (card) {
                    card.classList.remove("d-none");
                }
                return;
            }
            var u = urlInput && urlInput.value ? urlInput.value.trim() : "";
            if (u) {
                setSrc(escUrl(u));
                if (card) {
                    card.classList.remove("d-none");
                }
            } else if (inicial) {
                setSrc(escUrl(inicial));
                if (card) {
                    card.classList.remove("d-none");
                }
            } else {
                setSrc("");
                if (card) {
                    card.classList.add("d-none");
                }
            }
        }

        syncPreview();

        if (urlInput) {
            urlInput.addEventListener("input", syncPreview);
            urlInput.addEventListener("change", syncPreview);
        }
        if (fileInput) {
            fileInput.addEventListener("change", syncPreview);
        }

        toggle.addEventListener("click", function () {
            var open = box.classList.contains("d-none");
            box.classList.toggle("d-none", !open);
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
            toggle.textContent = open ? "Ocultar vista previa" : "Mostrar vista previa";
        });
    }

    function initDownloadChartPng() {
        window.panelDownloadChartPng = function (canvasId, fileBase) {
            var c = document.getElementById(canvasId);
            if (!c || !c.toDataURL) {
                return;
            }
            var a = document.createElement("a");
            a.href = c.toDataURL("image/png");
            a.download = (fileBase || "babyviip_grafico") + ".png";
            a.rel = "noopener";
            a.click();
        };
    }

    function initSimuladorCompra() {
        var form = document.getElementById("panel-simulador-form");
        if (!form) return;

        var modoSel = form.querySelector('select[name="modo"]');
        var lineCount = form.querySelector('input[name="line_count"]');
        var banner = document.getElementById("panel-simulador-modo-banner");
        var bannerText = document.getElementById("panel-simulador-modo-text");
        var confirmWrap = document.getElementById("panel-simulador-confirm-wrap");
        var confirmInput = form.querySelector('input[name="confirmar_permanente"]');
        var tabla = document.getElementById("panel-simulador-tabla");
        var addBtn = document.getElementById("panel-simulador-add-line");
        var variantesUrl = form.getAttribute("data-variantes-url") || "";
        var totalEl = document.getElementById("panel-sim-total");
        var impactoEl = document.getElementById("panel-sim-impacto");

        var acTimer = null;
        var acLastQ = "";
        var acAbort = null;

        function debounce(fn, ms) {
            return function () {
                var args = arguments;
                clearTimeout(acTimer);
                acTimer = setTimeout(function () {
                    fn.apply(null, args);
                }, ms);
            };
        }

        function closeAc(row) {
            var box = row ? row.querySelector(".panel-sim-ac") : null;
            if (!box) return;
            box.innerHTML = "";
            box.classList.remove("panel-sim-ac--open");
            var search = row ? row.querySelector(".panel-sim-search") : null;
            if (search) {
                search.setAttribute("aria-expanded", "false");
            }
        }

        function renderAc(row, items) {
            var box = row.querySelector(".panel-sim-ac");
            if (!box) return;
            if (!box.id) {
                box.id = "panel-sim-ac-" + String(row.getAttribute("data-prefix") || "");
            }
            if (!items || !items.length) {
                box.innerHTML =
                    '<div class="panel-sim-ac__empty">Sin resultados</div>';
                box.classList.add("panel-sim-ac--open");
                row.__acIndex = -1;
                box.setAttribute("role", "listbox");
                var search0 = row.querySelector(".panel-sim-search");
                if (search0) {
                    search0.setAttribute("aria-expanded", "true");
                    search0.setAttribute("aria-controls", box.id);
                }
                return;
            }
            var html = "";
            for (var i = 0; i < items.length; i++) {
                var it = items[i];
                var badgeClass = "panel-sim-badge--ok";
                var badgeText = "Stock OK";
                var stockNum = Number(it.stock || 0);
                if (stockNum <= 0) {
                    badgeClass = "panel-sim-badge--out";
                    badgeText = "Agotado";
                } else if (stockNum <= 3) {
                    badgeClass = "panel-sim-badge--low";
                    badgeText = "Stock bajo";
                }
                html +=
                    '<button type="button" role="option" aria-selected="false" tabindex="-1" class="panel-sim-ac__item" data-id="' +
                    String(it.id) +
                    '" data-stock="' +
                    String(it.stock) +
                    '" data-precio="' +
                    String(it.precio) +
                    '">' +
                    '<span class="panel-sim-badge ' + badgeClass + '">' + badgeText + "</span>" +
                    String(it.label) +
                    "</button>";
            }
            box.innerHTML = html;
            box.classList.add("panel-sim-ac--open");
            box.setAttribute("role", "listbox");
            var search1 = row.querySelector(".panel-sim-search");
            if (search1) {
                search1.setAttribute("aria-expanded", "true");
                search1.setAttribute("aria-controls", box.id);
            }
            row.__acIndex = 0;
            setActiveAcIndex(row, 0);
        }

        function setActiveAcIndex(row, idx) {
            if (!row) return;
            var box = row.querySelector(".panel-sim-ac");
            if (!box) return;
            var items = box.querySelectorAll(".panel-sim-ac__item");
            if (!items.length) return;
            var i;
            for (i = 0; i < items.length; i++) {
                items[i].classList.remove("is-active");
                items[i].setAttribute("aria-selected", "false");
            }
            var clamped = Math.max(0, Math.min(items.length - 1, idx));
            items[clamped].classList.add("is-active");
            items[clamped].setAttribute("aria-selected", "true");
            row.__acIndex = clamped;
            try {
                items[clamped].scrollIntoView({ block: "nearest" });
            } catch (e) {}
        }

        function setSelected(row, id, stock, precio, label) {
            var select = row.querySelector("select");
            if (select) {
                select.value = String(id);
            }
            var meta = row.querySelector(".panel-sim-meta");
            if (meta) {
                meta.textContent = "stock " + String(stock) + " · $" + String(precio);
            }
            row.setAttribute("data-sel-precio", String(precio || ""));
            row.setAttribute("data-sel-stock", String(stock || ""));
            var search = row.querySelector(".panel-sim-search");
            if (search && label) {
                search.value = label;
            }
            var qty = row.querySelector('input[type="number"]');
            if (qty) {
                var qn = Number(qty.value || 0);
                if (!qn || qn <= 0) qty.value = "1";
            }
            closeAc(row);
            syncResumen();
        }

        function fetchVariantes(row, q) {
            if (!variantesUrl) return;
            var qq = (q || "").trim();
            if (qq.length < 2) {
                closeAc(row);
                return;
            }
            if (acAbort) {
                try { acAbort.abort(); } catch (e) {}
            }
            acAbort = new AbortController();
            var url = variantesUrl + "?q=" + encodeURIComponent(qq);
            fetch(url, { credentials: "same-origin", signal: acAbort.signal })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (!data || !data.ok) return;
                    renderAc(row, data.items || []);
                })
                .catch(function () { /* ignore */ });
        }

        function syncResumen() {
            // total estimado: suma precio seleccionado * cantidad
            if (!tabla || !totalEl) return;
            var rows = tabla.querySelectorAll("tbody tr.panel-sim-line");
            var total = 0;
            for (var i = 0; i < rows.length; i++) {
                var r = rows[i];
                var p = Number(r.getAttribute("data-sel-precio") || 0);
                var qtyEl = r.querySelector('input[type="number"]');
                var qn = qtyEl ? Number(qtyEl.value || 0) : 0;
                if (p > 0 && qn > 0) {
                    total += p * qn;
                }
            }
            totalEl.textContent = "$" + String(Math.round(total));
            if (impactoEl && modoSel) {
                var m = String(modoSel.value || "").toLowerCase();
                if (m === "permanente") impactoEl.textContent = "Venta real (afecta stock y reportes)";
                else if (m === "temporal") impactoEl.textContent = "Simulación reversible (descuenta stock; puede revertirse)";
                else impactoEl.textContent = "Sin impacto (no crea venta ni descuenta stock)";
            }
        }

        function setBanner(modo) {
            if (!banner || !bannerText) return;
            var m = (modo || "").toLowerCase();
            banner.classList.remove("alert-secondary", "alert-warning", "alert-danger");
            if (m === "permanente") {
                banner.classList.add("alert-danger");
                bannerText.textContent = "Permanente (venta real)";
                if (confirmWrap) confirmWrap.classList.remove("d-none");
            } else if (m === "temporal") {
                banner.classList.add("alert-warning");
                bannerText.textContent = "Temporal (simulación reversible)";
                if (confirmWrap) confirmWrap.classList.add("d-none");
                if (confirmInput) confirmInput.checked = false;
            } else {
                banner.classList.add("alert-secondary");
                bannerText.textContent = "Sin impacto";
                if (confirmWrap) confirmWrap.classList.add("d-none");
                if (confirmInput) confirmInput.checked = false;
            }
            syncResumen();
        }

        function syncLineCount() {
            if (!lineCount || !tabla) return;
            var rows = tabla.querySelectorAll("tbody tr.panel-sim-line");
            lineCount.value = String(rows.length || 1);
        }

        function wireRow(row) {
            if (!row) return;
            var search = row.querySelector(".panel-sim-search");
            var select = row.querySelector("select");
            var remove = row.querySelector(".panel-sim-remove");
            if (search && select) {
                search.setAttribute("role", "combobox");
                search.setAttribute("aria-autocomplete", "list");
                search.setAttribute("aria-haspopup", "listbox");
                search.setAttribute("aria-expanded", "false");
                var run = debounce(function () {
                    var q = (search.value || "").trim();
                    if (q === acLastQ) return;
                    acLastQ = q;
                    fetchVariantes(row, q);
                }, 200);
                search.addEventListener("input", run);
                search.addEventListener("focus", run);
                search.addEventListener("keydown", function (ev) {
                    var box = row.querySelector(".panel-sim-ac");
                    if (!box || !box.classList.contains("panel-sim-ac--open")) return;
                    var items = box.querySelectorAll(".panel-sim-ac__item");
                    if (!items.length) return;
                    var idx = typeof row.__acIndex === "number" ? row.__acIndex : 0;
                    if (ev.key === "ArrowDown") {
                        ev.preventDefault();
                        setActiveAcIndex(row, idx + 1);
                    } else if (ev.key === "ArrowUp") {
                        ev.preventDefault();
                        setActiveAcIndex(row, idx - 1);
                    } else if (ev.key === "Enter") {
                        ev.preventDefault();
                        var t = items[Math.max(0, Math.min(items.length - 1, idx))];
                        if (!t) return;
                        setSelected(
                            row,
                            t.getAttribute("data-id"),
                            t.getAttribute("data-stock"),
                            t.getAttribute("data-precio"),
                            t.textContent || ""
                        );
                    } else if (ev.key === "Escape") {
                        ev.preventDefault();
                        closeAc(row);
                    } else if (ev.key === "Tab") {
                        // dejar que el foco avance, pero cerrar el dropdown
                        closeAc(row);
                    }
                });
                // clicks en resultados
                var box = row.querySelector(".panel-sim-ac");
                if (box) {
                    // Evitar que el blur del input cierre antes de seleccionar
                    box.addEventListener("mousedown", function (ev) {
                        if (ev && ev.preventDefault) ev.preventDefault();
                    });
                    box.addEventListener("click", function (ev) {
                        var t = ev.target;
                        if (!t || !t.getAttribute) return;
                        if (!t.classList.contains("panel-sim-ac__item")) return;
                        var id = t.getAttribute("data-id");
                        var stock = t.getAttribute("data-stock");
                        var precio = t.getAttribute("data-precio");
                        var label = t.textContent || "";
                        setSelected(row, id, stock, precio, label);
                    });
                }
                // cambio manual de select => actualizar meta
                select.addEventListener("change", function () {
                    closeAc(row);
                    var opt = select.options[select.selectedIndex];
                    if (!opt) return;
                    // no tenemos stock/precio aquí; dejamos meta en —
                    row.removeAttribute("data-sel-precio");
                    row.removeAttribute("data-sel-stock");
                    var meta = row.querySelector(".panel-sim-meta");
                    if (meta) meta.textContent = "—";
                    syncResumen();
                });
                // cerrar al hacer blur (con pequeño delay para permitir click)
                search.addEventListener("blur", function () {
                    setTimeout(function () { closeAc(row); }, 160);
                });
            }
            var qty = row.querySelector('input[type="number"]');
            if (qty) {
                qty.addEventListener("input", function () {
                    syncResumen();
                });
            }
            if (remove) {
                remove.addEventListener("click", function () {
                    var tbody = row.parentElement;
                    if (!tbody) return;
                    row.remove();
                    // mantener al menos 1 línea
                    if (tbody.querySelectorAll("tr.panel-sim-line").length === 0) {
                        // si no quedan, reinsertar una copiando la plantilla base
                        if (window.__panelSimTemplateRow) {
                            tbody.appendChild(window.__panelSimTemplateRow.cloneNode(true));
                            wireRow(tbody.lastElementChild);
                        }
                    }
                    syncLineCount();
                    syncResumen();
                });
            }
        }

        function buildTemplateRow() {
            if (!tabla) return null;
            var first = tabla.querySelector("tbody tr.panel-sim-line");
            if (!first) return null;
            var tpl = first.cloneNode(true);
            // limpiar valores
            var search = tpl.querySelector(".panel-sim-search");
            if (search) search.value = "";
            var qty = tpl.querySelector('input[type="number"]');
            if (qty) qty.value = "1";
            var meta = tpl.querySelector(".panel-sim-meta");
            if (meta) meta.textContent = "—";
            closeAc(tpl);
            tpl.removeAttribute("data-sel-precio");
            tpl.removeAttribute("data-sel-stock");
            return tpl;
        }

        // init
        setBanner(modoSel ? modoSel.value : "");
        if (modoSel) modoSel.addEventListener("change", function () { setBanner(modoSel.value); });

        if (confirmWrap) confirmWrap.classList.add("d-none");
        if (modoSel) setBanner(modoSel.value);

        if (tabla) {
            var rows = tabla.querySelectorAll("tbody tr.panel-sim-line");
            for (var i = 0; i < rows.length; i++) wireRow(rows[i]);
            window.__panelSimTemplateRow = buildTemplateRow();
            syncLineCount();
            syncResumen();
        }

        if (addBtn && tabla) {
            addBtn.addEventListener("click", function () {
                var tbody = tabla.querySelector("tbody");
                if (!tbody) return;
                var count = tbody.querySelectorAll("tr.panel-sim-line").length;
                if (count >= 30) return;
                var row = window.__panelSimTemplateRow
                    ? window.__panelSimTemplateRow.cloneNode(true)
                    : null;
                if (!row) return;

                // Reescribir prefix para que el servidor lo lea (lN-*)
                var next = count + 1;
                row.setAttribute("data-prefix", "l" + next);
                var sel = row.querySelector("select");
                var qty = row.querySelector('input[type="number"]');
                if (sel && sel.name) sel.name = "l" + next + "-variante";
                if (sel && sel.id) sel.id = "id_l" + next + "-variante";
                if (qty && qty.name) qty.name = "l" + next + "-cantidad";
                if (qty && qty.id) qty.id = "id_l" + next + "-cantidad";
                // también actualizar label/for si existiera (no hay)

                tbody.appendChild(row);
                wireRow(row);
                syncLineCount();
            });
        }
    }

    function initPanelNavScroll() {
        var scroller = document.querySelector(".panel-nav-scroller");
        if (!scroller) return;
        var btnL = document.querySelector(".panel-nav-scroll-btn--left");
        var btnR = document.querySelector(".panel-nav-scroll-btn--right");
        if (!btnL || !btnR) return;
        var STORAGE_KEY = "babyviip_panel_nav_scroll_left";

        function step() {
            // scroll “por pantalla” (un poco menos que el ancho visible)
            return Math.max(140, Math.floor(scroller.clientWidth * 0.75));
        }

        function syncDisabled() {
            var max = Math.max(0, scroller.scrollWidth - scroller.clientWidth);
            var x = scroller.scrollLeft || 0;
            // No usar disabled (puede bloquear clicks aunque haya overflow por layout tardío).
            // Solo marcamos visualmente.
            if (max <= 0) {
                btnL.classList.add("is-disabled");
                btnR.classList.add("is-disabled");
                return;
            }
            btnL.classList.toggle("is-disabled", x <= 2);
            btnR.classList.toggle("is-disabled", x >= max - 2);
        }

        function savePos() {
            try {
                window.sessionStorage.setItem(
                    STORAGE_KEY,
                    String(Math.max(0, Math.floor(scroller.scrollLeft || 0)))
                );
            } catch (e) {}
        }

        function restorePos() {
            try {
                var raw = window.sessionStorage.getItem(STORAGE_KEY);
                if (!raw) return;
                var x = parseInt(raw, 10);
                if (!isFinite(x) || x < 0) return;
                scroller.scrollLeft = x;
            } catch (e) {}
        }

        function nudge(dx) {
            // Utilidad: ajustar scroll del contenedor si hace falta.
            try {
                scroller.scrollBy({ left: dx, behavior: "smooth" });
            } catch (e) {}
            scroller.scrollLeft = (scroller.scrollLeft || 0) + dx;
            window.setTimeout(syncDisabled, 60);
        }

        function links() {
            return Array.prototype.slice.call(scroller.querySelectorAll("a.nav-link"));
        }

        function activeIndex(arr) {
            for (var i = 0; i < arr.length; i++) {
                if (arr[i].classList && arr[i].classList.contains("nav-link--active")) {
                    return i;
                }
            }
            return -1;
        }

        function go(dir) {
            var arr = links();
            if (!arr.length) return;
            var ix = activeIndex(arr);
            if (ix < 0) ix = 0;
            var next = Math.max(0, Math.min(arr.length - 1, ix + dir));
            var a = arr[next];
            if (!a || !a.href) return;
            // Asegurar visibilidad del target dentro del scroller
            try {
                a.scrollIntoView({ block: "nearest", inline: "nearest" });
            } catch (e) {
                // fallback: mover un poco hacia el lado
                nudge(dir * step());
            }
            savePos();
            window.location.href = a.href;
        }

        // Click: pestaña anterior/siguiente
        btnL.addEventListener("click", function (ev) {
            if (ev && ev.preventDefault) ev.preventDefault();
            if (ev && ev.stopPropagation) ev.stopPropagation();
            go(-1);
        });
        btnR.addEventListener("click", function (ev) {
            if (ev && ev.preventDefault) ev.preventDefault();
            if (ev && ev.stopPropagation) ev.stopPropagation();
            go(1);
        });

        // Mantener apretado: movimiento continuo
        var holdTimer = null;
        function startHold(dir) {
            if (holdTimer) window.clearInterval(holdTimer);
            holdTimer = window.setInterval(function () {
                go(dir);
            }, 240);
        }
        function stopHold() {
            if (holdTimer) window.clearInterval(holdTimer);
            holdTimer = null;
        }
        ["mousedown", "pointerdown", "touchstart"].forEach(function (evName) {
            btnL.addEventListener(evName, function (ev) {
                if (ev && ev.preventDefault) ev.preventDefault();
                if (ev && ev.stopPropagation) ev.stopPropagation();
                startHold(-1);
            });
            btnR.addEventListener(evName, function (ev) {
                if (ev && ev.preventDefault) ev.preventDefault();
                if (ev && ev.stopPropagation) ev.stopPropagation();
                startHold(1);
            });
        });
        ["mouseup", "mouseleave", "pointerup", "pointercancel", "touchend", "touchcancel"].forEach(
            function (evName) {
                btnL.addEventListener(evName, stopHold);
                btnR.addEventListener(evName, stopHold);
            }
        );
        scroller.addEventListener("scroll", function () {
            syncDisabled();
            savePos();
        });
        // Guardar posición antes de navegar (click en pestañas)
        scroller.addEventListener("click", function (ev) {
            var t = ev && ev.target ? ev.target : null;
            if (!t) return;
            // si se clickea un link dentro del scroller, guardar
            if (t.tagName === "A" || (t.closest && t.closest("a"))) {
                savePos();
            }
        });
        window.addEventListener("resize", function () {
            syncDisabled();
        });
        // Esperar a que el layout termine (fonts/badges pueden cambiar widths)
        try {
            window.requestAnimationFrame(function () {
                restorePos();
                syncDisabled();
                window.setTimeout(syncDisabled, 180);
            });
        } catch (e) {
            window.setTimeout(function () {
                restorePos();
                syncDisabled();
            }, 0);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        initImagenPreview();
        initDownloadChartPng();
        initSimuladorCompra();
        initPanelNavScroll();
    });
})();
