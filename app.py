from flask import Flask,render_template,url_for,redirect,request,flash,session,send_file
from flask_session import Session
import mysql.connector
from otp import genotp
from cmail import sendmail
from stoken import token,dtoken
#import otp
from io import BytesIO
import re
import flask_excel as excel
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
excel.init_excel(app)
Session(app)
mydb=mysql.connector.connect(host='localhost',user='root',password='Raghava@1880',db='spm')
app.secret_key=b'PM\xaek(s'
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        stu_fname=request.form['s_fname']
        stu_lname=request.form['s_lname']
        email=request.form['email']
        ph_no=request.form['ph_no']
        password=request.form['password']
        #data={'email':email,'stu_fname':stu_fname,'stu_lname':stu_lname,'password':password}
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(email) from student where email=%s',[email])
        #data=cursor.fetchall()
        data=cursor.fetchone()[0]
        #print(data)
        if data==0:
            otp=genotp()
            data={'otp':otp,'email':email,'stu_fname':stu_fname,'stu_lname':stu_lname,'password':password}
            subject='Verification otp for SPM Application'
            body=f'Registration otp for SPM Application {otp}'
            sendmail(to=email,subject=subject,body=body)
            #return redirect(url_for('verifyotp',otp=otp,email=email,stu_fname=stu_fname,stu_lname=stu_lname,password=password))
            return redirect(url_for('verifyotp',data1=token(data=data)))
            #otp=otp.genotp()
            #print(stu_fname,stu_lname,email,ph_no,password)
            '''cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into student(email,student_fname,student_lname,password) values(%s,%s,%s,%s)',[email,stu_fname,stu_lname,password])
            mydb.commit()
            cursor.close()'''
            #print('Done')
        else:
            flash('Email already existed')
            return redirect(url_for('register'))
    return render_template('register.html')
#@app.route('/otp/<otp>/<email>/<stu_fname>/<stu_lname>/<password>',methods=['GET','POST'])
@app.route('/otp/<data1>',methods=['GET','POST'])
#def verifyotp(otp,email,stu_fname,stu_lname,password):
def verifyotp(data1):
    try:
        data1=dtoken(data=data1)
        print(data1)
    except Exception as e:
        print(e)
        return 'time out of opt'
    else:
        if request.method=='POST':
            uotp=request.form['otp']
            #if uotp==otp:
            if uotp==data1['otp']:
                cursor=mydb.cursor(buffered=True)
                #cursor.execute('insert into student(email,student_fname,student_lname,password) values(%s,%s,%s,%s)',[email,stu_fname,stu_lname,password])
                cursor.execute('insert into student(email,student_fname,student_lname,password) values(%s,%s,%s,%s)',[data1['email'],data1['stu_fname'],data1['stu_lname'],data1['password']])
                mydb.commit()
                cursor.close()
                print('d')
                flash('Registration successfull')
                return redirect(url_for('login'))
            else:
                return f'otp invalid please check your mail'
    finally:
        print('done')
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('email'):
        return redirect(url_for('panel'))
    else:
        if request.method=='POST':
            email=request.form['email']
            password=request.form['password']
            print(password.encode('utf-8'))
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select email,password from student where email=%s',[email])
                data=cursor.fetchone()
                print(data[1])
            except Exception as e:
                print(e)
                return 'Email wrong'
            else:
                if data[1]==password.encode('utf-8'):
                    session['email']=email
                    if not session.get(email):
                        session[email]={}
                        return redirect(url_for('panel'))
                else:
                    flash('Invalid password')
        return render_template('login.html')
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            added_by=session.get('email')
            #mysql
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notes(title,note_content,added_by) values(%s,%s,%s)',[title,content,added_by])
            mydb.commit()
            cursor.close()
            flash(f'Notes {title} added successfully')
            return redirect(url_for('panel'))
        return render_template('notes.html')
@app.route('/panel')
def panel():
    if not session.get('email'):
        return redirect(url_for('login'))
    return render_template('panel.html')
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,note_content from notes where nid=%s',[nid])
        note_data=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor.execute('update notes set title=%s,note_content=%s where nid=%s',[title,content,nid])
            mydb.commit()
            cursor.close()
            flash(f'Notes {title} updated successfully')
            return redirect(url_for('updatenotes',nid=nid))
        return render_template('updatenotes.html',note_data=note_data)

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s and added_by=%s',[nid,session.get('email')])
        mydb.commit()
        cursor.close()
        flash(f'Delete this {nid} successfully')
        return redirect(url_for('panel'))

