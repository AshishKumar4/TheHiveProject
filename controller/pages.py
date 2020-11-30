import os
import random
import string
from flask import *
from database import *
from flask_sessionstore import Session
import json
from werkzeug.utils import secure_filename
import subprocess
from bson import ObjectId
import hashlib
import time
import requests

def render_template_user(template, session, *args, **kwargs):
    if 'login' in session and request.siteType in ['user'] and session['access-level'] == 'user':
        # print('got here')
        return render_template(template, login=session['login'], userLevel=session['access-level'], siteViewer=request.siteType, *args, **kwargs)
    else:
        return render_template(template, siteViewer=request.siteType, *args, **kwargs)

def render_template_all(template, session, *args, **kwargs):
    if 'access-level' in session:
        if session['access-level'] == 'user':
            return render_template_user(template, session, *args, **kwargs)
    else:
        return render_template(template, siteViewer=request.siteType, *args, **kwargs)

#######################################################################################################################
##################################################### User Stuff ######################################################
#######################################################################################################################


def Home(request, session, db):
    return render_template_all('/index.html', session)

def Dashboard(request, session, db):
    """
    This page is visible to users/contestents upon login
    """
    print("GOT HERE!!!")
    runningQueue = db.getFullRunningQueue(session['login'])
    pendingQueue = db.getPendingExperiments(session['login'])
    completedQueue = db.getFullCompletedQueue(session['login'])
    clientStatus = db.getAllClientStatus(session['login'])
    return render_template('dashboard.html', 
        runningQueue=runningQueue, 
        pendingQueue=pendingQueue, 
        completedQueue=completedQueue,
        clientStatus=clientStatus)

def Login(request, session, db):
    """
    The login screen for users/contestents
    """
    if request.method == "POST":
        uid = request.form['username']
        upass = request.form['password']
        print("Login : ", uid, upass)
        if(uid == '' or upass == ''):
            return render_template_user('/login.html', session, error="Enter a valid Username/Password")
        val, status = db.validateUser(uid, upass)
        print(val, status)
        if status:
            if val == "unverified":     # Don't let them login!
                session['unverified'] = uid
                return redirect('/registerVerify')
            session["login"] = uid
            # Its a list of all the access levels granted
            session["access-level"] = 'user'
            session['status'] = val
            return redirect('/dashboard')
        else:
            return render_template_user("/login.html", session, error="Incorrect Username/Password")
    else:
        return render_template_user('/login.html', session, error="")

def Register(request, session, db, mail):
    if request.method == "POST":
        data = dict(request.form)
        status = db.userExists(data)
        if status == 2:
            return render_template_user('/register.html', session, resp="Username Already Taken!")
        elif status == 3:
            return render_template_user('/register.html', session, resp="Email Already Taken!")

        data['otp'] = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))

        # if mail.sendOTP(data['emailId'], data['username'], data['otp']) is None:
        #     return jsonify("Problem in sending Email!")

        if db.createUserSimple(data) == 1:
            session['unverified'] = data['username']
            print(data, data['username'], data['password'])
            # return render_template_user("/otpVerify.html", session, uid=data['username'], resp='')
            return redirect("/login")
        else:
            return render_template_user('/register.html', session, resp="Username Already Taken")
    else:
        return render_template_user("/register.html",  session, resp = "")

def RegisterVerify(request, session, db):
    if request.method == "POST":
        try:
            # uid = request.form['username']
            uid = session['unverified']
            if uid is None:
                return redirect('/login')
            otp = request.form['otp']
            print(uid, otp)

            val, status = db.verifyOtpUser(uid, otp)
            if status:
            #    return render_template_user("/success.html", session)
                print("OTP Verified!")
                del session['unverified']
                session["login"] = uid
                # Its a list of all the access levels granted
                session["access-level"] = 'user'
                session['status'] = val
                return redirect('/profileSettings')
            else: 
                return render_template_user("/otpVerify.html", session, uid = uid, resp = "Wrong otp!")
        except Exception as ex:
            raise ex
            # print(ex)
            # return render_template_user("/500.html", session)
    else:
        if 'unverified' in session: 
            return render_template_user("/otpVerify.html", session, uid = session['unverified'], resp = "")
        return redirect('/login')

def ResendOTP(request, session, db, mail):
    if request.method == "POST":
        try:
            email = request.form['emailId']
            otp,uname = db.getOTPbyEmail(email)
            if uname is None:
                return render_template_user("/otpVerify.html", session, resp = "Username Not registered!");
            g = mail.sendOTP(email, uname, otp)
            if g:
               return render_template_user("/otpVerify.html", session, resp = "OTP sent again, may take few minutes! Contact us on Facebook if it dosent work");
            else: 
                return render_template_user("/otpVerify.html", session, resp = "Email address not found/Incorrect");
        except Exception as ex:
            raise ex
            # print(ex)
            # return render_template_user("/500.html", session)
    else:
        return render_template_user("/otpVerify.html", session, resp = "")
