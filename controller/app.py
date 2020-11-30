from flask import *
from flask_restful import *
import hashlib
import json
import os
import time
from werkzeug.utils import secure_filename

import accounts
import logger
from database import *
import apis
import pages

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'raw', 'bmp'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config.update(
    DATABASE='Hive'
)

global db
db = Database("mongodb://localhost:27017/hive")

log = logger.Logger('logs/applogs.json')

app.secret_key = os.urandom(32)#bytes(str(hex(random.getrandbits(128))), 'ascii')

API_KEY = hashlib.md5(b"I AM ALIVE!!!").hexdigest() # d3261fa60c79562a4b717f3bd3420ccc

mail = Mailer(app)

def manage_error(func):
    @wraps(func)
    def function_wrapper(*args, **kwarg):
        try:
            result = func(*args, **kwarg)
            return result
        except Exception as e:
            print("Error in %s" % request.path, e)
            log.error(request.path, request, session, e)
            return render_template("/errors/500.html")
    return function_wrapper


def validateApiKey():
    def function_wrapper(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            apiKey = request.form['apiKey']
            user, status = db.validateApiKey(apiKey)
            if status == True:
                return func(user, *args, **kwargs)
            return {"status":False, "error":"Wrong API Key"}
            
def loginRedirecter(*args, **kwargs):
    return redirect("/login")

def require_auth(ifFalse=loginRedirecter,
                 requireComplete=False,
                 ifIncomplete=lambda: redirect('/profileSettings'), level='all'):
    def function_wrapper(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            if "login" in session:
                if type(level) == list:
                    if session['access-level'] in level:
                        return func(*args, **kwargs)
                else:
                    if session['access-level'] == level:
                        return func(*args, **kwargs)
                if requireComplete and session['status'] == 'incomplete':
                    return ifIncomplete(*args, **kwargs)
                else:
                    return ifFalse(*args, **kwargs)
            else:
                return ifFalse(*args, **kwargs)
        return wrap
    return function_wrapper

def servePage(func, extra=None):
    def wrap():
        if extra is None:
            return func(request, session, db)
        else:
            return func(request, session, db, extra)
    return wrap

#######################################################################################################################
###################################################### Dashboards #####################################################
#######################################################################################################################

@app.errorhandler(404)
def page_not_found(e):
    return render_template("/404.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
@app.route("/dashboard", methods=["GET", "POST"])
@manage_error
@require_auth(ifFalse=servePage(pages.Home), requireComplete=True, level='user')
def dashboard():
    return pages.Dashboard(request, session, db)

@app.route("/", methods=["GET", "POST"])        # Home Page
@app.route("/home", methods=["GET", "POST"])        # Home Page
@app.route("/dashboard", methods=["GET", "POST"])        # Home Page
@manage_error
@require_auth(ifFalse=servePage(pages.Home), requireComplete=True, level='user')
def home():
    return pages.Dashboard(request, session, db)


@app.route("/login", methods=["GET", "POST"])
@manage_error
@require_auth(ifFalse=servePage(pages.Login), requireComplete=False, level='user')
def login_user():
    return redirect("/dashboad")


@app.route("/register", methods=["GET", "POST"])
@app.route("/register_user", methods=["GET", "POST"])
@manage_error
@require_auth(ifFalse=servePage(pages.Register, mail), requireComplete=False, level='user')
def register_user():
    return redirect("/dashboad")


@app.route("/registerVerify", methods=["GET", "POST"])
@manage_error
@require_auth(ifFalse=servePage(pages.RegisterVerify), requireComplete=False, level='user')
def registerVerify():
    return redirect("/dashboad")


@app.route("/resendOTP", methods=["GET", "POST"])
@manage_error
@require_auth(ifFalse=servePage(pages.ResendOTP, mail), requireComplete=False, level='user')
def resendOTP():
    return redirect("/dashboad")


@app.route("/logout", methods=["GET", "POST"])
@app.route("/logout", methods=["GET", "POST"], subdomain='corporate')
@manage_error
def logout():
    print("Logging OUt")
    global db
    del db
    db = Database("mongodb://localhost:27017/")
    session.pop('login', None)
    session.pop('access-level', None)
    return redirect("/login")

#######################################################################################################################
###################################################### HIVE APIS ######################################################
#######################################################################################################################

@app.route("/api/v1/fetchExperiment", methods=["POST"])
@manage_error
@validateApiKey()
def api_fetchExperiment(user):
    resource = request.form['resource']
    experiment, status = db.makeNewRun(resource)
    if status == True:
        return {"status":True, "experiment":experiment}
    return {"status":False}


@app.route("/api/v1/setExperimentWandb", methods=["POST"])
@manage_error
@validateApiKey()
def api_setExperimentWandb(user):
    pass 

@app.route("/api/v1/concludeExperiment", methods=["POST"])
@manage_error
@validateApiKey()
def api_concludeExperiment(user):
    pass 

#######################################################################################################################
##################################################### RESTFUL APIS ####################################################
#######################################################################################################################

@app.route('/uploads/<path:filename>', methods=["GET", "POST"])
@app.route("/uploads/<path:filename>", methods=["GET", "POST"], subdomain='corporate')
def uploaded_files(filename):
    print("Requesting ", filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

api = Api(app)
apiv1_uri = '/api/v1/'

# api.add_resource(apis.Contests, apiv1_uri + 'contest',
#                  resource_class_kwargs={'database': db, 'session': session})
# api.add_resource(apis.User, apiv1_uri + 'user',
#                  resource_class_kwargs={'database': db, 'session': session})
# api.add_resource(apis.Organizer, apiv1_uri + 'organizer',
#                  resource_class_kwargs={'database': db, 'session': session})
# api.add_resource(apis.Submission, apiv1_uri + 'submission',
#                  resource_class_kwargs={'database': db, 'session': session})
# api.add_resource(apis.Participant, apiv1_uri + 'participant',
#                  resource_class_kwargs={'database': db, 'session': session})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)