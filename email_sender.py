import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_gmail(receiver_email, subject, body):
    """
    Sends an email using a Gmail account.
    """
    # 1. Set up the SMTP server and port for Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "chandrashekar1990a@gmail.com"
    app_password = "hqbcnhvulcojhuho"

    # 2. Create the email message container
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # 3. Attach the body of the email to the message
    msg.attach(MIMEText(body, 'plain'))

    try:
        # 4. Connect to the server
        print("Connecting to server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Secure the connection
        
        # 5. Login using the App Password
        print("Logging in...")
        server.login(sender_email, app_password)
        
        # 6. Send the email
        print("Sending email...")
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # 7. Close the connection to the server
        server.quit()

# --- Usage Example ---
if __name__ == "__main__":
    # Replace these with your actual details
    SENDER = "your_email@gmail.com"
    PASSWORD = "your_16_character_app_password" # No spaces
    RECEIVER = "recipient_email@example.com"
    
    SUBJECT = "Test Email from Python"
    BODY = "Hello! This is an automated email sent from a Python script."

    send_gmail(SENDER, PASSWORD, RECEIVER, SUBJECT, BODY)