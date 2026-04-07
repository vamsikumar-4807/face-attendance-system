import smtplib
import pandas as pd
from email.message import EmailMessage
from datetime import date

def send_mails():

    print("📧 Mail system started...")

    students = pd.read_csv("students.csv")
    attendance = pd.read_csv("attendance.csv")

    # present names
    present_names = attendance["name"].str.lower().tolist()

    # find absentees
    absent_students = students[
        ~students["name"].str.lower().isin(present_names)
    ]

    sender_email = "pydah.attendance.system@gmail.com"
    sender_password = "wmrv xwrb dnyo btlg"   # 🔐 PUT GMAIL APP PASSWORD HERE

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)

    today = date.today().strftime("%d-%m-%Y")

    absentee_names = []

    for index, row in absent_students.iterrows():

        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = row["email"]
        msg["Subject"] = "Attendance Alert"

        msg.set_content(f"""
This is an automated message from Pydah College.

Dear {row['name']},

You were marked ABSENT today.
Please make sure that your attendance is mandatory
A strict action will be taken for repeated absentees

If there is any issue, please contact  Pydah College CSE Dept.

Regards,
Pydah College
""")

        server.send_message(msg)
        print("Mail sent to:", row["name"])

        absentee_names.append(row["name"])

    server.quit()
    print("✅ Mail system finished.")

    return absentee_names
