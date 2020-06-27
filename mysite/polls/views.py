from django.shortcuts import render
import pandas as pd
import os
# Create your views here.
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connection
import json
from django.views.decorators.csrf import csrf_exempt
import re
from random import random
from .forms import UploadFileForm

def json_build(raw_data) :
    j = {}
    j['slot_pre_id']= raw_data[0]
    j['time']= raw_data[1]
    j['subject']= raw_data[2]
    j['batch']= raw_data[3]
    j['grp']= raw_data[4]
    j['type']= raw_data[5]
    j['weight']= raw_data[6]
    return(j)


def my_custom_sql(request, teacher , day):
    cursor = connection.cursor()
    query = "SELECT slot_pre_id , time , subject ,batch ,grp , type , weight FROM slots_pre where deleted_at is NULL and username = '"+str(teacher)+"' and day = '"+str(day)+"'  order by time " 
    cursor.execute(query)
    row = cursor.fetchall()
#    df1 = pd.read_sql_query(query, connection)
#    print(df1[11])
#    df2 = [json_build(x) for x in df1]
#    print(df2)
    data = [json_build(x) for x in row]
    print(data)
    data2 = {}
    data2['username'] = teacher
    data2['day'] = day
    data2['timetable'] = data
    return JsonResponse(data2, safe=False )


