import smtplib, datetime, mysql.connector, json
from email.message import EmailMessage

server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.login("1909devpatel@gmail.com", "ghansupatel@19")

today_date = datetime.date.today()
today_date_string = "'" + str(today_date.strftime("%Y")) + "-" + str(today_date.strftime("%m")) + "-" + str(int(today_date.strftime("%d"))+1) + "'"

db = mysql.connector.connect(
            host="192.168.29.201",
            user="dev_learner",
            password="dev@mysql_all",
            database="vacci_safe",
        )

conn = db.cursor()
query = "SELECT patients.email, vaccines.v_name, patients.fname, patients.lname FROM appt_records JOIN patients ON appt_records.patient_fk = patients.patient_pk JOIN vaccines ON vaccines.vaccine_pk = appt_records.vaccine_fk  WHERE reminder_date = " + today_date_string
conn.execute(query)
data_set = conn.fetchall()
print(query)
print(data_set)

names = {}
reminders = {}

for d in data_set:
    if d[0] in reminders.keys():
        reminders[d[0]].append(d[1])
    else:
        reminders[d[0]] = [d[1]]
        names[d[0]] = d[2] + " " + d[3]

print(json.dumps(reminders, indent = 4))

for email in reminders.keys():

    msg = EmailMessage()
    msg['Subject'] = 'VacciSafe Reminder'
    msg['From'] = "1909devpatel@gmail.com"
    msg['To'] = email

    reminder_msg = "Dear " + names[email] + ",\n"
    reminder_msg += "Please note that your following vaccine(s) are due:\n"

    for vaccine_name in reminders[email]:
        reminder_msg += "\t-> " +  vaccine_name + "\n"

    reminder_msg += "\nPlease do arrange to take the due vaccine(s), and mark them as 'Taken' in the VacciSafe app.\n"
    reminder_msg += "Thank you, Stay healthy and safe,\n"
    reminder_msg += "VacciSafe Team"
    print(reminder_msg)

    msg.set_content(reminder_msg)

    server.send_message(msg)

server.quit()