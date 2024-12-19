from flask import Flask, render_template, request,redirect,session,jsonify,send_from_directory,url_for
import sqlite3
from cas import CASClient
from urllib.parse import quote_plus
from cryptography.fernet import Fernet
import os
from functools import cmp_to_key

key = Fernet.generate_key()

BASE_URL = os.getenv('BASE_URL', 'http://172.22.0.2:80')
SUBPATH = os.getenv('SUBPATH', '')

SECRET_KEY = os.getenv('SECRET_KEY',os.urandom(24))
CAS_SERVER_URL = os.getenv('CAS_SERVER_URL', 'https://login.iiit.ac.in/cas/')
SERVICE_URL = os.getenv('SERVICE_URL', f'{BASE_URL}{SUBPATH}/Get_Auth')
REDIRECT_URL = os.getenv('REDIRECT_URL', f'{BASE_URL}{SUBPATH}/Get_Auth')

app = Flask(__name__)
app.secret_key = SECRET_KEY

cas_client = CASClient(
    version=3,
    service_url=f"{SERVICE_URL}?next={quote_plus(REDIRECT_URL)}",
    server_url=CAS_SERVER_URL,
)

# Database Setup
conn = sqlite3.connect('sqllite_volume/cabmates.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Login (
        Fname TEXT,
        Lname TEXT,
        Email TEXT,
        RollNo TEXT,
        Uid TEXT PRIMARY KEY,
        Batch TEXT,
        Gender TEXT,
        PhoneNo TEXT
    )
