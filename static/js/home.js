/**
 * home.js — Comportamiento ligero de la página de bienvenida.
 * Se enlaza desde: templates/home.html → {% static 'js/home.js' %}
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var yearEl = document.getElementById("footer-year");
        if (yearEl) {
            yearEl.textContent = String(new Date().getFullYear());
        }
    });
})();
