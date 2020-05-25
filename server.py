from flask import Flask, render_template, request
import sqlite3 as sql
from datetime import datetime

app = Flask(__name__)

conn = sql.connect('database.db')

numRoom = 0
numHall = 0
numAudi = 0
serverStart = False
curUser = ''
curUserName = ''
toBook = []
toCancel = []
cancelIndex = 0
toStart = ''
toFinish = ''

@app.route('/')
def home(logout = False):
   global curUser
   global curUserName
   global serverStart
   global numRoom, numHall, numAudi
   curUser = ''
   curUserName = ''

   if(not serverStart):
      con = sql.connect("database.db")
      cursor = con.cursor()
      tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
      cursor.execute(tableListQuery)
      tables = cursor.fetchall();
      
      for table in tables:
         if(table[0][:4] == "Room"):
            numRoom = numRoom + 1
         if(table[0][:4] == "Audi"): 
            numAudi = numAudi + 1
         if(table[0][:4] == "Hall"):
            numHall = numHall + 1
      serverStart = True

   return render_template('home.html')

#Customer Module
@app.route('/signup')
def signup(msg = ''):
   return render_template('signup.html', msg = msg, usertype = "customer")

@app.route('/login')
def login(msg = ''):
   return render_template('login.html', msg= msg, usertype = "customer")

@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():

   if request.method == 'POST':
      try:
         usrnm = request.form['username']
         pswd = request.form['pass1']
         repswd = request.form['pass2']
         requesttype = request.form['submit'] == "Sign-Up"
         name = request.form['name']
         exusrnm = ''
         expass = ''
         if(requesttype):
            exusrnm = request.form['user']
            expass = request.form['pass']
         
         if(not(pswd == repswd)):
            msg = "Both passwords do not match"
            return signup(msg = msg)

         if(len(pswd) < 8):
            msg = "Password too short. Must be greater than 8 characters in length"
            return signup(msg = msg)

         con = sql.connect("database.db")
         con.row_factory = sql.Row
   
         cur = con.cursor()

         table = 'customers'
         if(requesttype):
            table = 'owners'
         cur.execute("select * from "+table)
   
         rows = cur.fetchall();

         for key in rows:
            if(key['username'] == usrnm):
               msg = "Username already taken"
               return signup(msg = msg)

         if(requesttype):
            flag = 0
            for key in rows:
               if(key['username'] == exusrnm and key['password'] == expass):
                  flag = 1
         
            if(flag == 0):
               msg = "Existing Owner Credentials Invalid"
               return signup(msg = msg)

         with sql.connect("database.db") as con:
            cur = con.cursor()
            command = "INSERT INTO " + table + " (username, password, name) VALUES (?,?,?)"
            cur.execute(command,(usrnm, pswd, name) )
            
            con.commit()
            msg = "Record successfully added. Please login using Home Page"
      except:
         con.rollback()
         msg = "Error in Signup process"
      
      finally:
         return signup(msg = msg)
         con.close()

@app.route('/findrec',methods = ['POST', 'GET'])
def findrec():

   usrnm = request.form['username']
   pswd = request.form['pass']
   requesttype = (request.form['submit'] == 'Log-In')
   con = sql.connect("database.db")
   con.row_factory = sql.Row
   
   cur = con.cursor()

   table = 'customers'
   if(requesttype):
      table = 'owners'
   command = "select * from "+table
   cur.execute(command)
   
   rows = cur.fetchall();

   for key in rows:
      if(key['username'] ==  usrnm and key['password'] == pswd):
         global curUser
         global curUserName
         curUser = key['name']
         curUserName = key['username']
         
         if(requesttype):
            return owner()
         else:
            return customer()

   msg = 'Invalid Login credentials. Try Again'
   if(requesttype):
      return loginO(msg= msg)
   else:
      return login(msg = msg)

@app.route('/customer')
def customer(msg = ''):
   return render_template("customer.html",name = curUser, msg= msg)

@app.route('/book')
def book(msg = ''):
   global numRoom
   global numHall
   global numAudi

   return render_template("book.html", rooms=numRoom, halls=numHall, audi=numAudi, msg= msg)

