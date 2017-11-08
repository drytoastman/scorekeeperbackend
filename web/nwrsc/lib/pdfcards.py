from flask import make_response
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def pdfcards(page, event, registered):
    """ Legacy PDF printing """
    if page == 'letter': # Letter has an additional 72 points Y to space out
        size = (8*inch, 11*inch)
    else:
        size = (8*inch, 5*inch)

    if page == 'letter' and len(registered)%2 != 0:
        registered.append(None) # Pages are always two cards per so make it divisible by 2

    buf = io.BytesIO()
    mycanvas = canvas.Canvas(buf, pagesize=size, pageCompression=1)
    while len(registered) > 0:
        if page == 'letter':
            mycanvas.translate(0, 18)  # 72/4, bottom margin for letter page
            drawCard(mycanvas, event, registered.pop(0))
            mycanvas.translate(0, 396)  # 360+72/2 card size plus 2 middle margins
            drawCard(mycanvas, event, registered.pop(0))
        else:
            drawCard(mycanvas, event, registered.pop(0))
        mycanvas.showPage()
    mycanvas.save()

    response = make_response(buf.getvalue())
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = 'attachment;filename=cards.pdf'
    return response


# 8inch = 576points, half = 288
# 5inch = 360points, half = 180
MIDDLE = 288

def stringLimit(c, txt, font, size, limit):
    if not txt:
        return ""
    w = c.stringWidth(txt, font, size)
    while w > limit:
        txt = txt[:-1]
        w = c.stringWidth(txt, font, size)
    return txt

def timerow(c, y, height):
    c.rect(MIDDLE-270,y, 220, height)
    c.rect(MIDDLE-50, y, 50,  height)
    c.rect(MIDDLE,    y, 50,  height)
    c.rect(MIDDLE+50, y, 220, height)

def row22(c, y, height):
    c.rect(MIDDLE-270, y, 270, height)
    c.rect(MIDDLE,     y, 270, height)

def row21(c, y, height):
    c.rect(MIDDLE-270, y, 270, height)
    c.rect(MIDDLE,     y, 135, height)

def row211(c, y, height):
    c.rect(MIDDLE-270, y, 270, height)
    c.rect(MIDDLE,     y, 135, height)
    c.rect(MIDDLE+135, y, 135, height)

def drawCard(c, event, entrant, **kwargs):

    # Draw all the boxes
    c.setLineWidth(0.5)

    y = 20
    timerow(c, y, 23); y += 23
    timerow(c, y, 23); y += 23
    timerow(c, y, 23); y += 23
    timerow(c, y, 23); y += 23
    timerow(c, y, 23); y += 23
    timerow(c, y, 23); y += 23

    timerow(c, y, 15); y += 21

    row22(c, y, 21); y+= 21
    row211(c, y, 21); y+= 21
    row211(c, y, 21); y+= 21
    row211(c, y, 21); y+= 21
    row211(c, y, 21); y+= 21
    row211(c, y, 21); y+= 21
    

    # Draw Labels
    c.setFont('Helvetica-Bold', 10)
    x = 67
    y = 187
    c.drawRightString(x, y, "Sponsor:"); y += 21
    c.drawRightString(x, y, "Email:"); y += 21
    c.drawRightString(x, y, "Phone:"); y += 21
    c.drawRightString(x, y, "CSZ:"); y += 21
    c.drawRightString(x, y, "Address:"); y += 21
    c.drawRightString(x, y, "Name:"); y += 21

    x = 332
    y = 187
    c.drawRightString(x, y, "Brag:"); y += 21
    c.drawRightString(x, y, "SCCA #:"); y += 21
    c.drawRightString(x, y, "Color:"); y += 21
    c.drawRightString(x, y, "Model:"); y += 21
    c.drawRightString(x, y, "Make:"); y += 21
    c.drawRightString(x, y, "Year:"); y += 21

    x = 487
    # y = 187 + (4*21)
    y = 208
    c.drawRightString(x, y, "Teched By:"); y += 21
    c.drawRightString(x, y, "Assignment:"); y += 21
    c.drawRightString(x, y, "Run/Work:"); y += 21
    c.drawRightString(x, y, "Number:"); y += 21
    c.drawRightString(x, y, "Class(IDX):"); y += 21

    x = 152
    y = 162
    c.drawRightString(x, y, "Raw Time"); x += 126
    c.drawRightString(x, y, "Cones"); x += 48
    c.drawRightString(x, y, "Gates"); x += 148
    c.drawRightString(x, y, "Official Time"); x += 20
    
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(MIDDLE, 337, "%s" % (event.name))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(MIDDLE, 320, event.date.strftime("%B %d, %Y"))
    #c.setFont('Helvetica-Bold', 12)
    #c.drawAlignedString(MIDDLE, 313, "Sponsored by: {}".format(event.attr.get('sponsor', '')), ':')
    if entrant is None:
        return

    c.setFont('Courier', 10)
    x = 70
    y = 187
    c.drawString(x, y, stringLimit(c, entrant.sponsor, 'Courier', 10, 200) or ""); y += 21
    c.drawString(x, y, entrant.email); y += 21
    c.drawString(x, y, entrant.phone); y += 21
    c.drawString(x, y, "%s, %s %s" % (entrant.city, entrant.state, entrant.zip)); y += 21
    c.drawString(x, y, entrant.address); y += 21
    c.drawString(x, y, "%s %s" % (entrant.firstname, entrant.lastname)); y += 21

    x = 337
    y = 187
    c.drawString(x, y, stringLimit(c, entrant.brag,  'Courier', 10, 200)); y += 21
    c.drawString(x, y, entrant.membership or ""); y += 21
    c.drawString(x, y, stringLimit(c, entrant.color, 'Courier', 10, 85)); y += 21
    c.drawString(x, y, stringLimit(c, entrant.model, 'Courier', 10, 85)); y += 21
    c.drawString(x, y, stringLimit(c, entrant.make,  'Courier', 10, 85)); y += 21
    c.drawString(x, y, stringLimit(c, entrant.year,  'Courier', 10, 85)); y += 21

    x = 490
    y = 187 + (4*21)
    c.drawString(x, y, str(entrant.number)); y += 21
    if entrant.indexcode:
        c.drawString(x, y, "%s(%s)" % (entrant.classcode, entrant.indexcode)); y += 21
    else:
        c.drawString(x, y, entrant.classcode); y += 21

    c.setFont('Courier', 20)
    c.drawRightString(558, 320, entrant.quickentry)

