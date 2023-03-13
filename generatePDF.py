import string
import random
import io
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.rl_config import defaultPageSize
from reportlab.lib.utils import simpleSplit
import database
import openai
import datetime
from pikepdf import Pdf, Page, Encryption
import uuid

openai.api_key = os.environ.get('OPENAI_API_KEY')
address = os.environ.get('API_URL')

def generate_token(email,redirect_address):
    # initializing size of string
    N = random.randrange(25, 32)

    # generating random string
    token = ''.join(random.choices(string.ascii_lowercase +
                                string.digits, k=N))
    
    database.add_token(token,email,redirect_address)
    return token

def update_url(token):
    path='templates/template.pdf'
    pdf = Pdf.open(path)
    Page(pdf.pages[0]).obj['/AA']['/O']['/URI'] = address + '/' + token
    pdf.save('/tmp/' +token + '.pdf')
    

def insert_text(token,context,title,subTitle, section):
   
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=context,
        temperature=0.7,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=2,
        presence_penalty=0
    )
    text = response["choices"][0]["text"]
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet)
    PAGE_WIDTH  = defaultPageSize[0]
    PAGE_HEIGHT = defaultPageSize[1]
    text_width = stringWidth(title,"Helvetica-Bold",28)
    
    can.setFillColorRGB(255,255,255)
    can.setFont("Helvetica-Bold",28)
    can.drawString((PAGE_WIDTH - text_width) / 2.0, 745, title)
    can.setFont("Helvetica-Oblique",22)
    text_width = stringWidth(subTitle,"Helvetica-Oblique",22)
    can.drawString((PAGE_WIDTH - text_width) / 2.0, 690, subTitle)

    can.setFillColorRGB(0,0,0)
    can.setFont("Helvetica-Bold",18)
    can.drawString(40, 615, section)

    can.line(40,605,PAGE_WIDTH-40,605)

    can.setFont("Helvetica",12)

    L = simpleSplit(text,can._fontname,can._fontsize,PAGE_WIDTH-80)
    x= 40
    y=580
    for t in L:
        can.drawString(x,y,t)
        y -= can._leading

    can.save()
    packet.seek(0)

    token_pdf = Pdf.open('/tmp/'+token+'.pdf',allow_overwriting_input=True)
    text_pdf = Pdf.open(packet)
    token_pdf_page = Page(token_pdf.pages[0])
    text_pdf_page = Page(text_pdf.pages[0])

    token_pdf_page.add_overlay(text_pdf_page)

    token_pdf.save()

def update_metadata(token):
   pdf = Pdf.open('/tmp/'+token+'.pdf',allow_overwriting_input=True)

   with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
    meta['pdf:Producer'] ='Adobe PDF Library 23.1.96'
    meta['xmp:CreatorTool'] = 'Acrobat PDFMaker 23 for Word'  
    meta['xmp:ModifyDate'] = get_mod_date()
    meta['xmp:CreateDate'] = get_creation_date()
    meta['xmp:MetadataDate'] = get_mod_date()
    meta['xmpMM:DocumentID'] = str(uuid.uuid4())
    meta['xmpMM:InstanceID'] = str(uuid.uuid4())
    
    pdf.save(encryption=Encryption(''))

def get_creation_date():
    time = datetime.datetime.now()
    rand_region =str(random.randint(1, 3))
    stamp = time.strftime('%Y-%m-%d')+'T'+time.strftime('%H:%M:%S')+ '+0'+ rand_region + ':00'
    return stamp

def get_mod_date():
    time = datetime.datetime.now()
    stamp = time.strftime('%Y-%m-%d')+'T'+time.strftime('%H:%M:%S')
    return stamp

def generate_pdf(context,title,subtitle,section,email,redirect_address):
    token = generate_token(email,redirect_address)
    update_url(token)
    insert_text(token,context,title,subtitle,section)
    update_metadata(token)
    return '/tmp/'+ token +'.pdf'
