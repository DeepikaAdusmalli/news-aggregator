from flask import Flask,flash,redirect,request,url_for,render_template,session,send_file,send_from_directory, request
from flask_session import Session
from otp import genotp
import mysql.connector
from cmail import sendmail
import random
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
from requests import get
from config import key
from os.path import join

app=Flask(__name__)
app.secret_key='748#$@jkjaf'
app.config['SESSION_TYPE']='filesystem'
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db,port=port)
#mydb=mysql.connector.connect(host='localhost',user='root',password='admin',db='finalproject')
with mysql.connector.connect(host=host,user=user,password=password,db=db,port=port) as conn:
    cursor=conn.cursor()
    cursor.execute('create table if not exists userslist(username varchar (20) primary key,mobile varchar(10),email varchar(50),password varchar(25))')
    
Session(app)
mysql=MySQL(app)
@app.route('/')
def homepage():
    return render_template('homepage.html')
@app.route('/signup',methods=['GET','POST'])
def page2():
    if request.method=='POST':
        username=request.form['username']
        mobile=request.form['mobile']
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select username from userslist')
        data=cursor.fetchall()
        cursor.execute('SELECT email from userslist')
        edata=cursor.fetchall()
            #print(data)
        if (username,) in data:
            flash('User already exists')
            return render_template('page2.html')
        if (email,) in edata:
             flash('Email  already exists')
             return render_template('page2.html')
        cursor.close()
        otp=genotp()
        subject='Thanks for registering to the application'
        body=f'Use this otp to register {otp}'
        sendmail(email,body,subject)
        return render_template('otp.html',otp=otp,username=username,mobile=mobile,email=email,password=password)
    return render_template('page2.html')
@app.route('/login',methods=['GET','POST'])
def loginpage():
    '''if session.get('user'):
        return redirect(url_for('homepage'))'''
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from userslist where email=%s and password=%s',[email,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid email or password')
            return render_template('loginpage.html')
        else:
            session['user']=email
            return redirect(url_for('index'))
    return render_template('loginpage.html')
@app.route('/home')
def home():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('loginpage'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('homepage'))
    else:
        flash('already logged out')
        return redirect(url_for('loginpage'))
    
@app.route('/otp/<otp>/<username>/<mobile>/<email>/<password>',methods=['GET','POST'])
def otp(otp,username,mobile,email,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            lst=[username,mobile,email,password]
            query='insert into userslist values(%s,%s,%s,%s)'
            cursor=mydb.cursor(buffered=True)
            mydb.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('loginpage'))
        else:
            flash('Wrong OTP')
    return render_template('otp.html',otp=otp,username=username,mobile=mobile,email=email,password=password)       
@app.route('/forgotpassword',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        username=request.form['username']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select name from userslist')
        data=cursor.fetchall()
        if(username,) in data:
            cursor.execute('select email from userslist where username=%s',[username])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("createpassword",token=token(name,240))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('loginpage'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')

@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        fid=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update finalproject set password=%s where username=%s',[npass,username])
                mydb.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('createpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'

@app.route('/index',methods=['POST','GET'])
def index():
	#print(request.remote_addr)
	response1 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'business'}).json()
	response2 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'entertainment'}).json()
	response3 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'general'}).json()
	response4 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'health'}).json()
	response5 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'science'}).json()
	response6 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'sports'}).json()
	response7 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'technology'}).json()
	return render_template('index.html', response1 = response1, response2 = response2, response3 = response3, response4 = response4, response5 = response5, response6 = response6, response7 = response7)

@app.route('/search', methods=['POST'])
def search():
	response = get("https://newsapi.org/v2/everything", params={'apikey' :'7ec9d22518644227a9df743d32bae034', 'q' : request.form['searchBar']}).json()
	return render_template('search.html', response = response)

@app.route('/sources')
def sources():
	response = get("https://newsapi.org/v2/sources", params = {'apiKey' :'7ec9d22518644227a9df743d32bae034'}).json()
	return render_template('sources.html', name = response)

@app.route('/about')
def about():
    return render_template('about.html')
	
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
if __name__ == "__main__":
    app.run(use_reloader=True,debug=True)
            
