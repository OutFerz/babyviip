# Instrucciones de documentación y contexto Babyviip

## Normas de desarrollo (resumen)

- Documenta en comentarios cuando añadas lógica en **HTML**, **CSS**, **JS** o **Python**, e indica **de qué carpeta/archivo se llama** a otro recurso.
- Las páginas deben tener **su CSS**, **su JS** y **su HTML** separados; evita meter todo el estilo o script en un solo archivo de plantilla.
- El contenido debe mantenerse alineado con la **empresa Babyviip** (ropa y accesorios para bebés 0–3 años, local + nube, integración con redes).
- Los cambios relevantes del portal se registran en **`Intrucciones_text/cambios.md`**.

## Portal de entrada (visitante sin sesión)

Objetivo: quien entra **sin iniciar sesión** ve primero la identidad de la marca, el mensaje de evolución hacia catálogo/e-commerce y **datos de contacto visibles** (redes, teléfono, dirección, mapa), coherentes con los informes de evaluación.

### Referencias y datos del local (visibles en la web y citas APA)

- **Instagram:** Babyviip [@babyviipcl]. (s.f.). [Perfil de Instagram]. Instagram. Recuperado el 13 de abril de 2026, de https://www.instagram.com/babyviipcl/
- **Facebook:** Babyviip. (s.f.). [Página de Facebook]. Facebook. Recuperado el 13 de abril de 2026, de https://www.facebook.com/groups/1362338867173654/user/61587245798428/
- **Datos del local:** Dirección: Gran Avenida 5234, local 17 (Babyviip, s.f.). Mapa: https://share.google/C6HMTq54TXQDafIMq · Teléfono de contacto: 927493733 (Babyviip, s.f.).

Correo y WhatsApp usados en el proyecto (informes de la empresa): **babyviip8@gmail.com**, **+56 9 2749 3733**.

## Relación con la base de datos (ERP)

La app `erp` define el modelo que en el futuro alimentará el catálogo y las ventas. Para un **visitante sin cuenta**, la página explica de forma breve qué habrá detrás:

| Área | Modelos (tablas) | Rol frente al usuario final |
|------|------------------|-----------------------------|
| Autenticación | `Usuario` (`AbstractUser`) | Quién inicia sesión; roles `es_cliente`, `es_administrador_tienda`, `is_staff`. |
| Inventario | `Categoria`, `Producto`, `Variante` | Catálogo público; `Producto.imagen` (archivo) o `Producto.imagen_url`; `Variante.visible`, `fecha_reposicion`. |
| Comportamiento | `Favorito` (usuario = `AUTH_USER_MODEL` + producto), `Busqueda` (término, usuario opcional, `ip`, `user_agent` opcionales) | Rankings en el dashboard; favoritos ⭐ con sesión; búsquedas con contexto para análisis. |
| Cliente / ventas | `Cliente` (opcional `usuario`), `Venta`, `DetalleVenta` | Datos de compra; la vista `/ventas/` solo para staff o admin de tienda. |

El **administrador Django** (`/admin/`) solo se enlaza si `user.is_staff`. Registro y login: `/accounts/registro/`, `/accounts/login/`.

## Mapa de archivos del portal de entrada

| Origen | Destino / uso |
|--------|----------------|
| `core/views.py` | Vistas `home`, `catalogo`, `ventas_clientes` (ventas restringida). |
| `erp/auth_views.py` | `registro`, login, logout. |
| `erp/forms.py` | `RegistroUsuarioForm`, `BabyviipAuthenticationForm`. |
| `core/context_processors.py` | `contacto`: **Configuración del sitio desde BD** (redes, teléfono, correo, dirección, mapa, WhatsApp) para todas las plantillas. |
| `templates/partials/site_nav.html` | Pestañas; **Ventas** solo si staff o `es_administrador_tienda`. |
| `templates/partials/flash_messages.html` | Mensajes (permisos, etc.). |
| `templates/auth/login.html`, `registro.html` | Autenticación. |
| `templates/home.html` | Bienvenida + contacto + citas APA (sin título “Referencias APA”). |
| `templates/catalogo.html` | Listado ERP: categorías, productos, variantes (tablas). |
| `templates/ventas.html` | Listado de ventas con acordeón de `DetalleVenta` (últimas 100). |
| `static/css/site_nav.css` | Estilos de cabecera y pestañas compartidas. |
| `static/css/home.css` | Estilos de la bienvenida. |
| `static/css/catalogo.css` | Estilos del catálogo. |
| `static/css/ventas.css` | Estilos de ventas. |
| `static/css/auth_login.css`, `auth_registro.css` | Login y registro. |
| `static/js/home.js`, `catalogo.js`, `ventas.js`, `auth_*.js` | Scripts por página. |
| `erp/management/commands/seed_productos.py` | Carga demo de productos. |
| `core/settings.py` | `AUTH_USER_MODEL`, `LOGIN_URL`, `STATICFILES_DIRS`, `contacto`. |

