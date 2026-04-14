# Cambios — portal Babyviip

## Fecha: 13 de abril de 2026

### Portal de entrada (visitantes sin sesión)

- **Objetivo:** Mejorar la primera impresión del sitio alineada con los informes de *Arquitectura Multi Cloud* e *Innovación y Emprendimiento II*: marca, transición a tienda online, integración con Instagram/Facebook, datos del local y mapa, teléfono y correo de contacto.
- **Separación de capas:** Estilos por página (`static/css/...`) y scripts por página (`static/js/...`).
- **Backend:** `core/context_processors.contacto` aporta el diccionario `contacto` a todas las plantillas; las vistas `catalogo` y `ventas_clientes` consultan el ERP.
- **Referencias APA:** bloque al pie en `home.html` con las citas (sin encabezado “Referencias (APA) — enlaces oficiales”).
- **Navegación:** Pestañas Inicio / Catálogo (`templates/partials/site_nav.html`).

### Ampliación: catálogo y ventas

- **Rutas:** `GET /catalogo/` — tablas `Categoria`, `Producto`, `Variante`. `GET /ventas/` — resumen de ventas (últimas 100).
- **Campo `Producto.imagen_url`:** URL de foto para la vitrina.

- **Ventas y clientes (`/ventas/`)**:
  - **Propósito**: vista operativa para administración que evidencia el modelo `Venta` + `DetalleVenta` (variante, cantidad, precio histórico), útil para control interno y validación del ERP.
  - **Mejor práctica**: se mueve al panel como `GET /panel/ventas/` para evitar confusión con flujo de compra del cliente.
  - **Ruta legacy**: `GET /ventas/` redirige a `GET /panel/ventas/` si el usuario tiene permisos; si no, redirige a login/inicio.
  - **Permisos**: solo usuarios autenticados con rol **staff** o `es_administrador_tienda`.
  - **Simulaciones**: por defecto se excluyen (`es_simulacion=False`) para no contaminar análisis; se pueden incluir con `?sim=1`.
  - **Mejoras UI**: barra de búsqueda y filtros por estado + toggle de simulaciones.

---

## Usuario Django, registro y permisos (actualización)

- **`erp.Usuario`** extiende `AbstractUser` con `es_cliente` y `es_administrador_tienda`. Configuración: `AUTH_USER_MODEL = "erp.Usuario"` en `core/settings.py`.
- **`Cliente`:** `usuario` OneToOne opcional; RUT, nombre, email, contacto para facturación / compras.
- **Registro:** `erp.forms.RegistroUsuarioForm` + `erp.auth_views.registro` → crea `Usuario` + `Cliente` vinculado.
- **Login / logout:** `BabyviipLoginView`, `BabyviipLogoutView`; plantillas `templates/auth/login.html`, `templates/auth/registro.html` con CSS/JS propios (`auth_login.css`, `auth_registro.css`, etc.).
- **Ventas y clientes:** `@login_required` + comprobación `is_staff` o `es_administrador_tienda`; si no hay permiso, mensaje y redirect a inicio. La pestaña **Ventas y clientes** solo se muestra a quien tiene esos permisos. **Administración** (`/admin/`) solo visible si `user.is_staff`.
- **Semilla de productos:** `python manage.py seed_productos` (polera Universidad de Chile — JugaBet, pantalón buzo rojo, variantes por talla).
- **Migración inicial nueva:** si la base ya tenía el esquema viejo sin usuario personalizado, hace falta volumen limpio (`docker compose down -v`) y volver a `migrate`.

### Archivos relevantes

- `erp/models.py`, `erp/forms.py`, `erp/auth_views.py`, `erp/admin.py`, `erp/migrations/0001_initial.py`
- `erp/management/commands/seed_productos.py`
- `core/views.py`, `core/urls.py`, `core/settings.py`
- `templates/partials/site_nav.html`, `templates/partials/flash_messages.html`, `templates/auth/login.html`, `templates/auth/registro.html`
- `templates/catalogo.html`, `templates/home.html`
- `static/css/site_nav.css`, `catalogo.css`, `auth_login.css`, `auth_registro.css`
- `README.md`, `Intrucciones_text/cambios.md`

### Catálogo: búsqueda en vivo, filtros y favoritos