def echo_admin(request, username , password):
    response = {}
    response['status'] = 0
    cursor = connection.cursor()
    cursor.execute("select admin_id from admin_login where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    if(len(row)>0) :
        response['status'] = 1	
    return JsonResponse(response, safe=False )

@csrf_exempt
def add_student(request):
    response = {}
    response['status'] = 0
    if(request.method == 'POST') & ('student_id' in request.POST) & ('student_name' in request.POST) & ('student_mobile' in request.POST) & ('parent_mobile' in request.POST):
        response['status'] = 1
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name')
        student_mobile = request.POST.get('student_mobile')
        parent_mobile = request.POST.get('parent_mobile')
        cursor = connection.cursor()
        cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' ")
        row = cursor.fetchall()
        if(len(row)==0) :
            cursor.execute("insert into student (school_id , student_id , name , student_contact , contact_number , username , password ) Values ( 1,  '{}' , '{}' , '{} ' , '{}', '{}', '{}' )".format(student_id , student_name , student_mobile , parent_mobile , str("1@")+str(student_id) , round(random()*1000000) ) )
    return JsonResponse(response, safe=False )    

@csrf_exempt
def add_teacher(request ):
    response = {}
    response['status'] = 0
    if(request.method == 'POST') & ('username' in request.POST) & ('name' in request.POST) & ('dept' in request.POST) & ('mobile' in request.POST):
        response['status'] = 1
        username = request.POST.get('username')
        name = request.POST.get('name')
        dept = request.POST.get('dept')
        mobile = request.POST.get('mobile')
        cursor = connection.cursor()
        cursor.execute("select username from tlogin where username = '"+str(username)+"' ")
        row = cursor.fetchall()
        print(username)
        if(len(row)==0) :
            cursor.execute("insert into tlogin (school_id , username , password , teacher_name , dept , mobile  ) Values ( 1,  '{}' , '{}' , '{}', '{}', '{}'  )".format( username , round(random()*1000000)  , name , dept , mobile ))
    return JsonResponse(response, safe=False )	


def slot_delete(request, slot_pre_id ): 
    cursor = connection.cursor()
    cursor.execute("delete from slots_pre where slot_pre_id = "+str(slot_pre_id)+"  ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 'done'
    return JsonResponse(response, safe=False ) 


@csrf_exempt
def login_post(request):
    print(request.method)
    response = {}
    response['status'] = 0
    if(request.method == 'POST'):
        print(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(str(username)+" "+str(password))
        cursor = connection.cursor()
        cursor.execute("select * from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        if(len(row)>0) :
            response['status'] = 1
    return JsonResponse(response, safe=False )


def login(request, username , password ):
    cursor = connection.cursor()
    cursor.execute("select * from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        response['status'] = 1
    return JsonResponse(response, safe=False )



def login_attendance_taker(request, username , password ):
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        query = " select a.student_id , a.presence , a.marked_at , s.class_time , s.subject , s.day , t.username from attendance a left join slots s on s.slot_id = a.slot_id left join tlogin t on t.teacher_id = a.teacher_id where t.username = '"+str(username)+"' and a.deleted_at is NULL and s.deleted_at is NULL ;"
        df1 = pd.read_sql_query(query, connection)
        path = str("/var/www/html/attendance_website/attendance_reports/")+str(row[0][0])+"_"+str(username)
        try:
            os.mkdir(path)
        except:
            print ("Creation of the directory %s failed" % path)
        df1.to_csv(path+"/"+str(username)+".csv", index = False)
        response['status'] = 1
        response['location'] = "http://attendancesimplified.com/attendance_website/attendance_reports/"+str(row[0][0]) +"_"+str(username)
        print(response['location'] )
    return JsonResponse(response, safe=False )



@csrf_exempt
def slot_edit_post(request):
    response = {}
    response['status'] = 'Invalid POST Request'
    if(request.method == 'POST'):
        password= request.POST.get('password')
        subject= request.POST.get('subject')
        day= request.POST.get('day')
        time = request.POST.get('time')
        username= request.POST.get('username')
        batch= request.POST.get('batch')
        grp= request.POST.get('grp')
        class_type= request.POST.get('type')
        weight= request.POST.get('weight')
        identifier = request.POST.get('identifier')
        if(identifier == None):
            identifier = str(username)+"_"+str(day)+"_"+str(time)
        print(identifier)
        cursor = connection.cursor()
        cursor.execute("select * from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        if(len(row)<=0) :
            print('Incorrect Username/ Password '+str(username)+' '+str(password) )
            response = {}
            response['status'] = 'Incorrect Username or Password'
        cursor.execute("select slot_pre_id from slots_pre where deleted_at is NULL and username  = '"+str(username)+"' and day = '"+str(day)+"' and time = '"+str(time)+"' limit 1 ")
        slot_pre_id  = cursor.fetchall()
        print(slot_pre_id)
        print("Len is : "+str(len(slot_pre_id)))
        if(len(slot_pre_id)>0) :
            slot_pre_id = slot_pre_id[0][0]
            cursor.execute("update slots_pre set subject = '"+str(subject)+"' , batch = '"+str(batch)+"' , grp = '"+grp+"',type = '"+class_type+"' , weight = '"+weight+"' ,identifier = '"+identifier+"'  where slot_pre_id = "+str(slot_pre_id)+" ")
        else :
            cursor.execute("insert into slots_pre (subject , day , time , username , batch , grp , type , weight , identifier ) Values ( '"+str(subject)+"' , '"+str(day)+"' , '"+str(time)+"' , '"+str(username)+"' , '"+str(batch)+"' , '"+str(grp)+"' , '"+str(class_type)+"' , '"+str(weight)+"' , '"+str(identifier)+"' )")

        response['status'] = 'Details Updated'

    return JsonResponse(response, safe=False )

@csrf_exempt
def fetch_slot_students(request):
    slot_pre_id = request.POST.get('slot_pre_id')
    cursor = connection.cursor()
    cursor.execute("SELECT identifier FROM slots_pre where slot_pre_id = '"+slot_pre_id+"' limit 1;")
    identifier = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(identifier)<=0):
        return JsonResponse(response, safe=False )
    print(str(identifier[0][0]))
    identifier = str(identifier[0][0])
    cursor.execute("SELECT student_id FROM slot_student_pre where deleted_at is NULL and not student_id = '' and  identifier = '"+identifier+"' ;")
    students = cursor.fetchall()
    if(len(students)>0):
        response = [x[0] for x in students]
    #response['status'] = 1    
    return JsonResponse(response, safe=False )



@csrf_exempt
def send_students(request):
    slot_pre_id = request.POST.get('slot_pre_id')
    print(str('slot_pre_id : ') + str(slot_pre_id))
    cursor = connection.cursor()
    cursor.execute("SELECT identifier FROM slots_pre where slot_pre_id = '"+slot_pre_id+"' limit 1;")
    identifier = cursor.fetchall()
    response = {}
    response['status'] = "0"
    if(len(identifier)<=0):
        return JsonResponse(response, safe=False )
    identifier = str(identifier[0][0])
    values = ""
    for key in request.POST:
        if key != 'slot_pre_id':
            value = request.POST[key]
            cursor.execute("SELECT student_id FROM student where student_id = '"+value+"' limit 1;")
            student_id = cursor.fetchall()
            if len(student_id)<=0 :
                cursor.execute("insert into student (student_id) values ( '"+value+"' ) ")
            if values == "" : 
                values = "('"+identifier+"' , '"+value+"')"    
            else :
                values = values + ","+ "('"+identifier+"' , '"+value+"')"
    print(values)
    cursor.execute("update slot_student_pre set deleted_at = now() where identifier  = '"+identifier+"'")               
    cursor.execute("insert into slot_student_pre (identifier , student_id) Values "+values)

    response['status'] = "1"
    return JsonResponse(response, safe=False )


@csrf_exempt
def login_sync(request):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    print("username  = "+username+" , password = " + password )
    cursor = connection.cursor()
    response = {}
    response['status'] = 0
    cursor.execute("Insert into logins_log (username , password  ) Values ( '"+username+"' , AES_ENCRYPT('"+password+"','nevertellkd12345') ) ")
    print("Successfully Logged the Request")
    cursor.execute("( SELECT t.teacher_id, t.school_id , (now() > (t.last_sync + interval 1 day)) as last_sync_1_day_ago FROM  tlogin t WHERE t.username='" + username + "' and t.password='" + password+ "'  ) union ( SELECT t.teacher_id , t.school_id , (now() > (t.last_sync + interval 1 day)) as last_sync_1_day_ago FROM  tlogin t WHERE t.username='" + username + "' and t.password=AES_ENCRYPT('" + password+ "','nevertellkd12345')  )  " )
    teacher_id = cursor.fetchall()
    if len(teacher_id)<=0 :
        return JsonResponse(response, safe=False )
    response['status'] = 1
    last_sync_1_day = str(teacher_id[0][2])	
    school_id = str(teacher_id[0][1])
    teacher_id = str(teacher_id[0][0])    
    print("Login Accepted for Sync API : school_id = "+school_id+" , teacher_id = "+teacher_id +"  last sync : "+last_sync_1_day)
    if last_sync_1_day == "0" :
        print("sync is False" )
    if last_sync_1_day == "1" :
        print("sync is True" )
        print("Deleting Future New Slots")
        cursor.execute(" delete from slots where  date(class_time) > date(now()) and marked = 0 and username = '"+username+"'  ")
        print("Adding Today's New Slots")
        cursor.execute("""insert into slots ( subject , day , batch , class_time , username, weight ,  slot_pre_id , identifier , code )  
                   select sp.subject , sp.day , sp.batch , concat( date( now() + interval {} day ) , ' ' , sp.time ) as class_time , 
                   sp.username , sp.weight , sp.slot_pre_id , sp.identifier ,  round(rand()*1000000) as code  from slots_pre sp left join 
                   slots s on s.class_time = concat( date( now() + interval {} day ) , ' ', sp.time ) and s.username = sp.username and s.subject = sp.subject and s.deleted_at is NULL and sp.deleted_at is NULL 
                   where sp.day = lower( date_format( now() + interval {} day , '%a' ) ) 
                   and s.slot_id is NULL and sp.username = '{}' """.format("0","0","0",username))
        print("Adding Slot User")
        cursor.execute(""" insert into slot_user (slot_id , username) select  s.slot_id , s.username  from slots_pre sp 
                   left join slots s on s.class_time = concat( date( now() + interval {} day ) , ' ', sp.time ) 
                   and s.username = sp.username left join slot_user su on su.slot_id = s.slot_id and 
                   su.username = s.username where sp.day = lower( date_format( now() + interval {} day , '%a' ) )  and
                   s.slot_id is not NULL and sp.username = '{}'  and su.su_id is NULL   """.format("0","0",username) )
        print("Adding Tomorrow's New Slots")
        cursor.execute("""insert into slots ( subject , day , batch , class_time , username, weight ,  slot_pre_id , identifier , code )
                   select sp.subject , sp.day , sp.batch , concat( date( now() + interval {} day ) , ' ' , sp.time ) as class_time ,
                   sp.username , sp.weight , sp.slot_pre_id , sp.identifier ,  round(rand()*1000000) as code from slots_pre sp left join
                   slots s on s.class_time = concat( date( now() + interval {} day ) , ' ', sp.time ) and
                   s.username = sp.username and s.subject = sp.subject and s.deleted_at is NULL and sp.deleted_at is NULL
                   where sp.day = lower( date_format( now() + interval {} day , '%a' ) )
                   and s.slot_id is NULL and sp.username = '{}' """.format("1","1","1",username))
        print("Adding Slot User")
        cursor.execute(""" insert into slot_user (slot_id , username) select  s.slot_id , s.username  from slots_pre sp
                   left join slots s on s.class_time = concat( date( now() + interval {} day ) , ' ', sp.time )
                   and s.username = sp.username left join slot_user su on su.slot_id = s.slot_id and
                   su.username = s.username where sp.day = lower( date_format( now() + interval {} day , '%a' ) )  and
                   s.slot_id is not NULL and sp.username = '{}'  and su.su_id is NULL   """.format("1","1",username) )
        print("Updating Last Sync")
        cursor.execute(""" update tlogin set last_sync = now() where username = '{}' """.format(username))	
    print("Fetching Slots Data")
    query = """select s.slot_id,batch,subject,s.class_time as class_time , s.identifier , s.code from slots s  
                   inner join slot_user su on su.slot_id = s.slot_id  where date(class_time) >= date(now() )  
                   and date(class_time) < date(NOW()+ INTERVAL {} Day) and marked = 0 and holiday = 0 and deleted_at is NULL 
                   and su.username = '{}' and school_id = {}  order by s.class_time """.format("1", username , school_id)
    slots_data = pd.read_sql_query(query, connection)
    slots_data.drop_duplicates(keep = "first", inplace = True)
    #print(slots_data)
    print("Fetching Slot_Students")
    slot_ids = '-1'
    slot_json = []
    for i in range(len(slots_data)) : 
        slot_ids = slot_ids + ", '"+str(slots_data.iloc[i,0])+"' " ;
        temp={}
        temp['slot_id'] = str(slots_data.iloc[i , 0])
        temp['batch'] = str(slots_data.iloc[i,1])
        temp['subject'] = str(slots_data.iloc[i,2])
        temp['class_time'] = str(slots_data.iloc[i,3])
        temp['identifier'] = str(slots_data.iloc[i,4])
        temp['code'] = str(slots_data.iloc[i,5])
        slot_json.append(temp)
    #print(slot_json)
    response['slots']= slot_json
    query = "select s.slot_id , ss.student_id  from slot_student_pre ss left join slots s on s.identifier = ss.identifier where ss.deleted_at is NULL and s.slot_id in ( {} )".format(slot_ids)
    slot_student_data = pd.read_sql_query(query, connection)
    slot_student_data.drop_duplicates(keep = "first", inplace = True)
    #print(slot_student_data)
    print("Fetching Student Data") 
    student_ids = '-1'
    slot_student_json =[]
    for i in range(len(slot_student_data)) :
        student_ids = student_ids + ", '"+str(slot_student_data.iloc[i,1])+"' " ;
        temp={}
        temp['slot_id'] = str(slot_student_data.iloc[i,0])
        temp['student_id'] = str(slot_student_data.iloc[i,1])
        slot_student_json.append(temp)
    response['slot_student']= slot_student_json
    query = "   select a.student_id , a.name from student a where student_id in ({})".format(student_ids)
    student_data = pd.read_sql_query(query, connection)
    student_data.drop_duplicates(keep = "first", inplace = True)
    student_json = []
    for i in range(len(student_data)) : 
        temp={}
        temp['name']=student_data.iloc[i,1]
        temp['student_id']=student_data.iloc[i,0]
        student_json.append(temp)
    response['student'] = student_json
    return JsonResponse(response, safe=False )

@csrf_exempt
def add_attendance(request):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))	
    slot_id = str(request.POST.get('slot_id'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    print("username  = "+username+" , password = " + password + " , slot_id = "+slot_id)
    cursor = connection.cursor()
    response = {}
    response['status'] = 1
    cursor.execute("( SELECT t.teacher_id, s.subject FROM  slots s inner join slot_user su on su.slot_id = s.slot_id inner join tlogin t on su.username = t.username WHERE s.school_id = t.school_id and t.username='" + username + "' and t.password='" + password+ "' and s.slot_id = "+slot_id+ " ) union ( SELECT t.teacher_id, s.subject FROM  slots s inner join slot_user su on su.slot_id = s.slot_id inner join tlogin t on su.username = t.username WHERE s.school_id = t.school_id and t.username='" + username + "' and t.password=AES_ENCRYPT('" + password+ "','nevertellkd12345')  and s.slot_id = "+slot_id + " )  " )
    teacher_id = cursor.fetchall()
    if len(teacher_id)<=0 :
        return JsonResponse(response, safe=False )
    subject    = str(teacher_id[0][1])
    teacher_id = str(teacher_id[0][0])
    print("Login Accepted")
    attendance = json.loads(str(request.POST.get('attendance')))
    print("---- : "+ str(attendance))
    st1 = ""
    st3 = ""
    MAC = "" 
    for i in range(len(attendance)) :
        studentID = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","",str(attendance[i]['roll']))
        presence = re.sub("[^0-9]", "" ,str(attendance[i]['presence']))
        if i == 0 :
            st1 = "( '" + studentID + "' , " +  slot_id + ","+ teacher_id + ","+presence+" , '"+MAC+"' , '"+username+"' , '"+subject+"' ) "
            st3 = "'"+studentID+"'"
        else :
            st1 = st1 + " , ( '" + studentID + "' , " +  slot_id + ","+ teacher_id + ","+presence+" , '"+MAC+"' , '"+username+"' , '"+subject+"' ) " ;
            st3 = st3+ " , '"+studentID+"' "
 
    cursor.execute("update attendance set deleted_at = now() where slot_id = " +  slot_id)
    cursor.execute("INSERT INTO attendance ( student_id , slot_id, teacher_id, presence , MAC , username , subject ) VALUES "+st1)
    cursor.execute("update student set last_detected = now() where student_id in ( "+st3+" )")
    cursor.execute(" update slots set username = '"+ username +"' where slot_id = "+slot_id)
    cursor.execute("update slots set marked = 1 , marked_at = Now() where slot_id = "+slot_id+ " ")
    return JsonResponse(response, safe=False )



@csrf_exempt
def get_unmarked_slots(request):
    response = {}
    response['status'] = 0
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))	
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    days = 70
    print("username  = "+username+" , password = " + password )
    cursor = connection.cursor()
    response = {}
    response['status'] = 1
    cursor.execute("Insert into logins_log (username , password  ) Values ( '"+username+"' , AES_ENCRYPT('"+password+"','nevertellkd12345') ) ")
    print("Successfully Logged the Request")
    cursor.execute("( SELECT t.teacher_id, t.school_id FROM  tlogin t WHERE t.username='" + username + "' and t.password='" + password+ "'  ) union ( SELECT t.teacher_id , t.school_id FROM  tlogin t WHERE t.username='" + username + "' and t.password=AES_ENCRYPT('" + password+ "','nevertellkd12345')  )  " )
    teacher_id = cursor.fetchall()
    if len(teacher_id)<=0 :
        return JsonResponse(response, safe=False )
    school_id = str(teacher_id[0][1])
    teacher_id = str(teacher_id[0][0])
    print("Login Accepted for Unmarked Slots API : school_id = "+school_id+" , teacher_id = "+teacher_id)
    query = ''' select s.slot_id,batch,subject,date_format(s.class_time,'%d-%b-%y(%a) %h:%i %p') as class_time from slots s  inner join slot_user su on su.slot_id = s.slot_id  where class_time > ( now() - interval {} day )  and date(class_time) < date( now()+ interval 7 hour  ) and marked = 0 and holiday = 0 and deleted_at is NULL and su.username = '{}' and school_id = {} order by s.class_time '''.format( days , username , 1)
    cursor.execute(query)
    slots_data = cursor.fetchall()
    slot_json = []
    for i in range(len(slots_data)) : 
        temp={}
        temp['slot_id'] = str(slots_data[i][0])
        temp['batch'] = str(slots_data[i][1])
        temp['subject'] = str(slots_data[i][2])
        temp['class_time'] = str(slots_data[i][3])
        slot_json.append(temp)
    #print(slot_json)
    response['table'] = slot_json
    return JsonResponse(response, safe=False )	

@csrf_exempt
def get_student_from_slot_id(request):
    response = {}
    response['status'] = 0
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    slot_id = str(request.POST.get('slot_id'))	
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    slot_id = re.sub("[^0-9]","" ,slot_id)
    print("username  = "+username+" , password = " + password +"  , slot_id = "+slot_id )
    cursor = connection.cursor()
    response = {}
    response['status'] = 1
    cursor.execute("Insert into logins_log (username , password  ) Values ( '"+username+"' , AES_ENCRYPT('"+password+"','nevertellkd12345') ) ")
    print("Successfully Logged the Request")
    cursor.execute("( SELECT t.teacher_id, t.school_id FROM  tlogin t WHERE t.username='" + username + "' and t.password='" + password+ "'  ) union ( SELECT t.teacher_id , t.school_id FROM  tlogin t WHERE t.username='" + username + "' and t.password=AES_ENCRYPT('" + password+ "','nevertellkd12345')  )  " )
    teacher_id = cursor.fetchall()
    if len(teacher_id)<=0 :
        return JsonResponse(response, safe=False )
    school_id = str(teacher_id[0][1])
    teacher_id = str(teacher_id[0][0])
    print("Login Accepted for Unmarked Slots API : school_id = "+school_id+" , teacher_id = "+teacher_id)
    query = ''' select batch, subject, date_format(s.class_time,'%d-%b-%y(%a) %h:%i %p') as class_time , s.identifier as identifier from slots s where slot_id = {} limit 1'''.format( slot_id )
    cursor.execute(query)
    slots_data = cursor.fetchall()
    response['batch'] = str(slots_data[0][0])
    response['subject'] = str(slots_data[0][1])
    response['time'] = str(slots_data[0][2])
    identifier = str(slots_data[0][3])
    query = '''  select a.student_id , a.name  from slot_student_pre ss left join student a on a.student_id = ss.student_id  where ss.deleted_at is NULL and identifier = '{}' and school_id = {} '''.format( identifier , school_id )
    cursor.execute(query)
    student_data = cursor.fetchall()
    student_json = []
    for i in range(len(student_data)) : 
        temp={}
        temp['student_id'] = str(student_data[i][0])
        temp['name'] = str(student_data[i][1])
        student_json.append(temp)
    response['table'] = student_json
    return JsonResponse(response, safe=False )	



@csrf_exempt
def customAttendanceJSONData(request):
    batch = str(request.POST.get('batch'))
    bactch_query = ""
    if 'batch' in request.POST:
        bactch_query = "and s.batch = '"+batch+"' "
        #print(bactch_query)
    username =  str(request.POST.get('username'))
    teacher_query = ""
    if 'username' in request.POST:
        teacher_query = "and s.username = '"+username+"' "
        #print(teacher_query)
    subject = str(request.POST.get('subject'))
    subject_query = ""
    if 'subject' in request.POST:
        subject_query = "and a.subject = '"+subject+"' "
        #print(subject_query)
    query = '''SELECT a.slot_id, a.teacher_id, a.presence , date(s.class_time) as date from attendance a left join slots s on a.slot_id = s.slot_id
    where s.marked = 1 and a.deleted_at is NULL and s.class_time >= (now() - INTERVAL 30 DAY) {}{}{} '''.format(bactch_query  , teacher_query , subject_query)
    print(query)
    df1 = pd.read_sql_query(query, connection)	
    df2 = df1.groupby('date' , as_index=False)['presence'].mean()
    #print(df2)
    dates = df2['date'].astype(str).tolist()
    #print(dates)	
    attendance = df2['presence'].tolist()
    #print(attendance)
    response = {}
    response['status'] = 1
    response['dates'] = dates
    response['attendance'] = attendance
    return JsonResponse(response, safe=False )
	
	
@csrf_exempt
def activate_code(request):
    response = {}
    response['status'] = 0
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    slot_id = str(request.POST.get('slot_id'))
    code_activation_time = str(request.POST.get('code_activation_time'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    slot_id = re.sub("[^0-9]","" ,slot_id)
    code_activation_time =  re.sub("[^0-9.:/ =-]","" ,code_activation_time)
    print("username  = "+username+" , password = " + password , )
    cursor = connection.cursor()
    response = {}
    response['status'] = 0
    cursor.execute("( SELECT t.teacher_id, s.subject , s.identifier , s.code FROM  slots s inner join slot_user su on su.slot_id = s.slot_id inner join tlogin t on su.username = t.username WHERE s.school_id = t.school_id and t.username='" + username + "' and t.password='" + password+ "' and s.slot_id = "+slot_id+ " ) union ( SELECT t.teacher_id, s.subject , s.identifier , s.code FROM  slots s inner join slot_user su on su.slot_id = s.slot_id inner join tlogin t on su.username = t.username WHERE s.school_id = t.school_id and t.username='" + username + "' and t.password=AES_ENCRYPT('" + password+ "','nevertellkd12345')  and s.slot_id = "+slot_id + " )  " )
    teacher_id = cursor.fetchall()
    if len(teacher_id)<=0 :
        return JsonResponse(response, safe=False )
    subject = str(teacher_id[0][1])
    identifier = str(teacher_id[0][2])
    code = str(teacher_id[0][3])
    teacher_id = str(teacher_id[0][0])
    print("Login Accepted for Code Activation API : subject = "+subject+" , teacher_id = "+teacher_id)
    query = ''' update slots set marked = 1, marked_at = now() , code_activate_time = '{}' where slot_id = {} '''.format( code_activation_time , slot_id )
    cursor.execute(query)
    print( " ---- marking attendance from student code entry ---- ")
    # First Insert Missing Student in the Attendance Table 
    query = ''' insert into attendance ( student_id , slot_id, teacher_id, presence , MAC , username , subject ) 
    select student_id , '{}' , '{}' , 0 , '-', '{}', '{}' from slot_student_pre where deleted_at is NULL and identifier = '{}' and student_id not in 
    ( select student_id from attendance where slot_id = '{}' and deleted_at is NULL )
     '''.format( slot_id , teacher_id , username, subject , identifier , slot_id )
    #print(query)
    cursor.execute(query)
    # Pick attendance from student_attendance_code table and delete the entries which are marked
    query = ''' update attendance set presence = 1 where slot_id = {} and student_id in ( select student_id from student_attendance_code where code = {} and code_input_time >= '{}' and code_input_time <= ('{}' + interval 200 second) )'''.format( slot_id , code , code_activation_time , code_activation_time )
    cursor.execute(query)
    response['status'] = 1
    return JsonResponse(response, safe=False )


@csrf_exempt
def recieve_student_code(request):
    response = {}
    response['status'] = 1
    code = str(request.POST.get('code'))
    code = re.sub("[^0-9]","" ,code)	
    student_id = str(request.POST.get('student_id'))
    student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
    code_input_time = str(request.POST.get('code_input_time'))
    #print(code_input_time)
    cursor = connection.cursor()
    query = ''' select slot_id from slots where code = {} and code_activate_time <= '{}' and  code_activate_time >= ('{}' - interval 200 second)  limit 1 '''.format( code , code_input_time , code_input_time )
    #print(query)
    cursor.execute( query )
    slot_id = cursor.fetchall()
    #print(slot_id)
    if len(slot_id)<=0 :
        cursor.execute(''' insert into student_attendance_code (student_id , code , code_input_time )  Values ( '{}' , '{}' , '{}') '''.format(student_id ,code , code_input_time ))
    else :
        slot_id = str(slot_id[0][0])
        #print(slot_id)
        query = ''' update attendance set presence = 1 where slot_id = '{}' and student_id = '{}' '''.format( slot_id , student_id )
        print(query)
        cursor.execute (query)
    return JsonResponse(response, safe=False )	


def create_json_subject(x,y) : 
    ret = {}
    ret['code']=str(x)
    ret['name']=str(y)
    return ret

	
@csrf_exempt
def quiz_teacher_login(request ):
    response = {}
    response['status'] = 0
    try :
        username = str(request.POST.get('username'))
        password = str(request.POST.get('password'))
        username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        cursor = connection.cursor()
        cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        if(len(row)>0) :
            response['status'] = 1
            subjects = []
            query = ''' select subject , subject_name from subjects '''
            df1 = pd.read_sql_query(query, connection)	
            subjects = [create_json_subject(x,y) for x,y in zip(df1.subject, df1.subject_name )]
            response['courses'] = subjects
            query = ''' select sc.subject, s.subject_name from subscribed_courses sc left join subjects s on sc.subject = s.subject where sc.username ='{}' '''.format(username)
            df1 = pd.read_sql_query(query, connection)	
            subscribed_course = [create_json_subject(x,y) for x,y in zip(df1.subject, df1.subject_name )]
            response['SubscribedCourses'] = subscribed_course   
            query = ''' select * from question_bank qb where qb.subject in (  select subject from subscribed_courses sc where sc.username ='{}'  ) '''.format(username)
            question_bank = pd.read_sql_query(query, connection)
            subjects = question_bank.subject.unique()
            question_bank_json = []
            for subject in subjects :
                try:
                    print(" Question Bank Subject : " +str(subject))
                    qb_json = {}
                    qb_json['subject'] =  subject 
                    question_bank_subject = question_bank[ question_bank.subject.astype(str).str.lower() == str(subject).lower() ].reset_index()
                    if len(question_bank_subject) > 0 : 
                        topics = question_bank_subject.topic.unique()
                        question_topic_json = []
                        for topic in topics : 
                            topic_json ={}
                            topic_json['topic'] = topic
                            topic_questions= []
                            question_bank_subject_topic = question_bank_subject[question_bank_subject.topic.astype(str).str.lower() == str(topic).lower()].reset_index()
                            if len(question_bank_subject_topic) > 0 : 
                                for i in range(len(question_bank_subject_topic)) : 
                                    question_json ={}
                                    question_json['question_id'] = str(question_bank_subject_topic.loc[ i , 'question_id'])
                                    question_json['question'] = str(question_bank_subject_topic.loc[ i , 'question'])
                                    question_json['options'] = question_bank_subject_topic.loc[ i , 'options']
                                    question_json['answer'] = str(question_bank_subject_topic.loc[ i , 'answer'])
                                    topic_questions.append(question_json)
                                topic_json['questions'] = topic_questions
                                question_topic_json.append(topic_json)
                        qb_json['questionTopics'] = question_topic_json
                        question_bank_json.append(qb_json)
                except Exception as e: print(e)
            response['QuestionBank'] = question_bank_json 
    except Exception as e: print(e)    
    return JsonResponse(response, safe=False )	
	

@csrf_exempt
def subscribe_course(request ):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    print(str(request.POST.get('course')) )
    subscribe_to_course = str(request.POST.get('course'))
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        response['status'] = 1
        cursor.execute("select subject from subjects where subject = '{}' limit 1 ".format(subscribe_to_course))
        row2 = cursor.fetchall()
        if len(row2)<=0 : 
            cursor.execute("insert into subjects (subject , subject_name) Values ('{}', '{}') ".format(subscribe_to_course , subscribe_to_course ))	
        cursor.execute("select subject from subscribed_courses where username = '{}' and subject = '{}' limit 1 ".format(username, subscribe_to_course))
        row3 = cursor.fetchall()
        if len(row3)<=0 : 
            query = "insert into subscribed_courses ( username , subject ) Values ( '{}' , '{}' ) ".format(username, subscribe_to_course)
            print(query)
            cursor.execute(query)
    return JsonResponse(response, safe=False )


@csrf_exempt
def add_question_to_bank(request ):
    response = {}
    response['status'] = 0
    print("add question api is running")
    try : 
        print(1)
    except Exception as e: print(e)  

    username = str(request.POST.get('username'))
    print(1.1)
    password = str(request.POST.get('password'))
    print(1.2)
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    print(1.3)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    print(2)
    subject = str(request.POST.get('subject'))
    topic = str(request.POST.get('topic'))
    question = str(request.POST.get('question'))
    options = str(request.POST.get('options'))
    answer = str(request.POST.get('answer'))
    print(str(username)+" "+str(password)+" "+str(subject)+" "+str(topic)+" "+str(question)+" "+str(options)+" "+str(answer))
    question_image = ""
    if 'question_image' in request.POST:
        question_image = str(request.POST.get('question_image'))
        question_image = re.sub("\"","\"\"" ,question_image)			
    print("---------- question image is ----------------") 
    print(question_image)
    print("---------- ----------------- ----------------") 
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    if(len(row)>0) :
        query = ''' insert into question_bank (subject , topic , question , options , answer , added_by_username , question_image )  
        Values ( '{}' , '{}', '{}', '{}', '{}', '{}' , "{}" ) '''.format(subject , topic, question , options , answer, username , question_image )
        cursor.execute(query)
        response['status'] = 1 
    return JsonResponse(response, safe=False )


@csrf_exempt
def create_quiz(request ):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    subject = str(request.POST.get('subject'))
    topics =  str(request.POST.get('topics'))
    quiz_date = request.POST.get('quiz_date')
    number_of_questions = re.sub("[^0-9]","" ,request.POST.get('number_of_questions'))
    quiz_duration_in_minutes = re.sub("[^0-9]","" ,request.POST.get('quiz_duration_in_minutes'))
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        cursor.execute("select subject from subjects where subject = '{}' limit 1 ".format(subject))
        row2 = cursor.fetchall()
        if len(row2)<=0 : 
            cursor.execute("insert into subjects (subject , subject_name ) Values ('{}' , '{}') ".format(subject, subject))	
        response['status'] = 1
        code = round(random()*1000000)
        while(len(str(code))!=6) :
            code = round(random()*1000000)	
        query = ''' insert into quiz_dates (quiz_date , topics , subject , username , quiz_code , number_of_questions , quiz_duration_in_minutes ) Values ('{}', '{}' , '{}' , '{}' , {} , {} , {} )  '''.format(quiz_date , topics , subject ,  username , code , number_of_questions , quiz_duration_in_minutes)
        cursor.execute(query)
        response['quiz_code'] = code
    return JsonResponse(response, safe=False )



def create_quiz_json(quiz_id, quiz_date, topics, quiz_code , number_of_questions , quiz_duration_in_minutes ):
    r = {}
    r['quiz_id'] = str(quiz_id)
    r['quiz_date'] = str(quiz_date)
    r['topics'] = str(topics)
    r['quiz_code'] = str(quiz_code)
    r['number_of_questions'] = str(number_of_questions)
    r['quiz_duration_in_minutes'] = str(quiz_duration_in_minutes)
    return r

@csrf_exempt
def all_subject_quiz(request ):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    subject = str(request.POST.get('subject'))
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        response['status'] = 1
        query = ''' select id , quiz_date , topics , quiz_code , number_of_questions , quiz_duration_in_minutes from quiz_dates where username ='{}' and subject= '{}'  '''.format(username , subject )
        quiz_df = pd.read_sql_query(query, connection)
        quiz_json = [create_quiz_json(i,x,y,z,a,b) for i,x,y,z,a,b in zip( quiz_df.id , quiz_df.quiz_date, quiz_df.topics , quiz_df.quiz_code , quiz_df.number_of_questions , quiz_df.quiz_duration_in_minutes )]
        response['quiz_dates'] = quiz_json
    return JsonResponse(response, safe=False )


@csrf_exempt
def delete_quiz(request ):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    quiz_id = str(request.POST.get('quiz_id'))
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        response['status'] = 1
        query = ''' delete from quiz_dates where username ='{}' and id = '{}'  '''.format(username , quiz_id )
        cursor.execute(query)
    return JsonResponse(response, safe=False )


@csrf_exempt
def delete_question(request ):
    username = str(request.POST.get('username'))
    password = str(request.POST.get('password'))
    username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    question_id = str(request.POST.get('question_id'))
    cursor = connection.cursor()
    cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        response['status'] = 1
        query = ''' delete from question_bank where added_by_username ='{}' and question_id = '{}'  '''.format(username , question_id )
        cursor.execute(query)
    return JsonResponse(response, safe=False )



@csrf_exempt
def quiz_student_login(request ):
    student_id = str(request.POST.get('student_id'))
    password = str(request.POST.get('password'))
    student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
    password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
    cursor = connection.cursor()
    cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' and password = '"+str(password)+"' limit 1 ")
    row = cursor.fetchall()
    response = {}
    response['status'] = 0
    if(len(row)>0) :
        response['status'] = 1
        student_id = str(row[0][0])
        subjects = []
        query = ''' select subject , subject_name from subjects '''
        df1 = pd.read_sql_query(query, connection)	
        subjects = [create_json_subject(x,y) for x,y in zip(df1.subject, df1.subject_name )]
        response['courses'] = subjects
        query = ''' select sc.subject, s.subject_name from student_subscribed_courses sc left join subjects s on sc.subject = s.subject where sc.student_id ='{}' '''.format(student_id)
        df1 = pd.read_sql_query(query, connection)	
        subscribed_course = [create_json_subject(x,y) for x,y in zip(df1.subject, df1.subject_name )]
        response['SubscribedCourses'] = subscribed_course   
    return JsonResponse(response, safe=False )	


@csrf_exempt
def student_subscribe_course(request ):
    response = {}
    response['status'] = 0
    try :
        student_id = str(request.POST.get('student_id'))
        password = str(request.POST.get('password'))
        student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        subscribe_to_course = str(request.POST.get('course'))
        cursor = connection.cursor()
        cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        if(len(row)>0) :
            response['status'] = 1
            student_id = str(row[0][0])
            cursor.execute("select subject from subjects where subject = '{}' limit 1 ".format(subscribe_to_course))
            row2 = cursor.fetchall()
            if len(row2)<=0 : 
                cursor.execute("insert into subjects (subject) Values ('{}') ".format(subscribe_to_course))	
            cursor.execute("select subject from student_subscribed_courses where student_id = '{}' and subject = '{}' limit 1 ".format(student_id, subscribe_to_course))
            row3 = cursor.fetchall()
            if len(row3)<=0 : 
                query = "insert into student_subscribed_courses ( student_id , subject ) Values ( '{}' , '{}' ) ".format(student_id, subscribe_to_course)
                print(query)
                cursor.execute(query)
    except Exception as e: 
        pass
    return JsonResponse(response, safe=False )

def create_student_quiz_json(quiz_id , quiz_date, topics, subject , subject_name , number_of_questions , quiz_duration_in_minutes , created_by, quiz_code):
    r = {}
    r['quiz_id'] = str(quiz_id)
    r['quiz_date'] = str(quiz_date)
    r['topics'] = str(topics)
    r['subject'] = str(subject)
    r['subject_name'] = str(subject_name)
    r['number_of_questions'] = str(number_of_questions)
    r['quiz_duration_in_minutes'] = str(quiz_duration_in_minutes)
    r['created_by'] = str(created_by)
    r['quiz_code'] = str(quiz_code)
    return r


@csrf_exempt
def show_subject_quizes_today(request ):
    response = {}
    response['status'] = 0
    try :
        student_id = str(request.POST.get('student_id'))
        password = str(request.POST.get('password'))
        student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        cursor = connection.cursor()
        cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        if(len(row)>0) :
            response['status'] = 1
            query = ''' select q.id , quiz_date , topics , s.subject , s.subject_name , number_of_questions , quiz_duration_in_minutes , username , quiz_code from quiz_dates q left join subjects s on s.subject = q.subject where quiz_date >= (now()+ interval (5*60+30-15) minute) and quiz_date <= (now()+ interval (5*60+30+4*60) minute) and q.subject in ( select subject from student_subscribed_courses where student_id =  '{}' )  '''.format( student_id )
            quiz_df = pd.read_sql_query(query, connection)
            quiz_json = [create_student_quiz_json(i ,x,y,z,a,b,c, d,e) for i,x,y,z,a,b,c,d,e in zip(quiz_df.id , quiz_df.quiz_date, quiz_df.topics , quiz_df.subject , quiz_df.subject_name , quiz_df.number_of_questions , quiz_df.quiz_duration_in_minutes , quiz_df.username , quiz_df.quiz_code )]
            response['quiz_dates'] = quiz_json
    except Exception as e: 
        pass
    return JsonResponse(response, safe=False )



def create_question_json(question_id , question , question_image , options , answer ):
    r = {}
    r['question_id'] = str(question_id)
    r['question'] = str(question)
    r['question_image'] = str(question_image)	
    r['options'] = str(options)
    #r['answer'] = str(answer)
    return r



@csrf_exempt
def get_quiz_questions(request ):
    response = {}
    response['status'] = 0
    try :
        student_id = str(request.POST.get('student_id'))
        password = str(request.POST.get('password'))
        student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        quiz_id = str(request.POST.get('quiz_id'))
        quiz_code = str(request.POST.get('quiz_code'))
        cursor = connection.cursor()
        cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        cursor.execute("select subject, topics , number_of_questions from quiz_dates where quiz_date <= ( now() + interval (5*60+30) minute ) and ( quiz_date + interval 15 minute ) >= ( now() + interval (5*60+30) minute ) and id = '"+str(quiz_id)+"' and quiz_code = '"+str(quiz_code)+"' limit 1 ")
        row2 = cursor.fetchall()
        cursor.execute("select quiz_date  from quiz_dates where id = '"+str(quiz_id)+"' and quiz_code = '"+str(quiz_code)+"' limit 1 ")
        row3 = cursor.fetchall()
        cursor.execute("select id  from quiz_questions where quiz_id = '"+str(quiz_id)+"' and student_id = '"+str(student_id)+"' limit 1 ")
        row4 = cursor.fetchall()
        if(len(row4)>0) : 
            response['reason'] = "Quiz Questions already fetched by Student"
        if(len(row2)==0) : 
            response['reason'] = "Quiz is scheduled at "+ str(row3[0][0])
        if((len(row)>0) & (len(row2)>0) & (len(row4)<=0)) :
            response['status'] = 1
            subject = str(row2[0][0])
            topics = str(row2[0][1])
            number_of_questions = str(row2[0][2])
            query = ''' select question_id , question , question_image , options , answer from question_bank qb where lower(subject) = lower('{}') and lower('{}') LIKE CONCAT('%', lower(topic) , '%') order by rand() limit {}'''.format( subject , topics , number_of_questions )
            quiz_df = pd.read_sql_query(query, connection)
            question_json = [create_question_json(x,y,z,a,b) for x,y,z,a,b in zip(quiz_df.question_id , quiz_df.question , quiz_df.question_image , quiz_df.options , quiz_df.answer )]
            response['questions'] = question_json
            cursor.execute(" insert into quiz_questions (student_id, quiz_id ) Values ('{}','{}') ".format(student_id, quiz_id  ))
    except Exception as e: 
        print(e)
    return JsonResponse(response, safe=False )




@csrf_exempt
def submit_quiz_answers(request ):
    response = {}
    response['status'] = 0
    try :
        student_id = str(request.POST.get('student_id'))
        password = str(request.POST.get('password'))
        student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        quiz_id = str(request.POST.get('quiz_id'))
        quiz_code = str(request.POST.get('quiz_code'))
        cursor = connection.cursor()
        cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        cursor.execute("select subject, topics , number_of_questions from quiz_dates where id = '"+str(quiz_id)+"' and quiz_code = '"+str(quiz_code)+"' limit 1 ")
        row2 = cursor.fetchall()
        cursor.execute("select answer_id from quiz_answers where quiz_id = '"+str(quiz_id)+"' and student_id = '"+str(student_id)+"' limit 1 ")
        row3 = cursor.fetchall()
        cursor.execute("select id from quiz_dates where (quiz_date + interval (quiz_duration_in_minutes+15) minute) < (now() + interval (5*60+30) minute ) and id = '"+str(quiz_id)+"' and quiz_code = '"+str(quiz_code)+"' limit 1 ")
        row4 = cursor.fetchall()
        if (len(row3)>0) : 
            response['status_text'] = "quiz already taken"
        if (len(row4)>0) : 
            response['status_text'] = "quiz time is over"
        if((len(row)>0) & (len(row2)>0) & (len(row3)<=0)  & (len(row4)<=0) ) :
            response['status'] = 1
            subject = str(row2[0][0])
            quiz_answers = str(request.POST.get('quiz_answers'))
            quiz_answers = json.loads(quiz_answers)
            query = ""
            for i in range(len(quiz_answers)) : 
                q= quiz_answers[i]
                if i == 0 : 
                    query  = " ( '{}','{}','{}', '{}' ) ".format(student_id, quiz_id , str(q['question_id']), str(q['answer']) )
                else : 
                    query = query + " , "+" ( '{}','{}','{}', '{}' ) ".format(student_id, quiz_id , str(q['question_id']), str(q['answer']) )
            query =  "insert into quiz_answers (student_id , quiz_id , question_id , answer ) Values " + query 
            cursor.execute(query)
            query = " update quiz_answers qa left join question_bank q on q.question_id = qa.question_id set qa.actual_answer = q.answer where student_id = '{}' and quiz_id = '{}' ".format(student_id , quiz_id)
            cursor.execute(query)
            query = " update quiz_answers set is_correct = 1 where trim(lower(actual_answer)) = trim(lower(answer)) and student_id = '{}' and quiz_id = '{}' ".format(student_id , quiz_id) 
            cursor.execute(query)
            query = " select sum(is_correct) as num_correct , avg(is_correct) as percentage_correct , count(is_correct) as total_questions from quiz_answers  where student_id = '{}' and quiz_id = '{}'  ".format(student_id , quiz_id) 
            cursor.execute(query)
            row4 = cursor.fetchall()
            num_correct = str(row4[0][0])
            percentage_correct = str(row4[0][1])
            total_questions = str(row4[0][2])
            query = " delete from student_quiz_marks where student_id = '{}' and quiz_id = '{}' ".format(student_id , quiz_id ) 
            cursor.execute(query)
            query = " insert into student_quiz_marks (student_id , quiz_id , num_correct , percentage_correct , total_questions) values ( '{}' , '{}' , '{}' , '{}' , '{}' ) ".format(student_id , quiz_id , num_correct , percentage_correct , total_questions) 
            cursor.execute(query)
            response['num_correct'] = num_correct
            response['percentage_correct'] = percentage_correct
            response['total_questions'] = total_questions
    except Exception as e: 
        print(e)
    return JsonResponse(response, safe=False )



@csrf_exempt
def hello_world(request ):
    response = {}
    response['status'] = 0
    response['ramlal'] = 'this is ramlal'    
    return 	JsonResponse(response, safe=False )

def create_result_json(student_id , num_correct , percentage_correct , total_questions ):
    r = {}
    r['student_id'] = str(student_id)
    r['num_correct'] = str(num_correct)
    r['percentage_correct'] = str(percentage_correct)
    r['total_questions'] = str(total_questions)
    return r


@csrf_exempt
def fetch_all_quiz_results(request ):
    response = {}
    response['status'] = 0
    try : 
        username = str(request.POST.get('username'))
        password = str(request.POST.get('password'))
        username = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", username)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        quiz_id = str(request.POST.get('quiz_id'))
        cursor = connection.cursor()
        cursor.execute("select teacher_id from tlogin where username = '"+str(username)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        cursor.execute("select id from quiz_dates where username = '"+str(username)+"' and id = '"+str(quiz_id)+"' limit 1 ")
        row2 = cursor.fetchall()
        if((len(row)>0) & (len(row2)>0)) :
            response['status'] = 1
            query = ''' select student_id , num_correct , concat( round(percentage_correct*100,1) , '%' ) as percentage_correct, total_questions  from student_quiz_marks where quiz_id = '{}' order by student_id '''.format(quiz_id )
            result_df = pd.read_sql_query(query, connection)
            result_json = [create_result_json(x,y,z,a) for x,y,z,a in zip(result_df.student_id , result_df.num_correct, result_df.percentage_correct , result_df.total_questions )]
            response['results'] = result_json
    except Exception as e: 
        print(e)        
    return JsonResponse(response, safe=False )


def create_student_result_json(teacher , subject , quiz_date , num_correct , percentage_correct , total_questions ):
    r = {}
    r['teacher'] = str(teacher)
    r['subject'] = str(subject)
    r['quiz_date'] = str(quiz_date)	
    r['num_correct'] = str(num_correct)
    r['percentage_correct'] = str(percentage_correct)
    r['total_questions'] = str(total_questions)
    return r
	
	
@csrf_exempt
def fetch_student_quiz_results(request ):
    response = {}
    response['status'] = 0
    try :
        student_id = str(request.POST.get('student_id'))
        password = str(request.POST.get('password'))
        student_id = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]" , "", student_id)
        password = re.sub("[^A-Za-z0-9.:/ =_?@!#$&*()]","" ,password)
        cursor = connection.cursor()
        cursor.execute("select student_id from student where student_id = '"+str(student_id)+"' and password = '"+str(password)+"' limit 1 ")
        row = cursor.fetchall()
        cursor.execute("select id from student_quiz_marks where student_id = '"+str(student_id)+"' limit 1 ")
        row2 = cursor.fetchall()
        if((len(row)>0) & (len(row2)>0)) :
            response['status'] = 1
            query = ''' select qd.username as teacher , qd.subject as subject , date_format(qd.quiz_date,'%d-%b-%y(%a) %h:%i %p') as quiz_date  , sm.num_correct , concat( round(sm.percentage_correct*100,1) , '%' ) as percentage_correct, sm.total_questions  from student_quiz_marks sm left join quiz_dates qd on qd.id = sm.quiz_id where sm.student_id = '{}' and qd.quiz_date is not NULL  '''.format(student_id )
            result_df = pd.read_sql_query(query, connection)
            result_json = [create_student_result_json(x,y,z,a ,b, c) for x,y,z,a,b,c in zip(result_df.teacher , result_df.subject , result_df.quiz_date , result_df.num_correct, result_df.percentage_correct , result_df.total_questions )]
            response['results'] = result_json
    except Exception as e: 
        print(e)        
    return JsonResponse(response, safe=False )

@csrf_exempt
def uploadTest(request):
    print("testing goes")        
    response = {}
    response['status'] = 0
    if request.method == 'POST':
        print("testing goes 2")        
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            response['status']=1
            return JsonResponse(response, safe=False )
    else:
        form = UploadFileForm()
    return JsonResponse(response, safe=False )



def handle_uploaded_file(f):
    with open('/Users/VaibhavKumar/Desktop/testFolder/name.jpg', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)