**URLs:** `/` inicio · `/catalogo/` catálogo · `/ventas/` ventas (restringido) · `/accounts/login/`, `/accounts/registro/`.

## Panel de catálogo (`/panel/`) y alineación con los informes

El panel web complementa el **administrador Django** (`/admin/`). La entrada **`/panel/`** muestra un **resumen (dashboard)** con KPIs (productos, categorías, stock bajo, variantes agotadas), gráficos (Chart.js), ventas recientes, rankings de **más vendidos** (`DetalleVenta`), **más favoritos** (`Favorito`) y **términos más buscados** (`Busqueda`). Las secciones **Productos** y **Categorías** mantienen el CRUD; el flag **`Producto.publicado`** oculta todo el ítem en la vitrina, mientras que por **variante** se controlan **`visible`**, **`stock`** (agotado si es 0) y **`fecha_reposicion`** para el mensaje al cliente.

- **Innovación y Emprendimiento II:** el informe señala brechas por gestión manual de inventario y precios; un único registro en el ERP + visibilidad controlada en catálogo responde a esa necesidad de integración y precisión.
- **Arquitectura Multi Cloud:** la propuesta plantea catálogos e inventario disponibles de forma centralizada “en la nube”; este proyecto materializa esa idea en un **servicio web** (desplegable en contenedor / nube) como **corazón digital** operativo, previo o paralelo a una futura tienda completa en Azure u otro proveedor.

**Archivos del panel:** `erp/panel_views.py`, `erp/panel_urls.py`, `erp/panel_forms.py`, `templates/panel/*`, `static/css/panel.css`, `static/js/panel.js`.

**API catálogo (estadísticas y favoritos en cuenta):** `POST /api/catalogo/favorito/` (JSON, usuario autenticado), `POST /api/catalogo/busqueda/` (form `termino`, CSRF). Implementación: `erp/catalog_api.py`. Umbral de stock bajo en panel: `STOCK_BAJO_UMBRAL` en `core/settings.py` (env `STOCK_BAJO_UMBRAL`, por defecto 5).

**Archivos subidos:** `MEDIA_ROOT` / `media/` (productos); en desarrollo (`DEBUG`) Django sirve `/media/`. **Exportaciones del resumen:** `GET /panel/exportar/<csv|xlsx|pdf|html>/` (informe completo). **Por gráfico:** `GET /panel/exportar/grafico/<kpis|vendidos|favoritos>/<formato>/` (mismos datos que Chart.js: CSV, Excel, PDF, HTML + PNG desde el menú). **Por tabla:** `GET /panel/exportar/tabla/<busquedas|ventas|ranking_vendidos|ranking_favoritos>/<formato>/`. Implementación: `erp/dashboard_export.py`.

| Origen | Uso |
|--------|-----|
| `templates/panel/base.html` | Cabecera: Resumen, Productos, Categorías, **Configuración**. |
| `templates/panel/dashboard.html` | Dashboard con KPIs y gráficos. |
| `templates/panel/configuracion_form.html` | Formulario `/panel/configuracion/` para editar contacto/redes/local. |
| `static/css/panel.css` | Estética Babyviip (celeste / rosa), tablas, KPIs, bloques de gráfico. |
| `static/js/catalogo.js` | Favoritos locales o servidor; registro de búsquedas; filtros “solo con stock” / “solo agotados”. |

## Configuración del sitio (sin HTML fijo)

Para que Instagram/Facebook/teléfono/correo/dirección se puedan cambiar **sin editar código**, se creó el modelo
`erp.models.ConfiguracionSitio` (un solo registro) y una pantalla en el panel:

- `GET/POST /panel/configuracion/`: edita **Contacto, redes y local** (Instagram, Facebook, teléfono, correo, dirección, mapa y WhatsApp).
- El `context_processor` `core.context_processors.contacto` lee desde la base de datos y entrega el dict `contacto` a `templates/home.html`.

## Pasos en tu máquina (Docker)

```bash
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_productos
docker compose exec web python manage.py createsuperuser
```