- Barra de búsqueda con lista de sugerencias (autocompletado) mientras se escribe; el listado principal se actualiza con debounce.
- Con **Solo favoritos** activo, las sugerencias también se limitan a favoritos.
- Botón **Filtrar por tipo** despliega recuadros (checkbox) por categoría; desmarcar oculta ese tipo.
- **Solo favoritos** filtra productos marcados con ♥; los favoritos se guardan en `localStorage` (`babyviip_favoritos`).
- **Paginación:** máximo de productos por pantalla configurable (`data-products-per-page` en `#catalogo-mount`, por defecto 6); navegación 1, 2, 3…
- El catálogo público solo incluye productos con **`publicado=True`** (vista `catalogo` filtra en `Prefetch`).

### Panel de catálogo (staff / `es_administrador_tienda`)

- Rutas bajo **`/panel/`**: **`/panel/`** = **dashboard** (KPIs, gráficos Chart.js, ventas recientes, rankings vendidos / favoritos / búsquedas, accesos a productos, categorías, ventas y clientes en admin). Listado y CRUD de productos y categorías; variantes en línea al editar (`VarianteFormSet`).
- **Modelos:** `Variante.visible`, `Variante.fecha_reposicion`, propiedad `esta_agotado`; `Favorito` (`AUTH_USER_MODEL`); `Busqueda` (+ `ip`, `user_agent` opcionales). Migraciones `0003_…`, `0004_busqueda_contexto_auth_user_swappable`.
- **Stock bajo (panel):** umbral `STOCK_BAJO_UMBRAL` en `core/settings.py` (variable de entorno homónima).
- **Ocultar en vitrina:** `Producto.publicado` (producto entero) o “Publicar/Ocultar” en el listado; por variante, **visible** y **stock** (agotado = 0) + fecha de reposición en catálogo público.
- **API:** `POST /api/catalogo/favorito/`, `POST /api/catalogo/busqueda/` (`erp/catalog_api.py`, búsqueda guarda IP y user-agent cuando son válidos). Catálogo: favoritos con cuenta o `localStorage`; registro de búsquedas con debounce. Filtros **Solo favoritos / Solo con stock / Solo agotados** van dentro del panel **Filtrar por tipo y disponibilidad**.
- **UI:** `static/css/panel.css`, `templates/panel/dashboard.html`, pestaña **Resumen** en `templates/panel/base.html`.
- Enlace **Panel catálogo** en la cabecera apunta al **resumen** (`panel_inicio`).

### Imagen de producto y exportación del panel

- **`Producto.imagen`:** `ImageField` (`media/productos/`) además de `imagen_url`; prioridad del archivo en catálogo (`url_imagen_para_catalogo`). Formulario con `enctype="multipart/form-data"`, vista previa con botón mostrar/ocultar (`static/js/panel.js`).
- **Dependencias:** `Pillow`, `openpyxl`, `reportlab` en `requirements.txt`. Migración `erp/migrations/0005_producto_imagen.py`.
- **Exportaciones (panel):**
  - **Informe completo:** `GET /panel/exportar/<csv|xlsx|pdf|html>/`.
  - **Por gráfico:** `GET /panel/exportar/grafico/<kpis|vendidos|favoritos>/<csv|xlsx|pdf|html>/` (y descarga PNG desde el botón del gráfico).
  - **Por tabla:** `GET /panel/exportar/tabla/<busquedas|ventas|ranking_vendidos|ranking_favoritos>/<csv|xlsx|pdf|html>/`.
  - Implementación: `erp/dashboard_export.py` + `erp/dashboard_context.py`.

### Configuración editable (Contacto, redes y local)

- Se eliminó la dependencia de datos fijos en `home.html` para Instagram/Facebook/teléfono/correo/dirección.
- **Nuevo modelo:** `erp.models.ConfiguracionSitio` (un solo registro).
- **Nuevo panel:** `GET/POST /panel/configuracion/` para actualizar datos de contacto/redes/local sin tocar código.
- **Contexto global:** `core.context_processors.contacto` ahora lee desde BD y expone `contacto.*` a las plantillas.

### Auditoría del sistema (trazabilidad)

- **Objetivo:** trazabilidad y control interno (quién cambió qué, cuándo y desde dónde), alineado con la gestión centralizada del panel.
- **Nuevo rol:** `Usuario.es_empleado` (acceso limitado).
- **Nuevo modelo:** `erp.models.Auditoria` (acciones: crear/editar/eliminar/login/logout/cambio_estado/exportar).
- **Permisos en auditoría:**
  - Admin/staff: ve **todo**.
  - Empleado: ve **solo sus acciones**.