''')


cursor.execute('''CREATE TABLE IF NOT EXISTS fromCampus (BookingID INTEGER PRIMARY KEY AUTOINCREMENT, Uid TEXT, DateTime DATETIME, Station TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS toCampus (BookingID INTEGER PRIMARY KEY AUTOINCREMENT, Uid TEXT, DateTime DATETIME, Station TEXT)''')

# Database Setup End


def compare_datetime(entry1, entry2):
    if entry1[2] < entry2[2]:
        return -1
    elif entry1[2] > entry2[2]:
        return 1
    else:
        return 0
    
def sort_by_datetime(entries):
    entries.sort(key=cmp_to_key(compare_datetime))
    return entries



@app.route(f'{SUBPATH}/')
def LogIn():
    return render_template('LogIn.html', subpath=SUBPATH)


@app.route(f'{SUBPATH}/Get_Auth', methods=['POST', 'GET'])
def Get_Auth():
    if request.method == 'POST':
        cas_login_url = cas_client.get_login_url()
        return redirect(cas_login_url)
    else:
        ticket = request.args.get('ticket')
        if ticket:
            user, attributes, pgtiou = cas_client.verify_ticket(ticket)
            if user:
                roll = attributes['RollNo']
                email = attributes['E-Mail']
                first_name = attributes['FirstName']
                last_name = attributes['LastName']
                uid = attributes['uid']
                batch = ''
                gender = ''
                cursor = conn.cursor()
                try:
                    cursor.execute( '''
                                    SELECT * FROM Login WHERE Uid = ?
                                    ''', (uid,))
                    entry=cursor.fetchone()
                    conn.commit()
                    if entry:
                        fernet = Fernet(key)
                        token = fernet.encrypt(uid.encode())
                        session['token'] = token
                        return redirect(f'{SUBPATH}/upcomingTravels')
                    else:
                        message='User not found! Please Sign Up.'
                        return render_template('SignUp.html',roll=roll, email=email, first_name=first_name, last_name=last_name, uid=uid, message=message, subpath=SUBPATH)
                except:
                    message='Error with database. Please try again'
                    return render_template('LogIn.html', message=message, subpath=SUBPATH)
            else:
                message='Error with CAS. Please try again'
                return render_template('LogIn.html', message=message, subpath=SUBPATH)
        else:
            message='Error with CAS. Please try again'
            return render_template('LogIn.html', message=message, subpath=SUBPATH)
        


@app.route(f'{SUBPATH}/Get_userData',methods=['POST', 'GET'])
def Get_userData():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        roll = request.form['roll']
        uid = request.form['uid']
        gender = request.form['gender']
        batch = request.form['batch']
        PhoneNo = request.form['PhoneNo']
        cursor = conn.cursor()
        try:
            print(fname)
            print(lname)
            print(email)
            print(roll)
            print(uid)
            print(gender)
            print(batch)
            print(PhoneNo)
            cursor.execute('''
                        INSERT INTO Login (Fname, Lname, Email, RollNo, Uid, Batch, Gender, PhoneNo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (fname, lname, email, roll, uid, batch, gender, PhoneNo))
            print('signUp successful')
            conn.commit()
            fernet = Fernet(key)
            token = fernet.encrypt(uid.encode())
            session['token'] = token
            return redirect(f'{SUBPATH}/upcomingTravels')
        except:
            print('Sign Up Failed')
            message='Sign Up Failed!'
            return render_template('LogIn.html', message=message, subpath=SUBPATH)




@app.route(f'{SUBPATH}/getDataForBooking',methods=['POST', 'GET'])
def getForFromCampus():
    if request.method == 'POST':
        token = session['token']
        fernet = Fernet(key)
        uid = fernet.decrypt(token).decode()
        to = request.form['station']
        date = request.form['departureDate']
        time = request.form['departureTime']
        direction = request.form['direction']
        print(to,date,time)
        f = '%Y-%m-%d %H:%M:%S'
        date_time = date + ' ' + time + ':00'
        try:
            cursor = conn.cursor()
            if direction == 'From Campus':
                cursor.execute('''INSERT INTO fromCampus (Uid, DateTime, Station) VALUES (?, ?, ?)''', (uid, date_time, to))
            else:
                cursor.execute('''INSERT INTO toCampus (Uid, DateTime, Station) VALUES (?, ?, ?)''', (uid, date_time, to))
            print('Data inserted')
            conn.commit()
            
        except:
            print('Data not inserted')
        return redirect(f'{SUBPATH}/index')
    else:
        return redirect(f'{SUBPATH}/index')

@app.route(f'{SUBPATH}/deleteBooking', methods=['POST', 'GET'])
def delete_booking_route():
    entry_id = request.form['entry_id']
    direction = request.form['direction']
    print(direction, entry_id)
    try:
        cursor = conn.cursor()
        if direction == 'From Campus':
            cursor.execute('''DELETE FROM fromCampus WHERE BookingID = ?''', (entry_id,))
        else:
            cursor.execute('''DELETE FROM toCampus WHERE BookingID = ?''', (entry_id,))
        conn.commit()
        
        print('Data deleted')
    except:
        print('Data not deleted')
    return redirect(f'{SUBPATH}/index')  

@app.route(f'{SUBPATH}/viewBooking', methods=['POST', 'GET'])
def view_booking():
    entry_id = request.form['entry_id']
    direction = request.form['direction']
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()
    print(direction, entry_id)
    try:
        cursor = conn.cursor()
        BookingEntries = []
        if direction == 'From Campus':
            cursor.execute('''SELECT * FROM fromCampus WHERE BookingID = ?''', (entry_id,))
            # cursor.execute('''SELECT * FROM fromCampus''')
            entry = cursor.fetchone()
            cursor.execute('''SELECT * FROM fromCampus WHERE Station = ?''', (entry[3],))
            # cursor.execute('''SELECT * FROM fromCampus ''')
            
        else:
            cursor.execute('''SELECT * FROM toCampus WHERE BookingID = ?''', (entry_id,))
            # cursor.execute('''SELECT * FROM toCampus''')
            entry = cursor.fetchone()
            cursor.execute('''SELECT * FROM toCampus WHERE Station = ?''', (entry[3],))
            # cursor.execute('''SELECT * FROM toCampus''')
            
        entries = cursor.fetchall()
        
        for item in entries:
            if item[1] == uid:
                continue
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            uid = item[1]
            cursor.execute( '''select * from Login where Uid = ?''', (item[1],))
            data = cursor.fetchone()
            Fname = data[0]
            Lname = data[1]
            Name = Fname + ' ' + Lname
            Gender = data[6]
            Batch = data[5]
            temp_tuple = (date, time, uid, Name, Gender, Batch)
            BookingEntries.append(temp_tuple)
        cursor.execute('SELECT * FROM Login WHERE Uid = ?', (uid,))
        user = cursor.fetchone()
        conn.commit()
        
    except:
        print('Data not found')
    return render_template('/bookingspage.html', available_options = BookingEntries, fname=user[0], lname=user[2] , entry_id=entry_id,  direction=direction, subpath=SUBPATH)

@app.route(f'{SUBPATH}/upcomingTravels')
def upcomingTravels():
    cursor = conn.cursor()
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()
    if(session):
        cursor.execute( '''
                        SELECT * FROM fromCampus WHERE Uid = ?
                        ''', (uid,))
        entries = cursor.fetchall()
        sort_by_datetime(entries)
        fromCampus_entries = []
        for item in entries:
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            station = item[3]
            entry_id = item[0]
            temp_tuple = (date,time,station,entry_id)
            fromCampus_entries.append(temp_tuple)
        cursor.execute( '''
                        SELECT * FROM toCampus WHERE Uid = ?
                        ''', (uid,))
        
        entries = cursor.fetchall()
        sort_by_datetime(entries)
        toCampus_entries = []
        for item in entries:
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            station = item[3]
            entry_id = item[0]
            temp_tuple = (date,time,station,entry_id)
            toCampus_entries.append(temp_tuple)
        cursor.execute( '''select * from Login where Uid = ?''', (uid,))
        user = cursor.fetchone()
        return render_template('upcomingtravels.html', fromCampus_entries = fromCampus_entries, toCampus_entries = toCampus_entries, fname=user[0], lname=user[1], subpath=SUBPATH)
    else:
        return redirect(f'{SUBPATH}/')
    
@app.route(f'{SUBPATH}/index')
def index():
    cursor = conn.cursor()
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()
    if(session):
        cursor.execute( '''select * from Login where Uid = ?''', (uid,))
        user = cursor.fetchone()
        print('uid:',uid)
        print('user:',user)
        return render_template('index.html', fname=user[0],lname=user[1], subpath=SUBPATH)
    else:
        return redirect(f'{SUBPATH}/')


@app.route(f'{SUBPATH}/logout_user', methods=['POST', 'GET'])
def logout_user():
    session.pop('token', None)
    return redirect(f'{SUBPATH}/')


@app.route(f'{SUBPATH}/viewBookingRedirect', methods=['POST', 'GET'])
def view_booking_redirect():
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()
        
    try:
        cursor = conn.cursor()
        BookingEntries = []
        cursor.execute('''SELECT * FROM fromCampus''')
        entries1 = cursor.fetchall()
        
        for item in entries1:
            if item[1] == uid:
                continue
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            cursor.execute( '''select * from Login where Uid = ?''', (item[1],))
            data = cursor.fetchone()
            Fname = data[0]
            Lname = data[1]
            Name = Fname + ' ' + Lname
            email_id=data[2]
            Gender = data[6]
            PhoneNo = data[7]
            Batch = data[5]
            station= item[3]
            from_location="IIIT Campus"
            temp_tuple = (date, time, uid, Name, Gender, Batch, station, from_location, email_id, PhoneNo)
            BookingEntries.append(temp_tuple)
        
        cursor.execute('''SELECT * FROM toCampus''')
        entries1 = cursor.fetchall()
        for item in entries1:
            if item[1] == uid:
                continue
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            cursor.execute( '''select * from Login where Uid = ?''', (item[1],))
            data = cursor.fetchone()
            Fname = data[0]
            Lname = data[1]
            Name = Fname + ' ' + Lname
            Gender = data[6]
            PhoneNo = data[7]
            Batch = data[5]
            email_id=data[2]
            station= "IIIT Campus"
            from_location=item[3]
            temp_tuple = (date, time, uid, Name, Gender, Batch,station,from_location, email_id, PhoneNo)
            BookingEntries.append(temp_tuple)
        cursor.execute('SELECT * FROM Login WHERE Uid = ?', (uid,))
        user = cursor.fetchone()
        conn.commit()
        
    except Exception as e:
        print('An error occurred:', e)
        
    return render_template('/bookingspage.html', available_options = BookingEntries, fname=user[0], lname=user[1], subpath=SUBPATH)

def isTimeNotInRange(requested_time, entry_time):
    for i in range(len(requested_time)):
        hour = int(entry_time.split(':')[0])
        timeRange = requested_time[i].split('-')
        if (hour >= int(timeRange[0].split(':')[0]) and hour <= int(timeRange[1].split(':')[0])):
            return False
    return True

@app.route(f'{SUBPATH}/apply_filters', methods=['POST'])
def apply_filters():
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()
    
    try:
        cursor = conn.cursor()
        filters = request.json

        requested_batch = filters.get('selectedBatch').split(",")
        requested_time = filters.get('selectedTime').split(",")
        requested_desti = filters.get('selectedDestination').split(",")
        requested_start = filters.get('selectedStart').split(",")
        requested_date = filters.get('selectedDate')
        
        AllEntries = []
        cursor.execute('''SELECT * FROM fromCampus''')
        entries1 = cursor.fetchall()
        for item in entries1:
            if item[1] == uid:
                continue
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            cursor.execute( '''select * from Login where Uid = ?''', (item[1],))
            data = cursor.fetchone()
            Fname = data[0]
            Lname = data[1]
            Name = Fname + ' ' + Lname
            email_id=data[2]
            Gender = data[6]
            PhoneNo = data[7]
            Batch = data[5]
            station= item[3]
            from_location="IIIT Campus"
            temp_tuple = (date, time, uid, Name, Gender, Batch, station, from_location, email_id, PhoneNo)
            AllEntries.append(temp_tuple)
        
        cursor.execute('''SELECT * FROM toCampus''')
        entries1 = cursor.fetchall()
        for item in entries1:
            if item[1] == uid:
                continue
            date = item[2].split(' ')[0]
            time = item[2].split(' ')[1]
            cursor.execute( '''select * from Login where Uid = ?''', (item[1],))
            data = cursor.fetchone()
            Fname = data[0]
            Lname = data[1]
            Name = Fname + ' ' + Lname
            Gender = data[6]
            PhoneNo = data[7]
            Batch = data[5]
            email_id=data[2]
            station= "IIIT Campus"
            from_location=item[3]
            temp_tuple = (date, time, uid, Name, Gender, Batch,station,from_location, email_id, PhoneNo)
            AllEntries.append(temp_tuple)

        BookingEntries = []       
        for entry in  AllEntries:
            if (requested_batch[0] != '' and entry[5] not in requested_batch):
                continue
            if (requested_desti[0] != '' and entry[6] not in requested_desti):
                continue
            if (requested_start[0] != '' and entry[7] not in requested_start):
                continue
            if (requested_date != None and entry[0] != requested_date):
                continue
            if (requested_time[0] != '' and isTimeNotInRange(requested_time, entry[1])):
                continue
            BookingEntries.append(entry)
                
        filtered_data = {'available_options': BookingEntries}
        
        return jsonify(filtered_data)
    
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500
    
    

@app.route(f'{SUBPATH}/about')
def about():
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Login WHERE Uid = ?', (uid,))
    user = cursor.fetchone()

    return render_template('about.html', fname=user[0], lname=user[1], subpath=SUBPATH)


@app.route(f'{SUBPATH}/editprofilepage')
def editprofilepage():
    token = session['token']
    fernet = Fernet(key)
    uid = fernet.decrypt(token).decode()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Login WHERE Uid = ?', (uid,))
        user = cursor.fetchone()
        
        return render_template('editprofilepage.html', fname=user[0], lname=user[1],user=user, subpath=SUBPATH)
    except Exception as e:
        print('An error occurred:2', e)
    


@app.route(f'{SUBPATH}/update_userData', methods=['POST'])
def update_userData():
    try:
        gender = request.form.get('gender')
        batch = request.form.get('batch')
        PhoneNo = request.form.get('PhoneNo')
        token = session['token']
        fernet = Fernet(key)
        uid = fernet.decrypt(token).decode()

        cursor = conn.cursor()

        cursor.execute('''
        UPDATE Login
        SET gender = ?, batch = ?, PhoneNo = ?
        WHERE Uid = ?
        ''', (gender, batch, PhoneNo, uid))
        
        conn.commit()
        
        cursor.execute('SELECT * FROM Login WHERE Uid = ?', (uid,))
        user = cursor.fetchall()
        

        # Redirect with a success message
        return redirect(url_for('editprofilepage', update_message='success', subpath=SUBPATH))
        
    except Exception as e:
        print('An error occurred:', e)
        return redirect(url_for('editprofilepage', update_message='error', subpath=SUBPATH))

@app.route(f'{SUBPATH}/static/<path:path>')
def send_report(path: str = ""):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)