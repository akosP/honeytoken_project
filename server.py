from flask import Flask, render_template,send_file, request, after_this_request, redirect, Response, make_response
from email.message import EmailMessage
import generatePDF
import os
import requests
from datetime import datetime
import database
import smtplib
import json

gmail_pw = os.environ.get('GMAIL_PW')
app = Flask(__name__)

@app.route('/', defaults={'path': ''},methods=['GET', 'POST'])
@app.route("/<string:path>",methods=['GET', 'POST'])
@app.route('/<path:path>',methods=['GET', 'POST'])
def index(path):
  token = path
  ip_address = request.remote_addr
  if token in database.get_tokens():
    info = get_location(ip_address,path)
    email = database.get_mail_address(token)
    redirect_address = database.get_redirect_address(token)

    send_mail(info,email)
    
    if  redirect_address:
      return redirect(redirect_address, code=302)   
  else:
    return render_template('index.html')
  
@app.route('/manage_token/',methods=['GET', 'POST'])
def display_token_alerts():
  token = request.form['token']
  if token in database.get_tokens():
    return database.get_alerts(token)
  else:
     return 'No such token exists'

@app.route('/generate_pdf/',methods=['GET', 'POST'])
def generate_pdf():
  context = request.form['context']
  title = request.form['title']
  subTitle = request.form['stitle']
  section =request.form['section']
  email =request.form['email']
  redirect_address =request.form['redirect']

  path = generatePDF.generate_pdf(context,title,subtitle=subTitle,section=section,email=email,redirect_address=redirect_address)

  @after_this_request
  def delete_image(response):
    try:
      os.remove(path)
    except Exception as ex:
      print(ex)
    return response
  return send_file(path, as_attachment=True)

def get_location(ip_address,token):
        response = requests.get("http://ip-api.com/json/{}".format(ip_address)).json()
        location_data = {
            "token": token,
            "ip": ip_address,
            "city": response.get("city"),
            "region": response.get("regionName"),
            "country": response.get("country"),
            "isp": response.get("isp"),
            "time": datetime.now().strftime('%Y %B %d %H:%M')
        }
        database.add_alert(location_data)
        return location_data


def send_mail(data,email):
    #Create your SMTP session 
    smtp = smtplib.SMTP('smtp.gmail.com', 587) 

   #Use TLS to add security 
    smtp.starttls() 
    email_address = "honeytoken.alert@gmail.com"
    email_password = gmail_pw
    #User Authentication 
    smtp.login(email_address,email_password)

    em = EmailMessage()
    data.pop('_id')
    msg = str(data)
    em.set_content(msg)
    em['To'] = email
    em['From'] = email_address
    em['Subject'] = "Honeytoken has been triggered!"

     # NB call the server's *send_message* method
    smtp.send_message(em)
    #smtp.sendmail(email_address, email,message) 

    #Terminating the session 
    smtp.quit() 


if __name__ == '__main__':
  app.run(debug=True)