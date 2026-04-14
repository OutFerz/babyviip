import csv
import html
from io import BytesIO, StringIO

from django.http import HttpResponse
from django.utils import timezone


def _stamp() -> str:
    return timezone.localdate().isoformat()


def _attach(response: HttpResponse, filename: str) -> HttpResponse:
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def export_auditoria_csv(qs):
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(["Babyviip — Auditoría (CSV)"])
    w.writerow(["Generado", timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M")])
    w.writerow([])
    w.writerow(
        ["Fecha", "Usuario", "Rol", "Acción", "Módulo", "Entidad", "Entidad ID", "Descripción", "IP"]
    )
    for a in qs:
        w.writerow(
            [
                timezone.localtime(a.creado_en).strftime("%Y-%m-%d %H:%M"),
                a.usuario.username if a.usuario else "",
                a.rol or "",
                a.accion,
                a.modulo or "",
                a.entidad or "",
                a.entidad_id or "",
                (a.descripcion or "").replace("\n", " ").strip(),
                a.ip or "",
            ]
        )
    response = HttpResponse("\ufeff" + buf.getvalue(), content_type="text/csv; charset=utf-8")
    return _attach(response, f"babyviip_auditoria_{_stamp()}.csv")


def export_auditoria_xlsx(qs):
    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse(
            "Falta openpyxl. pip install openpyxl",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoria"
    ws.append(["Babyviip — Auditoría"])
    ws.append(["Generado", timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M")])
    ws.append([])
    ws.append(
        ["Fecha", "Usuario", "Rol", "Acción", "Módulo", "Entidad", "Entidad ID", "Descripción", "IP"]
    )
    for a in qs:
        ws.append(
            [
                timezone.localtime(a.creado_en).replace(tzinfo=None),
                a.usuario.username if a.usuario else "",
                a.rol or "",
                a.accion,
                a.modulo or "",
                a.entidad or "",
                a.entidad_id or "",
                (a.descripcion or "").strip(),
                a.ip or "",
            ]
        )
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    response = HttpResponse(
        bio.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return _attach(response, f"babyviip_auditoria_{_stamp()}.xlsx")


def export_auditoria_pdf(qs):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except ImportError:
        return HttpResponse(
            "Falta reportlab. pip install reportlab",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, y, "Babyviip — Auditoría")
    y -= 0.6 * cm
    p.setFont("Helvetica", 9)
    p.drawString(
        2 * cm,
        y,
        f"Generado: {timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')}",
    )
    y -= 0.8 * cm
    p.setFont("Helvetica", 8)
    for a in qs:
        if y < 2 * cm:
            p.showPage()
            y = height - 2 * cm
            p.setFont("Helvetica", 8)
        who = a.usuario.username if a.usuario else "—"
        line = (
            f"{timezone.localtime(a.creado_en).strftime('%Y-%m-%d %H:%M')} | {who} | "
            f"{a.accion} | {a.modulo} | {a.entidad} {('#'+a.entidad_id) if a.entidad_id else ''} | "
            f"{(a.descripcion or '').strip()}"
        )
        p.drawString(2 * cm, y, line[:140])
        y -= 0.42 * cm
    p.save()
    pdf = buf.getvalue()
    buf.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    return _attach(response, f"babyviip_auditoria_{_stamp()}.pdf")


def export_auditoria_html(qs):
    gen = html.escape(timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M"))
    trs = "".join(
        "<tr>"
        f"<td>{html.escape(timezone.localtime(a.creado_en).strftime('%Y-%m-%d %H:%M'))}</td>"
        f"<td>{html.escape(a.usuario.username if a.usuario else '—')}</td>"
        f"<td>{html.escape(a.rol or '')}</td>"
        f"<td>{html.escape(a.accion)}</td>"
        f"<td>{html.escape(a.modulo or '')}</td>"
        f"<td>{html.escape(a.entidad or '')}</td>"
        f"<td>{html.escape(a.entidad_id or '')}</td>"
        f"<td>{html.escape((a.descripcion or '').strip())}</td>"
        f"<td>{html.escape(a.ip or '')}</td>"
        "</tr>"
        for a in qs
    )
    body = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Babyviip — Auditoría</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:1.5rem;color:#0f172a;}}
.card{{max-width:1100px;margin:0 auto;border:1px solid #e2e8f0;border-radius:14px;padding:1.25rem 1.25rem 1rem;}}
.brand{{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:baseline;}}
.brand h1{{margin:0;color:#0277bd;font-size:1.25rem;}}
.meta{{margin:0;color:#475569;font-size:.95rem;}}
table{{border-collapse:collapse;width:100%;margin-top:.75rem;font-size:.95rem;}}
th,td{{border:1px solid #e2e8f0;padding:8px 10px;text-align:left;vertical-align:top;}}
th{{background:#f8fafc;}}
footer{{margin-top:1rem;color:#64748b;font-size:.9rem;}}
</style></head><body>
<div class="card">
<div class="brand"><h1>Babyviip — Auditoría</h1><p class="meta">Generado: {gen}</p></div>
<table>
<tr><th>Fecha</th><th>Usuario</th><th>Rol</th><th>Acción</th><th>Módulo</th><th>Entidad</th><th>ID</th><th>Descripción</th><th>IP</th></tr>
{trs}
</table>
</div>
<footer>Exportado desde el panel operativo Babyviip.</footer>
</body></html>"""
    response = HttpResponse(body, content_type="text/html; charset=utf-8")
    return _attach(response, f"babyviip_auditoria_{_stamp()}.html")