@app.route('/allnotes')
def allnotes():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        added_by=session.get('email')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select nid,title,created_at from notes where added_by=%s',[added_by])
        data=cursor.fetchall()
        print(data)
        return render_template('table.html',data=data)
@app.route('/logout')
def logout():
    if session.get('email'):
        session.pop('email')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,note_content from notes where nid=%s',[nid])
        note_data=cursor.fetchone()
        return render_template('viewnotes.html',note_data=note_data)
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            file=request.files['file']
            file_name=file.filename
            added_by=session.get('email')
            file_data=file.read()
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into files_data(file_name,file_data,added_by) values(%s,%s,%s)',[file_name,file_data,added_by])
            mydb.commit()
            cursor.close()
            flash(f"file {file.filename} added successfully")
            return redirect(url_for('panel'))
    return render_template('fileupload.html')
@app.route('/viewall_files')
def viewall_files():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        added_by=session.get('email')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select f_id,file_name,created_at from files_data where added_by=%s',[added_by])
        data=cursor.fetchall()
        return render_template('allfiles.html',data=data)
@app.route('/view_file/<fid>')
def view_file(fid):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select file_name,file_data from files_data where f_id=%s and added_by=%s',[fid,session.get('email')])
            fname,fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata)
            filename=fname
            return send_file(bytes_data,download_name=filename,as_attachment=False)
        except Exception as e:
            print(e)
            return "file not found"
        finally:
            cursor.close()
@app.route('/download_file/<fid>')
def download_file(fid):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select file_name,file_data from files_data where f_id=%s and added_by=%s',[fid,session.get('email')])
            fname,fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata)
            filename=fname
            return send_file(bytes_data,download_name=filename,as_attachment=True)
        except Exception as e:
            print(e)
            return "file not found"
        finally:
            cursor.close()
@app.route('/delete_file/<fid>')
def delete_file(fid):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from files_data where f_id=%s and added_by=%s',[fid,session.get('email')])
        mydb.commit()
        cursor.close()
        flash(f'Delete this {fid} successfully')
        return redirect(url_for('panel'))
@app.route('/forgot_password',methods=['GET','POST'])
def forgotpassword():
    if session.get('email'):
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            email=request.form['email']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(email) from student where email=%s',[email])
            count=cursor.fetchone()[0]
            if count==0:
                flash('Email not exists pls register')
                return redirect(url_for('register'))
            elif count==1:
                subject='Reset link for SPM Application'
                body=f"Reset link for SPM Application: {url_for('reset',data=token(data=email),_external=True)}"
                sendmail(to=email,subject=subject,body=body)
                flash('Reset link has been sent to given email')
            else:
                return "Something went wrong"
    return render_template('forgot.html')
@app.route('/reset/<data>',methods=['GET','POST'])
def reset(data):
    try:
        email=dtoken(data=data)
    except Exception as e:
        print(e)
        return "Somethong went wrong"
    else:
        if request.method=='POST':
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update student set password=%s where email=%s',[npassword,email])
                mydb.commit() #because of saving
                cursor.close()
                flash("nwe password updated successfully")
                return redirect(url_for('login'))
            else:
                return "Confirm password wrong pls check again"
    return render_template('newpassword.html')
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('email'):
        if request.method=='POST':
            name=request.form['sname']
            strg=['A-Za-z0-9']
            pattern=re.compile(f"^{strg}",re.IGNORECASE)
            if (pattern.match(name)):
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select * from notes where added_by=%s and title like %s',[session.get('email'),name+'%']) #search title 
                sname=cursor.fetchall()#search notes title data
                cursor.execute('select f_id,file_name,created_at from files_data where added_by=%s and file_name like %s',[session.get('email'),name+'%']) #check file search
                fname=cursor.fetchall() #check file search
                cursor.close()
                return render_template('panel.html',sname=sname,fname=fname)
            else:
                flash('result not found')
                return redirect(url_for('panel'))
    else:
        return redirect(url_for('login'))
@app.route('/getexcel_data')
def getexcel_data():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        user=session.get('email')
        columns=['Title','Content','Data'] #heading in xlsx sheet
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,note_content,created_at from notes where added_by=%s',[user])
        data=cursor.fetchall()
        array_data=[list(i) for i in data]
        array_data.insert(0,columns)
        return excel.make_response_from_array(array_data,'xlsx',filename='NotesData') #module to convert array data to exce sheet

app.run(debug=True,use_reloader=True)
