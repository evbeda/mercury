from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
from django.conf import settings
from .models import (
    Order,
    Merchandise,
)


def pdf_merchandise(order_id):
    temp = BytesIO()
    p = canvas.Canvas(temp, pagesize=A4)
    order = Order.objects.get(id=order_id)
    name_event = order.event.name
    rl_config.TTFSearchPath.append(
        str(settings.BASE_DIR) + '/mercury_app/static/font')
    pdfmetrics.registerFont(TTFont(
        'Roboto-BlackItalic',
        'Roboto-BlackItalic.ttf'
    ))
    pdfmetrics.registerFont(TTFont(
        'Roboto-Medium',
        'Roboto-Medium.ttf'
    ))
    pdfmetrics.registerFont(TTFont(
        'Roboto-Light',
        'Roboto-Light.ttf'
    ))

    p.setLineWidth(.3)
    p.setFont('Roboto-BlackItalic', 30)
    p.drawString(30, 750, 'Merchandise of ')

    p.setFont('Roboto-Medium', 15)
    p.drawString(30, 725, name_event)

    p.setFont('Roboto-Medium', 12)
    p.drawString(30, 690, order.name)

    p.drawString(30, 665, 'Order: ' + str(order.eb_order_id))

    merchandising = Merchandise.objects.filter(order=order_id)
    horizontal = 640
    total = 0
    for merchandise in merchandising:
        p.setFont('Roboto-Light', 10)
        p.drawString(30, horizontal - 15, 'Item:  ' + merchandise.name)
        p.drawString(30, horizontal - 30, 'Type:  ' + merchandise.item_type)
        p.drawString(30, horizontal - 45, 'Unit price:  ' + merchandise.value)
        p.drawString(30, horizontal - 60, 'Quantity:  ' + str(
            merchandise.quantity)
        )
        p.line(30, horizontal - 75, 550, horizontal - 75)
        total += float(merchandise.value)
        horizontal -= 90
    p.setFont('Roboto-Medium', 12)
    p.drawString(400, horizontal - 50, 'Merchandise total: ' + str(total))
    p.showPage()
    p.save()
    return temp.getvalue()