@app.route('/addEntries', methods = ['POST', 'GET'])
def addEntries():

   rtype = request.form['type']
   num = int(request.form['num'])
   t = num
   start = request.form['start']
   finish = request.form['finish']
   
   global numRoom, numHall, numAudi

   if(rtype == "room"):
      if(num>numRoom):
         msg = "Number of rooms needed is more than available"
         return book(msg)
   elif(rtype == "hall"):
      if(num>numHall):
         msg = "Number of halls needed is more than available"
         return book(msg)
   elif(rtype == "audi"):
      if(num>numAudi):
         msg = "Number of auditoriums needed is more than available"
         return book(msg)

   if (finish<=start):
      msg = "Invalid Dates"
      return book(msg)

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)

   if(start<currTime):
      print("This one")
      msg = "Invalid Dates"
      return book(msg)

   if(rtype == "room"):
      rtype = "Room"
   elif(rtype == "hall"):
      rtype = "Hall"
   elif(rtype == "audi"):
      rtype = "Audi"

   global toBook

   con = sql.connect("database.db")
   cursor = con.cursor()
   tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
   cursor.execute(tableListQuery)
   tables = cursor.fetchall();
   
   for table in tables:
      if(table[0][:4] == rtype):

         flag = 0
         con.row_factory = sql.Row
         cursor = con.cursor()
         command = "select * from "+table[0]
         cursor.execute(command)
         rows = cursor.fetchall();

         for data in rows:
            datastart = data['start']
            datafinish = data['finish']

            if((start>=datastart and start<datafinish) or (finish>datastart and finish<=datafinish) or (datastart>=start and datastart<finish) or (datafinish>start and datafinish<=finish)):
               flag = 1

         if(flag == 0):
            num = num - 1
            toBook.append(table[0])

         if(num == 0):
            break

   con.close()

   global toStart, toFinish

   if(rtype == "Room"):
      rtype = "Room(s)"
   elif(rtype == "Hall"):
      rtype = "Hall(s)"
   elif(rtype == "Audi"):
      rtype = "Auditorium(s)"

   if(num==t):
      msg = "No rooms available"
      return book(msg)
   
   else:
      toStart = start
      toFinish = finish
      msg = str(t-num) + "/" + str(t) + ' ' + rtype + " available on given dates. Confirm booking?" 
      return render_template("confirm.html", type = 1, msg = msg)

@app.route('/confirm', methods = ['POST', 'GET'])
def confirm():

   reply = request.form['submit']
   
   global toBook, toStart, toFinish

   if(reply == 'Confirm'):
      with sql.connect("database.db") as conn:
         cursor = conn.cursor()
         for i in toBook:
            command = "INSERT INTO " + i + " (start, finish) VALUES (?,?)" 
            cursor.execute(command,(toStart,toFinish))
            conn.commit()
            
      cursor.execute("INSERT INTO booking (username, type, num, start, finish, paid, cleaned) VALUES (?,?,?,?,?,?,?)", (curUserName, i[0:4], len(toBook), toStart, toFinish, "NO", "NO")) 
      conn.commit()     
      
      conn.close()
      toStart =''
      toFinish =''
      toBook =[]

      msg = "Booking Confirmed"
      return customer(msg)

   else:
      toStart =''
      toFinish =''
      toBook =[]
      msg = "Not Booked"
      return customer(msg)

