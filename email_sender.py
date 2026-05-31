import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

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
        try:
            server.quit()
        except:
            pass

def send_gmail_with_images(receiver_email, subject, html_body, image_paths):
    """
    Sends an HTML email with inline embedded images.
    image_paths is a dictionary of {content_id: file_path}
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "chandrashekar1990a@gmail.com"
    app_password = "hqbcnhvulcojhuho"

    msg = MIMEMultipart('related')
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Create HTML part
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    msg_alternative.attach(MIMEText(html_body, 'html'))

    # Attach inline images
    for cid, img_path in image_paths.items():
        if os.path.exists(img_path):
            try:
                with open(img_path, 'rb') as img_f:
                    msg_img = MIMEImage(img_f.read())
                    msg_img.add_header('Content-ID', f'<{cid}>')
                    msg_img.add_header('Content-Disposition', 'inline', filename=os.path.basename(img_path))
                    msg.attach(msg_img)
            except Exception as e:
                print(f"⚠️ Error attaching image {img_path}: {e}")
        else:
            print(f"⚠️ Image path not found: {img_path}")

    try:
        print(f"Connecting to SMTP to send email with images to {receiver_email}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Email with images sent successfully to {receiver_email}!")
    except Exception as e:
        print(f"An error occurred while sending email to {receiver_email}: {e}")
    finally:
        try:
            server.quit()
        except:
            pass

# --- Usage Example ---
if __name__ == "__main__":
    # Replace these with your actual details
    SENDER = "your_email@gmail.com"
    PASSWORD = "your_16_character_app_password" # No spaces
    RECEIVER = "recipient_email@example.com"
    
    SUBJECT = "Test Email from Python"
    BODY = "Hello! This is an automated email sent from a Python script."

    send_gmail(SENDER, PASSWORD, RECEIVER, SUBJECT, BODY)