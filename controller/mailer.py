from flask_mail import Mail, Message

class Mailer:
    def __init__(self, app):
        app.config['MAIL_SERVER']='smtp.gmail.com'
        app.config['MAIL_PORT'] = 465
        app.config['MAIL_USERNAME'] = 'support@qolab.io'
        app.config['MAIL_PASSWORD'] = 'Theskyisblack69'
        app.config['MAIL_USE_TLS'] = False
        app.config['MAIL_USE_SSL'] = True
        mail = Mail(app)
        self.app = app
        self.mail = mail

    def sendOTP(self, email, uid, otp):
        try:
            msg = Message('Hello ' + uid, sender=self.app.config.get("MAIL_USERNAME"), recipients = [email], body = "Hello ! " + uid + ", Greetings from Qolab.io. Please use the following otp : " + otp + " on the link http://qolab.io/registerVerify" )
            self.mail.send(msg)
            return True
        except Exception as e:
            print(e)
            return None