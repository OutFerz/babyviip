/**
 * catalogo.js — Búsqueda + favoritos (⭐ local o servidor) + filtros + paginación.
 * Datos: #catalogo-data · Config: #catalogo-config (csrf, favoritos servidor, sesión).
 * Plantilla: templates/catalogo.html
 */
(function () {
    "use strict";

    var STORAGE_FAV = "babyviip_favoritos";
    var DEBOUNCE_MS = 260;
    var BUSQUEDA_LOG_DEBOUNCE_MS = 750;

    function norm(s) {
        return String(s || "")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    function parseConfig() {
        var el = document.getElementById("catalogo-config");
        if (!el) {
            return { userAuth: false, favoritosServidor: [], csrf: "" };
        }
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            return { userAuth: false, favoritosServidor: [], csrf: "" };
        }
    }

    function initCatalogo() {
        var cfg = parseConfig();
        var userAuth = !!cfg.userAuth;
        var serverFavs = (cfg.favoritosServidor || []).map(function (x) {
            return parseInt(x, 10);
        });
        var csrfToken = cfg.csrf || "";

        function getFavoritosLocal() {
            try {
                var raw = localStorage.getItem(STORAGE_FAV);
                var arr = raw ? JSON.parse(raw) : [];
                return arr.map(function (x) {
                    return String(x);
                });
            } catch (e) {
                return [];
            }
        }

        function setFavoritosLocal(ids) {
            localStorage.setItem(STORAGE_FAV, JSON.stringify(ids));
        }

        function toggleFavoritoLocal(productId) {
            var id = String(productId);
            var s = getFavoritosLocal();
            var i = s.indexOf(id);
            if (i >= 0) {
                s.splice(i, 1);
            } else {
                s.push(id);
            }
            setFavoritosLocal(s);
            return s.indexOf(id) >= 0;
        }

        function isFavorito(productId) {
            var id = String(productId);
            if (userAuth) {
                return serverFavs.indexOf(parseInt(id, 10)) >= 0;
            }
            return getFavoritosLocal().indexOf(id) >= 0;
        }

        function toggleFavoritoAsync(productId) {
            var id = String(productId);
            if (!userAuth) {
                return Promise.resolve(toggleFavoritoLocal(id));
            }
            return fetch("/api/catalogo/favorito/", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({ producto_id: parseInt(id, 10) }),
            })
                .then(function (r) {
                    if (r.status === 401) {
                        window.location.href = "/accounts/login/?next=" + encodeURIComponent("/catalogo/");
                        return { favorito: false };
                    }
                    return r.json();
                })
                .then(function (data) {
                    var pid = parseInt(id, 10);
                    var on = !!data.favorito;
                    var ix = serverFavs.indexOf(pid);
                    if (on && ix < 0) {
                        serverFavs.push(pid);
                    }
                    if (!on && ix >= 0) {
                        serverFavs.splice(ix, 1);
                    }
                    return on;
                })
                .catch(function () {
                    return isFavorito(productId);
                });
        }

        var lastBusquedaLog = 0;
        var lastBusquedaTerm = "";
        function maybeLogBusqueda(raw) {
            var q = (raw || "").trim();
            if (q.length < 2 || !csrfToken) {
                return;
            }
            var now = Date.now();
            if (q === lastBusquedaTerm && now - lastBusquedaLog < 25000) {
                return;
            }
            lastBusquedaLog = now;
            lastBusquedaTerm = q;
            var fd = new FormData();
            fd.append("termino", q.slice(0, 100));
            fd.append("csrfmiddlewaretoken", csrfToken);
            fetch("/api/catalogo/busqueda/", {
                method: "POST",
                body: fd,
                credentials: "same-origin",
            }).catch(function () {});
        }

        function productoCoincideQuery(p, qn) {
            if (!qn) {
                return true;
            }
            if (norm(p.nombre).indexOf(qn) !== -1) {
                return true;
            }
            if (norm(p.material).indexOf(qn) !== -1) {
                return true;
            }
            for (var i = 0; i < p.variantes.length; i++) {
                var v = p.variantes[i];
                if (
                    norm(v.sku).indexOf(qn) !== -1 ||
                    norm(v.talla).indexOf(qn) !== -1 ||
                    norm(v.color).indexOf(qn) !== -1
                ) {
                    return true;
                }
            }
            return false;
        }

        function productoTieneStock(p) {
            var j;
            for (j = 0; j < p.variantes.length; j++) {
                if (p.variantes[j].stock > 0) {
                    return true;
                }
            }
            return false;
        }

        function productoTodoAgotado(p) {
            if (!p.variantes.length) {
                return false;
            }
            var j;
            for (j = 0; j < p.variantes.length; j++) {
                if (p.variantes[j].stock > 0) {
                    return false;
                }
            }
            return true;
        }

        function sugerenciasAutocomplete(data, qn, limit, favOnly) {
            if (!qn || qn.length < 1) {
                return [];
            }
            var seen = {};
            var out = [];
            data.forEach(function (cat) {
                cat.productos.forEach(function (p) {
                    if (favOnly && !isFavorito(p.id)) {
                        return;
                    }
                    if (out.length >= limit) {
                        return;
                    }
                    var n = norm(p.nombre);
                    if (n.indexOf(qn) !== -1 && !seen["p" + p.id]) {
                        seen["p" + p.id] = 1;
                        out.push({ tipo: "producto", label: p.nombre, id: p.id });
                    }
                    p.variantes.forEach(function (v) {
                        if (favOnly && !isFavorito(p.id)) {
                            return;
                        }
                        if (out.length >= limit) {
                            return;
                        }
                        var sku = v.sku;
                        if (norm(sku).indexOf(qn) !== -1 && !seen["s" + sku]) {
                            seen["s" + sku] = 1;
                            out.push({ tipo: "sku", label: sku + " · " + p.nombre, id: p.id });
                        }
                    });
                });
            });
            return out.slice(0, limit);
        }

        function fmtFechaIso(iso) {
            if (!iso) {
                return "";
            }
            var parts = String(iso).split("-");
            if (parts.length === 3) {
                return parts[2] + "/" + parts[1] + "/" + parts[0];
            }
            return iso;
        }

        function buildVariantesTable(variantes) {
            if (!variantes.length) {
                return '<p class="text-warning small mb-0">Producto sin variantes registradas.</p>';
            }
            var thead =
                "<thead><tr><th>Variante</th><th>SKU</th><th>Talla</th><th>Meses</th><th>Color</th><th>Precio</th><th>Stock</th><th>Estado</th><th>Acción</th></tr></thead>";
            var rows = variantes
                .map(function (v) {
                    var agotado = v.agotado === true || v.stock === 0;
                    var rep =
                        v.fecha_reposicion && agotado
                            ? '<div class="small text-muted mt-1">Reposición: ' +
                              esc(fmtFechaIso(v.fecha_reposicion)) +
                              "</div>"
                            : "";
                    var estado = agotado
                        ? '<span class="badge text-bg-secondary">Agotado</span>' + rep
                        : '<span class="badge text-bg-success">Disponible</span>';
                    var btn =
                        agotado
                            ? '<button type="button" class="btn btn-sm btn-outline-secondary" disabled>Sin stock</button>'
                            : '<button type="button" class="btn btn-sm btn-outline-primary catalogo-add-cart" data-variante-id="' +
                              esc(String(v.id)) +
                              '">Añadir</button> ' +
                              '<button type="button" class="btn btn-sm btn-baby-pink catalogo-buy-now" data-variante-id="' +
                              esc(String(v.id)) +
                              '">Comprar ahora</button>';
                    return (
                        "<tr><td>#" +
                        esc(String(v.id)) +
                        "</td><td><code>" +
                        esc(v.sku) +
                        "</code></td><td>" +
                        esc(v.talla) +
                        "</td><td>" +
                        esc(String(v.meses_min)) +
                        "–" +
                        esc(String(v.meses_max)) +
                        "</td><td>" +
                        esc(v.color) +
                        "</td><td>$" +
                        esc(v.precio) +
                        "</td><td>" +
                        esc(String(v.stock)) +
                        "</td><td>" +
                        estado +
                        "</td><td>" +
                        btn +
                        "</td></tr>"
                    );
                })
                .join("");
            return (
                '<div class="table-responsive"><table class="table table-sm table-bordered table-variants">' +
                thead +
                "<tbody>" +
                rows +
                "</tbody></table></div>"
            );
        }

        function renderProductoCard(p, favorito) {
            var img = p.imagen_url
                ? '<img src="' +
                  esc(p.imagen_url) +
                  '" alt="" class="producto-img" loading="lazy" width="280" height="280">'
                : '<div class="producto-img-placeholder">Sin imagen</div>';
            var starClass = favorito ? " catalogo-fav-btn--on" : "";
            var aria = favorito ? "true" : "false";
            return (
                '<article class="producto-card producto-row" data-producto-id="' +
                esc(String(p.id)) +
                '">' +
                '<div class="producto-img-wrap">' +
                img +
                "</div>" +
                '<div class="producto-body">' +
                '<div class="producto-title-row">' +
                "<h3>" +
                esc(p.nombre) +
                "</h3>" +
                '<button type="button" class="catalogo-fav-btn' +
                starClass +
                '" data-fav-producto="' +
                esc(String(p.id)) +
                '" aria-label="Marcar favorito" aria-pressed="' +
                aria +
                '" title="Favorito">★</button>' +
                "</div>" +
                '<p class="producto-meta mb-2"><strong>Material:</strong> ' +
                esc(p.material) +
                "</p>" +
                buildVariantesTable(p.variantes) +
                "</div></article>"
            );
        }

        function agruparPorCategoria(items) {
            var sections = [];
            var lastId = null;
            items.forEach(function (item) {
                var cid = item.cat.id;
                if (cid !== lastId) {
                    lastId = cid;
                    sections.push({ cat: item.cat, productos: [] });
                }
                sections[sections.length - 1].productos.push(item.p);
            });
            return sections;
        }

        var dataEl = document.getElementById("catalogo-data");
        var mount = document.getElementById("catalogo-mount");
        var pagWrap = document.getElementById("catalogo-paginacion-wrap");
        var sinRes = document.getElementById("catalogo-sin-resultados");
        var input = document.getElementById("catalogo-busqueda");
        var autoBox = document.getElementById("catalogo-autocomplete");
        var filtroToggle = document.getElementById("catalogo-filtro-toggle");
        var filtroPanel = document.getElementById("catalogo-filtro-panel");
        var filtroCats = document.getElementById("catalogo-filtro-categorias");
        var soloFav = document.getElementById("catalogo-solo-favoritos");
        var soloDisp = document.getElementById("catalogo-solo-disponibles");
        var soloAgo = document.getElementById("catalogo-solo-agotados");
        var yearEl = document.getElementById("footer-year");
        var carritoAddUrl = "/carrito/add/";
        var carritoBadge = document.getElementById("nav-carrito-badge");

        function postForm(url, data) {
            var form = new FormData();
            Object.keys(data || {}).forEach(function (k) {
                form.append(k, data[k]);
            });
            try {
                var cfgEl = document.getElementById("catalogo-config");
                var cfg = cfgEl ? JSON.parse(cfgEl.textContent || "{}") : {};
                var csrf = cfg.csrf || "";
                if (csrf) form.append("csrfmiddlewaretoken", csrf);
            } catch (e) {}
            return fetch(url, { method: "POST", body: form, credentials: "same-origin" });
        }

        function updateCartBadge(count) {
            if (!carritoBadge) return;
            var n = Number(count || 0);
            if (!n || n <= 0) {
                carritoBadge.textContent = "0";
                carritoBadge.classList.add("d-none");
                return;
            }
            carritoBadge.textContent = String(n);
            carritoBadge.classList.remove("d-none");
        }

        var currentPage = 1;
        var pageSize = 6;
        if (mount && mount.getAttribute("data-products-per-page")) {
            pageSize = Math.max(1, parseInt(mount.getAttribute("data-products-per-page"), 10) || 6);
        }

        if (yearEl) {
            yearEl.textContent = String(new Date().getFullYear());
        }
        if (!dataEl || !mount) {
            return;
        }

        var data = JSON.parse(dataEl.textContent);
        var selectedCats = {};
        data.forEach(function (c) {
            selectedCats[String(c.id)] = true;
        });

        function buildFiltroCheckboxes() {
            if (!filtroCats) {
                return;
            }
            filtroCats.innerHTML = "";
            data.forEach(function (c) {
                var col = document.createElement("div");
                col.className = "col-6 col-md-4 col-lg-3";
                var id = "cat-filter-" + c.id;
                col.innerHTML =
                    '<div class="form-check catalogo-cat-box">' +
                    '<input class="form-check-input" type="checkbox" id="' +
                    id +
                    '" data-cat-id="' +
                    c.id +
                    '" checked>' +
                    '<label class="form-check-label" for="' +
                    id +
                    '">' +
                    esc(c.nombre) +
                    "</label></div>";
                filtroCats.appendChild(col);
            });
            filtroCats.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
                cb.addEventListener("change", function () {
                    selectedCats[cb.getAttribute("data-cat-id")] = cb.checked;
                    render();
                });
            });
        }

        function alMenosUnaCategoriaVisible() {
            for (var k in selectedCats) {
                if (selectedCats[k]) {
                    return true;
                }
            }
            return false;
        }

        function collectVisibleFlat() {
            var q = input && input.value ? input.value.trim() : "";
            var qn = norm(q);
            var favOnly = soloFav && soloFav.checked;
            var soloDisponibles = soloDisp && soloDisp.checked;
            var soloAgotados = soloAgo && soloAgo.checked;
            var out = [];
            if (!alMenosUnaCategoriaVisible()) {
                return out;
            }
            data.forEach(function (cat) {
                if (!selectedCats[String(cat.id)]) {
                    return;
                }
                cat.productos.forEach(function (p) {
                    if (!productoCoincideQuery(p, qn)) {
                        return;
                    }
                    if (favOnly && !isFavorito(p.id)) {
                        return;
                    }
                    if (soloDisponibles && !productoTieneStock(p)) {
                        return;
                    }
                    if (soloAgotados && !productoTodoAgotado(p)) {
                        return;
                    }
                    out.push({ cat: cat, p: p });
                });
            });
            return out;
        }

        function renderPagination(total, totalPages) {
            if (!pagWrap) {
                return;
            }
            if (totalPages <= 1) {
                pagWrap.classList.add("d-none");
                pagWrap.innerHTML = "";
                return;
            }
            pagWrap.classList.remove("d-none");
            var html =
                '<ul class="pagination justify-content-center flex-wrap mb-0"><li class="page-item disabled"><span class="page-link bg-transparent border-0 text-muted pe-3">Página</span></li>';
            var p;
            for (p = 1; p <= totalPages; p += 1) {
                html +=
                    '<li class="page-item' +
                    (p === currentPage ? " active" : "") +
                    '"><button type="button" class="page-link" data-page="' +
                    p +
                    '">' +
                    p +
                    "</button></li>";
            }
            html += "</ul>";
            pagWrap.innerHTML = html;
            pagWrap.querySelectorAll("[data-page]").forEach(function (btn) {
                btn.addEventListener("click", function () {
                    currentPage = parseInt(btn.getAttribute("data-page"), 10);
                    render({ keepPage: true });
                });
            });
        }

        function bindFavButtons() {
            mount.querySelectorAll(".catalogo-fav-btn").forEach(function (btn) {
                btn.addEventListener("click", function () {
                    var pid = btn.getAttribute("data-fav-producto");
                    toggleFavoritoAsync(pid).then(function (on) {
                        btn.classList.toggle("catalogo-fav-btn--on", on);
                        btn.setAttribute("aria-pressed", on ? "true" : "false");
                        if (soloFav && soloFav.checked) {
                            render();
                        }
                    });
                });
            });
        }

        function render(opts) {
            opts = opts || {};
            if (!opts.keepPage) {
                currentPage = 1;
            }

            var flat = collectVisibleFlat();
            var total = flat.length;
            var totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);

            if (!alMenosUnaCategoriaVisible()) {
                mount.innerHTML = "";
                if (pagWrap) {
                    pagWrap.classList.add("d-none");
                }
                if (sinRes) {
                    sinRes.classList.remove("d-none");
                    sinRes.textContent =
                        "Selecciona al menos un tipo de producto o vuelve a marcar las categorías.";
                }
                return;
            }

            if (totalPages > 0 && currentPage > totalPages) {
                currentPage = totalPages;
            }
            if (totalPages === 0) {
                currentPage = 1;
            }

            var start = (currentPage - 1) * pageSize;
            var slice = flat.slice(start, start + pageSize);
            var grouped = agruparPorCategoria(slice);

            var html = "";
            grouped.forEach(function (sec) {
                html +=
                    '<section class="categoria-block" id="cat-' +
                    esc(String(sec.cat.id)) +
                    '">' +
                    "<h2>" +
                    esc(sec.cat.nombre) +
                    "</h2>";
                if (sec.cat.descripcion) {
                    html +=
                        '<p class="text-muted small mb-3">' + esc(sec.cat.descripcion) + "</p>";
                }
                sec.productos.forEach(function (p) {
                    html += renderProductoCard(p, isFavorito(p.id));
                });
                html += "</section>";
            });

            mount.innerHTML = html;

            if (sinRes) {
                if (total === 0) {
                    sinRes.classList.remove("d-none");
                    sinRes.textContent =
                        "No hay productos que coincidan con tu búsqueda, favoritos o filtros.";
                } else {
                    sinRes.classList.add("d-none");
                }
            }

            renderPagination(total, totalPages);
            bindFavButtons();

            // wire carrito buttons
            if (mount) {
                mount.querySelectorAll(".catalogo-add-cart").forEach(function (b) {
                    b.addEventListener("click", function () {
                        var vid = b.getAttribute("data-variante-id");
                        postForm(carritoAddUrl, { variante_id: vid, cantidad: 1 })
                            .then(function (r) { return r && r.json ? r.json() : null; })
                            .then(function (data) {
                                if (data && data.ok) updateCartBadge(data.count);
                            })
                            .catch(function () {});
                    });
                });
                mount.querySelectorAll(".catalogo-buy-now").forEach(function (b) {
                    b.addEventListener("click", function () {
                        var vid = b.getAttribute("data-variante-id");
                        postForm(carritoAddUrl, { variante_id: vid, cantidad: 1 })
                            .then(function (r) { return r && r.json ? r.json() : null; })
                            .then(function (data) {
                                if (data && data.ok) updateCartBadge(data.count);
                                window.location.href = "/carrito/checkout/";
                            })
                            .catch(function () {});
                    });
                });
            }
        }

        var debounceTimer;
        function scheduleRender() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                render();
            }, DEBOUNCE_MS);
        }

        var debounceBusquedaLog;
        function scheduleBusquedaLog(val) {
            clearTimeout(debounceBusquedaLog);
            debounceBusquedaLog = setTimeout(function () {
                maybeLogBusqueda(val);
            }, BUSQUEDA_LOG_DEBOUNCE_MS);
        }

        function updateAutocomplete() {
            var q = input && input.value ? input.value.trim() : "";
            var qn = norm(q);
            var favOnly = soloFav && soloFav.checked;
            if (!autoBox) {
                return;
            }
            if (qn.length < 1) {
                autoBox.classList.add("d-none");
                autoBox.innerHTML = "";
                return;
            }
            var sug = sugerenciasAutocomplete(data, qn, 8, favOnly);
            if (!sug.length) {
                autoBox.classList.add("d-none");
                autoBox.innerHTML = "";
                return;
            }
            autoBox.innerHTML = sug
                .map(function (s, idx) {
                    return (
                        '<button type="button" class="catalogo-autocomplete-item" role="option" data-idx="' +
                        idx +
                        '">' +
                        esc(s.label) +
                        "</button>"
                    );
                })
                .join("");
            autoBox.classList.remove("d-none");
            autoBox.querySelectorAll(".catalogo-autocomplete-item").forEach(function (btn, idx) {
                btn.addEventListener("mousedown", function (e) {
                    e.preventDefault();
                    input.value =
                        sug[idx].tipo === "sku"
                            ? sug[idx].label.split(" · ")[0]
                            : sug[idx].label;
                    autoBox.classList.add("d-none");
                    render();
                });
            });
        }

        var debounceAuto;
        if (input) {
            input.addEventListener("input", function () {
                var v = input.value || "";
                scheduleRender();
                scheduleBusquedaLog(v);
                clearTimeout(debounceAuto);
                debounceAuto = setTimeout(updateAutocomplete, 120);
            });
            input.addEventListener("focus", function () {
                updateAutocomplete();
            });
            input.addEventListener("blur", function () {
                setTimeout(function () {
                    if (autoBox) {
                        autoBox.classList.add("d-none");
                    }
                }, 200);
            });
        }

        document.addEventListener("click", function (e) {
            if (autoBox && input && !autoBox.contains(e.target) && e.target !== input) {
                autoBox.classList.add("d-none");
            }
        });

        if (filtroToggle && filtroPanel) {
            filtroToggle.addEventListener("click", function () {
                filtroPanel.classList.toggle("d-none");
                var visible = !filtroPanel.classList.contains("d-none");
                filtroToggle.setAttribute("aria-expanded", visible ? "true" : "false");
            });
        }

        if (soloFav) {
            soloFav.addEventListener("change", function () {
                currentPage = 1;
                render();
                updateAutocomplete();
            });
        }

        if (soloDisp && soloAgo) {
            soloDisp.addEventListener("change", function () {
                if (soloDisp.checked) {
                    soloAgo.checked = false;
                }
                currentPage = 1;
                render();
            });
            soloAgo.addEventListener("change", function () {
                if (soloAgo.checked) {
                    soloDisp.checked = false;
                }
                currentPage = 1;
                render();
            });
        }

        buildFiltroCheckboxes();
        render();
    }

    document.addEventListener("DOMContentLoaded", initCatalogo);
})();
