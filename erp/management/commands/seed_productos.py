"""
Carga demo: categorías Poleras / Pantalones, polera U. de Chile y pantalón buzo rojo.
Imágenes: URLs públicas (referencia visual para la vitrina).

Uso: python manage.py seed_productos
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from erp.models import Categoria, Producto, Variante

IMG_POLERA = (
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRtWBTDf0huUqXWJFYnvEbGbS0dk5Ikl9qwpw&s"
)
IMG_PANT = (
    "https://pillin.vtexassets.com/arquivos/ids/360791-800-450"
    "?v=638295177554500000&width=800&height=450&aspect=true"
)


class Command(BaseCommand):
    help = "Inserta categorías y productos demo (polera U.CH., pantalón rojo) con variantes."

    def handle(self, *args, **options):
        poleras, _ = Categoria.objects.get_or_create(
            nombre="Poleras",
            defaults={"descripcion": "Poleras y bodies para bebé."},
        )
        pantalones, _ = Categoria.objects.get_or_create(
            nombre="Pantalones",
            defaults={"descripcion": "Pantalones y buzos inferiores."},
        )

        polera, _ = Producto.objects.update_or_create(
            nombre="Polera Bebé Universidad de Chile — JugaBet",
            defaults={
                "material": "Algodón / mezcla deportiva",
                "imagen_url": IMG_POLERA,
                "categoria": poleras,
            },
        )
        for sku, talla, mn, mx, precio in [
            ("POL-UCH-AZUL-03M", "0-3M", 0, 3, "17990"),
            ("POL-UCH-AZUL-36M", "3-6M", 3, 6, "18990"),
            ("POL-UCH-AZUL-612M", "6-12M", 6, 12, "19990"),
        ]:
            Variante.objects.update_or_create(
                sku_unico=sku,
                defaults={
                    "producto": polera,
                    "talla_etiqueta": talla,
                    "meses_min": mn,
                    "meses_max": mx,
                    "color": "Azul",
                    "precio_unitario": Decimal(precio),
                    "stock": 12,
                },
            )

        pant, _ = Producto.objects.update_or_create(
            nombre="Pantalón buzo básico bebé",
            defaults={
                "material": "100% algodón frisa",
                "imagen_url": IMG_PANT,
                "categoria": pantalones,
            },
        )
        for sku, talla, mn, mx, precio in [
            ("PANT-ROJO-03M", "0-3M", 0, 3, "10990"),
            ("PANT-ROJO-36M", "3-6M", 3, 6, "11990"),
            ("PANT-ROJO-612M", "6-12M", 6, 12, "12990"),
        ]:
            Variante.objects.update_or_create(
                sku_unico=sku,
                defaults={
                    "producto": pant,
                    "talla_etiqueta": talla,
                    "meses_min": mn,
                    "meses_max": mx,
                    "color": "Rojo",
                    "precio_unitario": Decimal(precio),
                    "stock": 15,
                },
            )

        self.stdout.write(self.style.SUCCESS("OK: categorías, 2 productos y 6 variantes listos."))
