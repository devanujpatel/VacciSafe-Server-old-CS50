from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import mysql.connector, json, datetime

db = mysql.connector.connect(
            host="192.168.29.201",
            user="dev_learner",
            password="dev@mysql_all",
            database="vacci_safe"
        )

def check_id(user_email, user_password):

    conn = db.cursor()

    pwd_query = "SELECT password FROM patients WHERE email = '" +user_email+"'"

    conn.execute(pwd_query) 
    stored_password = conn.fetchall()

    conn.close()

    if stored_password:
        try:
            stored_password = stored_password[0][0]
            if user_password == stored_password:
                return True
            else:
                return False
        except:
            return "error"
    else:
        return "error"


def make_vaccine_date(dob_date_obj, vaccines_master_tuples):

    dob_date_obj = datetime.datetime.combine(dob_date_obj, datetime.time(0, 0)).date()
    # this is a list containin dictionaries about vaccines (since tuples are immutable!)
    vaccines_master = []

    for vaccine in vaccines_master_tuples:
        vaccines_master.append({"pk":vaccine[0],"name":vaccine[1], "date_v":None, "disease":vaccine[2], "details":vaccine[5], "gender":vaccine[6], "reminder_date":None, "vac_taken_date":None})
        ymw_string = vaccine[3]
        # sample vaccine date: 00y00m06w
        years = ymw_string[0:2]
        if years[0] == "0":
            years = years[1]
        years = int(years)
        months = ymw_string[3:5]
        if months[0] == "0":
            months = months[1]
        months = int(months)
        weeks = ymw_string[6:8]
        if weeks[0] == "0":
            weeks = weeks[1]
        weeks = int(weeks)

        # as per the data entries done in the database:
        # we have 14 weeks and 0 months as the faulty entries and then the correct combinations of vaccine dates
        # possible faulty combinations to be converted into proper ones: 0 months and 6, 10 or 14 weeks
        if weeks == 6:
            months += 1
            days = 14
        elif weeks == 10:
            months += 2
            days = 14
        elif weeks == 14:
            months += 3
            days = 14
        else:
            days = weeks * 7
        
        date_year = int(dob_date_obj.strftime("%Y")) + years
        date_month = int(dob_date_obj.strftime("%m")) + months
        date_day =  int(dob_date_obj.strftime("%d")) + days

        if date_month in [1,3,5,7,8, 10, 12]:
            max_date = 31
        elif date_month == 2 and date_year % 4 == 0:
            # leap year
            max_date = 29
        elif date_month == 2 and date_year % 4 != 0:
            max_date = 28
        else:
            max_date = 30

        while date_day > max_date:
            date_month += 1
            date_day = date_day - max_date

        while date_month > 12:
            date_year += 1
            date_month = date_month - 12

        print(date_year, date_month, date_day)

        date_v = datetime.date(date_year, date_month, date_day)
        
        vaccines_master[-1]["date_v"] = date_v

        if date_v > dob_date_obj:
            vaccines_master[-1]["reminder_date"] = date_v
        else:
            vaccines_master[-1]["vac_taken_date"] = dob_date_obj

    return vaccines_master

def get_insert_date(date):
    # convert datetime obj to a yyyy-mm-dd format (in string)
    return str(date.strftime("%Y")) + "-" + str(date.strftime("%m")) + "-" + str(date.strftime("%d"))


def get_recommended_vaccines(email):
    conn = db.cursor()

    conn.execute("SELECT dob FROM patients WHERE email = '"+email+"'")
    dob = conn.fetchall()
    conn.execute("SELECT * FROM vaccines")
    all_vaccines = conn.fetchall()
    conn.execute("SELECT patient_pk FROM patients WHERE email = '"+email+"'")
    patient_pk = conn.fetchall()

    conn.close()

    # cursor is not as such subscriptable

    for pk in patient_pk:
        patient_pk = pk[0]
    
    # this is a list which contains tuples containing data of vaccines
    vaccines_master = []
    for row in all_vaccines:
        vaccines_master.append(row)

    for row in dob:
        dob = row[0]

    vaccines_master = make_vaccine_date(dob, vaccines_master)
    
    conn = db.cursor()
    
    for vaccine in vaccines_master:
        
        vaccine_fk = vaccine["pk"]

        if vaccine["reminder_date"] == None:
            date = get_insert_date(vaccine["vac_taken_date"])
            query = f"INSERT INTO appt_records(vaccine_fk, patient_fk, vac_taken_date) VALUES ({vaccine_fk}, {patient_pk}, '{date}');"
        else:
            date = get_insert_date(vaccine["reminder_date"])
            query = f"INSERT INTO appt_records(vaccine_fk, patient_fk, reminder_date) VALUES ({vaccine_fk}, {patient_pk}, '{date}');"

        print(query)
        conn.execute(query)
        conn.fetchall()
        conn.execute("COMMIT;")
        conn.fetchall()
    # out of loop
    conn.close()

    return vaccines_master


def index(request):
    conn = db.cursor()
    conn.execute("SELECT * FROM appt_records")
    vaccines = conn.fetchall()
    conn.close()
    return HttpResponse(str(vaccines))

def register(request):

    data = json.loads(request.body)

    email = data['email']
    password = data['password']
    fname = data['fname']
    lname = data['lname']
    mobile_number = int(data['mobile_number'])
    gender = data['gender']
    year_dob = data['year_dob']
    month_dob = data['month_dob']
    day_dob = data['day_dob']
    blood_group = data['blood_group']
    address = data['address']
    city = data['city']
    dob_string = year_dob+ "-" + month_dob + "-" + day_dob
    
    query = f"INSERT INTO patients(fname, lname, email, password, external_id, mobile_number, gender, dob, bloodgroup, addr, city) VALUES ('{fname}', '{lname}', '{email}', '{password}', '{email}', {mobile_number}, '{gender}', '{dob_string}', '{blood_group}', '{address}', '{city}')"
    query_pk = "SELECT patient_pk FROM patients WHERE email = '" + email + "'"
    
    print(query)
    print(query_pk)
    
    conn = db.cursor()

    try:       
        conn.execute(query)
        conn.fetchall()
    except mysql.connector.errors.IntegrityError:
        print("email exists")
        return HttpResponse(json.dumps({"pk":"email exists"}))

    conn.execute(query_pk)
    pk_set = conn.fetchall()

    conn.close()
    
    result_set = get_recommended_vaccines(email)

    return HttpResponse(str(json.dumps({"pk":pk_set[0][0],"data": json.dumps(result_set, default = str)})))

@csrf_exempt
def log_in(request):
    identification = json.loads(request.body)

    result = check_id(identification["email"], identification["password"])

    if result == True:
        return HttpResponse(json.dumps({"is_valid":"true"}))

    elif result == False:
        return HttpResponse(json.dumps({"data": "false"}))
    else:
        return HttpResponse(json.dumps({"data": "no record found"}))