- **Nueva pestaña:** `GET /panel/auditoria/` con buscador + filtros por acción, módulo, usuario (solo admin) y rango de fechas.
- **Descargas:** `GET /panel/auditoria/exportar/<csv|xlsx|pdf|html>/` (respeta filtros y permisos).
- **Registro automático:** señales login/logout + eventos del panel (CRUD catálogo, cambios de publicado, configuración del sitio y exportaciones).

### Simulador de compras (QA / capacitación / prueba de flujo)

- **Nuevo módulo en panel:** `GET/POST /panel/simulador/compra/` para simular compras con estados:
  - **Por comprar**, **Pendiente de pago**, **Comprado**, **Pago cancelado**.
- **Modos de simulación (arquitectura recomendada):**
  - `sin_impacto`: no crea venta ni descuenta stock (solo calcula total).
  - `temporal`: crea venta con `es_simulacion=True`, descuenta stock y permite **revertir** (reponer stock) → estado `revertida`.
  - `permanente`: crea venta real con `es_simulacion=False` (aparece en reportes) pero mantiene `modo_simulacion="permanente"`.
- **Revertir temporal:** `POST /panel/simulador/compra/<id>/revertir/` repone stock y registra el evento en auditoría.
- **Ventas / reportes:** por defecto se filtra con `Venta.objects.filter(es_simulacion=False)`; en `/ventas/` se puede incluir con `?sim=1`.

### Chat cliente ↔ admin (atención y seguimiento con trazabilidad)

- **Objetivo (Babyviip):** centralizar consultas por stock/tallas y seguimiento dentro del sistema (más ordenado que WhatsApp manual), con historial y control de responsables.
- **Modelos nuevos:** `erp.models.Conversacion`, `erp.models.Mensaje`.
  - `Conversacion`: `cliente`, `administrador_asignado`, `asunto`, `estado` (abierta/cerrada), timestamps.
  - `Mensaje`: `conversacion`, `emisor`, `contenido`, flags `leido_por_admin` / `leido_por_cliente`.
- **Cliente (web pública):**
  - `GET /mensajes/` lista “Mis mensajes”.
  - `GET/POST /mensajes/nueva/` crea conversación.
  - `GET/POST /mensajes/<id>/` ver y responder (solo conversaciones propias).
- **Admin/Panel:**
  - `GET /panel/mensajes/` bandeja con buscador + botón **Filtros** (estado, no leídas, asignación).
  - `GET/POST /panel/mensajes/<id>/` ver y responder.
  - `POST /panel/mensajes/<id>/asignar/` asignarme/desasignar (solo admin).
  - `POST /panel/mensajes/<id>/cerrar/` cerrar conversación.
- **UI:** colores/badges para lectura (no leído resaltado), cerrado atenuado, badges “Nuevo/Abierta/Cerrada”.
- **Auditoría:** se registran eventos clave (crear conversación/mensaje, cerrar, asignar) con `log_event` para trazabilidad interna.

### Carrito + checkout (flujo de compra ordenado)

- **Objetivo:** completar el flujo natural **Catálogo → Carrito → Finalizar compra (checkout)** para clientes, y preparar una base reutilizable para pruebas.
- **Carrito (sesión):** se guarda en `request.session` (clave `babyviip_cart`) por **variante**, no por producto.
- **Rutas:**
  - `GET /carrito/` ver carrito, editar cantidades, vaciar.
  - `POST /carrito/add/` (AJAX desde catálogo) añade una variante.
  - `POST /carrito/update/` actualizar cantidad (0 = quitar).
  - `POST /carrito/clear/` vaciar carrito.
  - `GET/POST /carrito/checkout/` finalizar compra (demo).
- **UI:** pestaña superior **Carrito** con badge `Carrito (n)` usando context processor global.
- **Catálogo:** botones por variante **Añadir** y **Comprar ahora** (este último añade y redirige a checkout).
- **Checkout (demo):**
  - Requiere login y `perfil_cliente`.
  - Valida stock y crea `Venta` + `DetalleVenta`; descuenta stock al confirmar.
  - Limpia el carrito y registra evento en auditoría.