@app.route('/mybooking')
def mybooking():

   global curUser, curUserName

   con = sql.connect("database.db")
   con.row_factory = sql.Row

   cur = con.cursor()
   cur.execute("select * from booking")
   rows = cur.fetchall();

   bookings = []

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)
   
   for key in rows:
      if(key['username'] == curUserName and (key['start']>=currTime or key['paid'] == "NO")):
         bookings.append({'name':curUser, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish'], 'paid': key['paid']})
   msg = ''

   if(len(bookings) == 0):
      msg = 'You do not have any bookings currently'

   return render_template("mybooking.html", rows= bookings, msg = msg)

@app.route('/queryInput')
def queryInput(msg = ''):
   global numRoom
   global numHall
   global numAudi

   return render_template("queryInput.html", rooms=numRoom, halls=numHall, audi=numAudi, msg= msg)

@app.route('/query', methods = ['POST', 'GET'])
def query():

   rtype = request.form['type']
   start = request.form['start']
   finish = request.form['finish']
   
   global numRoom, numHall, numAudi
   mynum = 0

   if (finish<=start):
      msg = "Invalid Dates"
      return queryInput(msg)

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)

   if(start<currTime):
      print("This one")
      msg = "Invalid Dates"
      return queryInput(msg)

   if(rtype == "room"):
      rtype = "Room"
      mynum = numRoom
   elif(rtype == "hall"):
      rtype = "Hall"
      mynum = numHall
   elif(rtype == "audi"):
      rtype = "Audi"
      mynum = numAudi

   con = sql.connect("database.db")
   cursor = con.cursor()
   tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
   cursor.execute(tableListQuery)
   tables = cursor.fetchall();
   
   available = 0

   for table in tables:
      if(table[0][:4] == rtype):

         flag = 0
         con.row_factory = sql.Row
         cursor = con.cursor()
         command = "select * from "+table[0]
         cursor.execute(command)
         rows = cursor.fetchall();

         for data in rows:
            datastart = data['start']
            datafinish = data['finish']

            if((start>=datastart and start<datafinish) or (finish>datastart and finish<=datafinish) or (datastart>=start and datastart<finish) or (datafinish>start and datafinish<=finish)):
               flag = 1

         if(flag == 0):
            available = available + 1

   con.close()

   if(rtype == "Room"):
      rtype = "Room(s)"
   elif(rtype == "Hall"):
      rtype = "Hall(s)"
   elif(rtype == "Audi"):
      rtype = "Auditorium(s)"

   
   msg = str(available) + "/" + str(mynum) + " " + rtype+ " available on given dates"
   return queryInput(msg)

@app.route('/cancel')
def cancel():

   global curUser, curUserName

   con = sql.connect("database.db")
   con.row_factory = sql.Row

   cur = con.cursor()
   cur.execute("select * from booking")
   rows = cur.fetchall();

   global toCancel
   toCancel = []
   i = 0

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)
   Cancel = []
   for key in rows:
      if(key['username'] == curUserName and key['start']>=currTime):
         toCancel.append({'id':str(i),'name':curUserName, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish']})
         Cancel.append({'id':str(i),'name':curUser, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish']})
         i = i+1
  
   msg = ''
   if(len(toCancel) == 0):
      n = 0
      msg = 'You do not have any bookings to cancel'

   return render_template("cancel.html", rows= Cancel, msg = msg)

@app.route('/removecnf', methods = ['POST', 'GET'])
def removecnf():
   global cancelIndex
   cancelIndex = int(request.form['choice'])

   con = sql.connect("database.db")
   cur = con.cursor()
   cur.execute("select * from cancelPolicy")
   rows = cur.fetchall();
   pol = rows[0][0]

   msg = 'Please confirm to cancel you booking'
   return render_template("confirm.html", pol = pol, type = 2 , msg = msg)

@app.route('/remove', methods = ['POST', 'GET'])
def remove():
   reply = request.form['submit']
   
   global toCancel, cancelIndex

   if(reply == "Confirm"):
      msg = "Booking Cancelled"

      toDelete = toCancel[cancelIndex]

      con = sql.connect("database.db")
      cur = con.cursor()
      command = "delete from booking where (username = '{}' and type = '{}' and num = '{}' and start = '{}' and finish = '{}')" 
      cur.execute(command.format(toDelete['name'],toDelete['type'],toDelete['num'],toDelete['start'],toDelete['finish']))
      con.commit()
      con.close()

      n = toDelete['num']

      with sql.connect("database.db") as con:
         cursor = con.cursor()
         tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
         cursor.execute(tableListQuery)
         tables = cursor.fetchall();
         

         for table in tables:
            if(table[0][0:4] == toDelete['type']):
               command = 'select * from '+ table[0]
               cursor.execute(command)
               rows = cursor.fetchall()

               for row in rows:
                  if(row[0] == toDelete['start'] and row[1] == toDelete['finish']):
                     command = "delete from {} where start = '{}' and finish = '{}'"
                     cursor.execute(command.format(table[0], toDelete['start'], toDelete['finish']))
                     con.commit()
                     n = n - 1
                     break

               if(n == 0):
                  break
         
      con.close()            
   else:
      msg = "Booking not Cancelled"
   
   toCancel = []
   cancelIndex = 0

   return customer(msg = msg)

@app.route('/reschedule')
def reschedule(err_msg = ''):

   global curUser, curUserName

   con = sql.connect("database.db")
   con.row_factory = sql.Row

   cur = con.cursor()
   cur.execute("select * from booking")
   rows = cur.fetchall();

   global toCancel
   toCancel = []
   i = 0

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)
   Cancel = []
   for key in rows:
      if(key['username'] == curUserName and key['start']>=currTime):
         toCancel.append({'id':str(i),'name':curUserName, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish'], 'paid': key['paid']})
         Cancel.append({'id':str(i),'name':curUser, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish']})
         i = i+1
  
   msg = ''
   if(len(toCancel) == 0):
      msg = 'You do not have any bookings to reschedule'

   return render_template("reschedule.html", rows= Cancel, msg = msg, err_msg = err_msg)

@app.route('/reschedcheck', methods = ['POST','GET'])
def reschedcheck():

   start = request.form['start']
   finish = request.form['finish']
   c = int(request.form['choice'])

   if (finish<=start):
      msg = "Invalid Dates"
      return reschedule(err_msg = msg)

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)

   if(start<currTime):
      msg = "Invalid Dates"
      return reschedule(err_msg = msg)

   global cancelIndex, toCancel, toStart, toFinish 
   change = toCancel[c]

   if not(start>= change['start']  and start < change['finish'] and finish <= change['finish'] and finish>change['start']):
      msg = "Booking can be rescheduled only between dates of original booking. For any other case, query availability and book again."
      return reschedule(err_msg = msg)

   cancelIndex = c
   toStart = start
   toFinish = finish

   con = sql.connect("database.db")
   cur = con.cursor()
   cur.execute("select * from reschedPolicy")
   rows = cur.fetchall();
   pol = rows[0][0]

   msg = "Please confirm to reschedule you booking"
   return render_template("confirm.html", pol= pol, type = 3 , msg = msg)

@app.route('/change', methods = ['POST', 'GET'])
def change():
   
   reply = request.form['submit']
   
   global toCancel, cancelIndex, toStart, toFinish

   if(reply == "Confirm"):
      msg = "Booking Rescheduled"

      toDelete = toCancel[cancelIndex]

      with sql.connect("database.db") as con:
         cursor = con.cursor()
         command = "delete from booking where (username = '{}' and type = '{}' and num = '{}' and start = '{}' and finish = '{}')" 
         cursor.execute(command.format(toDelete['name'],toDelete['type'],toDelete['num'],toDelete['start'],toDelete['finish']))
         con.commit()
         command = "INSERT INTO booking (username, type, num, start, finish, paid, cleaned) VALUES (?,?,?,?,?,?,?)" 
         cursor.execute(command, (toDelete['name'],toDelete['type'],toDelete['num'],toStart,toFinish, toDelete['paid'], "NO"))
         con.commit()  

      n = toDelete['num']

      with sql.connect("database.db") as con:
         cursor = con.cursor()
         tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
         cursor.execute(tableListQuery)
         tables = cursor.fetchall();
         
         for table in tables:
            if(table[0][0:4] == toDelete['type']):
               command = 'select * from '+ table[0]
               cursor.execute(command)
               rows = cursor.fetchall()

               for row in rows:
                  if(row[0] == toDelete['start'] and row[1] == toDelete['finish']):
                     command = "delete from {} where start = '{}' and finish = '{}'"
                     cursor.execute(command.format(table[0], toDelete['start'], toDelete['finish']))
                     con.commit()
                     command = "INSERT INTO {} (start,finish) VALUES(?,?)"
                     cursor.execute(command.format(table[0]), (toStart, toFinish))
                     con.commit()
                     n = n - 1
                     break

               if(n == 0):
                  break

      con.close()

   else:
      msg = "Booking not Rescheduled"
   
   toCancel = []
   cancelIndex = 0
   toStart = ''
   toFinish = ''

   return customer(msg = msg)

@app.route('/bill')
def bill():

   global curUser, curUserName

   con = sql.connect("database.db")
   con.row_factory = sql.Row

   cur = con.cursor()
   cur.execute("select * from booking")
   rows = cur.fetchall();

   global toCancel
   toCancel = []
   i = 0

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)
   Cancel = []
   for key in rows:
      if(key['username'] == curUserName and key['paid'] == "NO" ):
         toCancel.append({'id':str(i),'name':curUserName, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish'], 'cleaned': key['cleaned']})
         Cancel.append({'id':str(i),'name':curUser, 'type': key['type'], 'num' : key['num'], 'start': key['start'], 'finish': key['finish']})
         i = i+1
  
   msg = ''
   if(len(toCancel) == 0):
      n = 0
      msg = 'You do not have any pending payments'

   return render_template("checkbill.html", rows= Cancel, msg = msg)

@app.route('/billconf', methods = ['POST', 'GET'])
def billconf():

   c = int(request.form['choice'])
   global cancelIndex
   cancelIndex = c
   msg = "Please confirm to pay"
   return render_template("confirm.html", type = 4, msg = msg)

@app.route('/pay', methods = ['POST', 'GET'])
def pay():

   reply = request.form['submit']
   
   global toCancel, cancelIndex

   if(reply == "Confirm"):
      msg = "Bill Paid"

      toDelete = toCancel[cancelIndex]
      notCleaned = toDelete['cleaned'] == "NO"

      with sql.connect("database.db") as con:
         cursor = con.cursor()
         command = "delete from booking where (username = '{}' and type = '{}' and num = '{}' and start = '{}' and finish = '{}')" 
         cursor.execute(command.format(toDelete['name'],toDelete['type'],toDelete['num'],toDelete['start'],toDelete['finish']))
         con.commit()

         if(notCleaned):  
            command = "INSERT INTO booking (username, type, num, start, finish, paid, cleaned) VALUES (?,?,?,?,?,?,?)"
            cursor.execute(command, (toDelete['name'],toDelete['type'],toDelete['num'],toDelete['start'],toDelete['finish'], "YES", "NO"))
            con.commit()  

   else:
      msg = "Booking not Rescheduled"
   
   toCancel = []
   cancelIndex = 0

   return customer(msg = msg)


#Owner Module
@app.route('/signupO')
def signupO(msg = ''):
   return render_template('signup.html',msg = msg, usertype = "owner")

@app.route('/loginO')
def loginO(msg = ''):
   return render_template('login.html', msg = msg, usertype = "owner")

@app.route('/owner')
def owner(msg = ''):
   return render_template("owner.html",name = curUser, msg= msg)

@app.route('/add')
def add():
   global numRoom
   global numHall
   global numAudi

   return render_template("add.html", rooms=numRoom, halls=numHall, audi=numAudi)

@app.route('/addTables', methods = ['POST', 'GET'])
def addTables():

   rtype = request.form['type']
   num = int(request.form['num'])

   conn = sql.connect('database.db')
   cur = conn.cursor()
   global numRoom, numHall, numAudi
   if(rtype == 'room'):
      msg = ''
      for i in range(numRoom, numRoom + num):
         command = "CREATE TABLE Room"+str(i+1)+" (start TEXT, finish TEXT)"
         conn.execute(command)
         
      numRoom = numRoom + num
      msg = "You added "+str(num)+" rooms" 

   elif(rtype == 'hall'):
      for i in range(numHall, numHall + num):
         command = "CREATE TABLE Hall"+str(i+1)+" (start TEXT, finish TEXT)"
         conn.execute(command)
         
      numHall = numHall + num
      msg = "You added "+str(num)+" halls"

   elif(rtype == 'audi'):   
      for i in range(numAudi, numAudi + num):
         command = "CREATE TABLE Audi"+str(i+1)+" (start TEXT, finish TEXT)"
         conn.execute(command)
         
      numAudi = numAudi + num
      msg = "You added "+str(num)+" auditoriums"

   conn.close()
   return owner(msg)

@app.route('/allTables')
def allTables():

   con = sql.connect("database.db")
   cursor = con.cursor()
   command = "SELECT name FROM sqlite_master WHERE (name != 'owners' and name != 'customers' and name!= 'booking' and name!='cancelPolicy' and name!='reschedPolicy') ORDER BY name"
   cursor.execute(command)
   tables = cursor.fetchall();
   con.close()

   global toCancel
   toCancel = []
   i = 0
   for table in tables:
      toCancel.append({'id':i, 'name': table[0]})
      i = i+1

   msg = ''
   if(len(toCancel) == 0):
      msg = "No Rooms/Halls/Auditoriums currently present"

   return render_template("selectRoom.html", msg = msg, rows = toCancel)

@app.route('/getStatus', methods = ['POST', 'GET'])
def getStatus():

   choice = int(request.form['choice'])

   global toCancel

   table = toCancel[choice]['name']
   toCancel = []
   con = sql.connect("database.db")
   cursor = con.cursor()
   command = "SELECT * FROM "+table
   cursor.execute(command)
   rows = cursor.fetchall();

   data = []
   
   for row in rows:
      data.append({'start':row[0], 'finish':row[1]})

   msg = ''
   if(len(data) == 0):
      msg = "Currently no bookings"

   return render_template("showStatus.html", rows = data, msg = msg)

@app.route('/checkBookings')
def checkBookings():

   con = sql.connect("database.db")
   con.row_factory = sql.Row
   cursor = con.cursor()
   command = "SELECT * FROM booking"
   cursor.execute(command)
   bookings = cursor.fetchall();
   con.close()

   msg = ''
   if(len(bookings) == 0):
      msg = "No bookings currently"

   return render_template("showbookings.html", msg = msg, rows = bookings)

@app.route('/cleanRooms')
def cleanRooms():
   con = sql.connect("database.db")
   con.row_factory = sql.Row
   cursor = con.cursor()
   command = "SELECT * FROM booking"
   cursor.execute(command)
   bookings = cursor.fetchall();
   con.close()

   global toCancel
   toCancel = []

   currTime = str(datetime.now().year) + '-' + "{:02d}".format(datetime.now().month) + '-' + "{:02d}".format(datetime.now().day)
   for row in bookings:
      if((row["finish"]<currTime and row["cleaned"] == "NO") or (row["finish"] == currTime and datetime.now().hour >=12 and row["cleaned"] == "NO")):
         toCancel.append({'username': row['username'], 'type': row['type'], 'num': row['num'], 'start': row['start'], 'finish': row['finish'], 'paid': row['paid'], 'cleaned': row['cleaned']})

   msg = ''
   if(len(toCancel) == 0):
      msg = 'No pending cleanings'

   return render_template("toClean.html", msg = msg, rows = toCancel)

@app.route('/finishCleaning')
def finishCleaning():
   global toCancel

   msg = "All pending Rooms/Halls/Auditoriums cleaned"

   for toDelete in toCancel:
      notPaid = toDelete['paid'] == "NO"

      with sql.connect("database.db") as con:
         cursor = con.cursor()
         command = "delete from booking where (username = '{}' and type = '{}' and num = '{}' and start = '{}' and finish = '{}')" 
         cursor.execute(command.format(toDelete['username'],toDelete['type'],toDelete['num'],toDelete['start'],toDelete['finish']))
         con.commit()

         if(notPaid):  
            command = "INSERT INTO booking (username, type, num, start, finish, paid, cleaned) VALUES (?,?,?,?,?,?,?)"
            cursor.execute(command, (toDelete['username'],toDelete['type'],toDelete['num'],toDelete['start'],toDelete['finish'], "NO", "YES"))
            con.commit()  
   
   toCancel = []

   return owner(msg = msg)

@app.route('/loadPolicyPage')
def loadPolicyPage():
   return render_template("selectPolicy.html")

@app.route('/policyUpdate', methods = ['POST', 'GET'])
def policyUpdate():

   reply = request.form['submit']
   pol = 0
   if(reply == 'Reschedule Policy'):
      pol = 1

   return render_template("addPolicy.html", pol = pol)

@app.route('/updateDB', methods = ['POST', 'GET'])
def updateDB():

   policy = request.form['policy']
   if(request.form['submit'] ==  "Update Cancellation Policy"):

      with sql.connect("database.db") as con:
         cursor = con.cursor()
         cursor.execute("delete from cancelPolicy")
         con.commit()
         cursor.execute("INSERT INTO cancelPolicy (policy) VALUES (?)",(policy,))
         con.commit()
      con.close()

   else:
      with sql.connect("database.db") as con:
         cursor = con.cursor()
         cursor.execute("delete from reschedPolicy")
         con.commit()
         cursor.execute("INSERT INTO reschedPolicy (policy) VALUES (?)",(policy,))
         con.commit()
      con.close()


   msg = 'Policy Updated'
   return owner(msg = msg)

if __name__ == '__main__':
   app.run(debug = True)      