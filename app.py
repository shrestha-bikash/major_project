import os
import json
import re
import random
import operator
import numpy as np
import MySQLdb as mysqldb
from sklearn import svm
from sklearn import decomposition
from sklearn.multiclass import OneVsRestClassifier
from flask import Flask, render_template, send_from_directory
from flask import url_for, request, session, redirect
from flask_oauth import OAuth


#logfile = open('log','w')
SECRET_KEY = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
FACEBOOK_APP_ID = '1309139539100169'
FACEBOOK_APP_SECRET = '05ad2dab2c8cf4a6e7ec919f63b05073'

# Open database connection
#db = mysqldb.connect("localhost","root","asdf","personalityPredict" )

# prepare a cursor object using cursor() method
#cursor = db.cursor()


# initialization
app = Flask(__name__)
app.config.update(
    DEBUG = True,
)
app.secret_key = SECRET_KEY

oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': ('public_profile, email, user_status')}
)

data = np.loadtxt("static/trainingFeature.txt", delimiter =' ')
X = data[:, 0:13099]

#pca = decomposition.PCA(n_components = 10).fit(X)
#X = pca.transform(X)

y = data[:, 13099:13104]
y = y.transpose()

def svm_Model(X, y, Xt):
    model = OneVsRestClassifier(svm.LinearSVC(C=1)).fit(X,y)

    predicted = model.predict(Xt)
    return predicted


#start process_status
def processStatus(status):
        #process the status
        #Convert to lower case
        status = status.lower()
        status = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','URL', status)
        status = re.sub('@[^\s]+', 'AT_USER', status)
        status = re.sub('[\s]+', ' ', status)
        status = status.strip('\'"')
        return status
#end

#initialize stopWords
stopWords = []

#start replaceTwoOrMore
def replaceTwoOrMore(s):
        #look for 2 or more repetitions of character and replace with the character itself
        pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
        return pattern.sub(r"\1\1", s)
#nd
#start getStopWordList
def getStopWordList(stopWordListFileName):
        #read the stopwords file and build a list
        stopWords = []
        stopWords.append('AT_USER')
        stopWords.append('URL')

        fp = open(stopWordListFileName, 'r')
        line = fp.readline()
        while line:
                word = line.strip()
                stopWords.append(word)
                line = fp.readline()
        fp.close()
        return stopWords
#end

#start getfeatureVector
def getFeatureVector(status, stopWords):
        featureVector = {}
        #split status into words
        words = status.split()
        for w in words:
                #replace two or more with two ocurrences
                w = replaceTwoOrMore(w)
                #strip punctuation
                w = w.strip('\'"?,.')
                #check if the word starts with an alphabet
                val = re.search(r"^[a-zA-Z][a-zA-Z0-9]*$", w)
                #ignore if it is a stop word
                if(w in stopWords or val is None):
                        continue
                else:
                        w = w.lower()
                        if w in featureVector: featureVector[w] += 1
                        else: featureVector[w] = 1
        return featureVector
#end

st = open('static/project/stopwords.txt', 'r')
stopwords = getStopWordList('static/project/stopwords.txt')
#with open('posts.txt', 'r') as f:
#    post = [line.rstrip('\n') for line in f]

tot = open('static/bagofword.txt', 'r').read()
totalbagofwords = eval(tot)




def getStatus(inpstatus):
    usermap = {}
    bagcount = {}
    
    for row in inpstatus:
            
            processedStatus = processStatus(row)
            featureVector = getFeatureVector(processedStatus, stopwords)

            for word in featureVector:
                if word not in bagcount: bagcount[word] = 0
                bagcount[word] += 1
                count = featureVector[word]
                usermap[word] = count
            
    print usermap
    maxcount = {}
    for i in usermap:
        if i not in maxcount:
            maxcount[i] = 0
        maxcount[i] = max(maxcount[i], usermap[i])

    

    feature = [.5 + .5 * usermap[j] / (0 if j not in maxcount else maxcount[j])  if j in usermap else 0 for j in totalbagofwords]
        #feature = [1 * data[j]  if j in data else 0 for j in totalbagofwords]
    return feature

# controllers
@app.route("/")
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#----------------------------------------
# facebook authentication
#----------------------------------------

@facebook.tokengetter
def get_facebook_token():
    return session.get('oauth_token')

def pop_login_session():
    session.pop('logged_in', None)
    session.pop('oauth_token', None)


@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    #global logfile
    #logfile.write("\nresp: ")
    #logfile.write(str(resp))
    next_url = request.args.get('next') or url_for('index')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)

    session['logged_in'] = True
    session['oauth_token'] = (resp['access_token'], '')
    #logfile.write("\ntoken: ")
    #logfile.write(resp['access_token'])

    getme = facebook.get('/me')
    me = getme.data
    #logfile.write("\nme: ")
    #logfile.write(str(getme.headers))
    #logfile.write(str(getme.raw_data))
    #me = json.dumps
    getposts = facebook.get('/me/posts')
    data = getposts.data
    #data = json.dumps(data)


    posts = []
    #mesg = open('posts.txt','w')

    if 'id' in me and 'name' in me:
        
        user_id = int(me['id'])
        user_name = str(me['name'])

    
    for i in data['data']:
        for k in i:
            if k == 'message':
                msg = i['message']
                posts.append(str(msg.encode('utf-8')))

                '''
                mesg.write("\n"+str(msg.encode('utf-8')))
                logfile.write("\n"+str(msg.encode('utf-8')))
                try:
                    
                    sql = 'insert into user_status values('
                    sql += str(user_id)
                    sql += ', "'
                    sql += user_name
                    sql +='", "'
                    sql += mysqldb.escape_string(msg.encode('utf-8'))
                    sql += '")'


                    #logfile.write("\nSQL is "+sql)

                    # Execute the SQL command
                    cursor.execute(sql)    

                    # Commit your changes in the database               
                    db.commit()
                except mysqldb.DatabaseError as err:
                    logfile.write('\ndatabase exception\n')
                    logfile.write(format(err))
                    logfile.write('\n')
                    # Rollback in case there is any error
                    db.rollback()
                
                '''
    
    
    
    #mesg.close()
    feature = getStatus(posts)
    #testpca = decomposition.PCA(n_components = 10).fit(feature)
    #Xt = testpca.transform(feature)
    opn = svm_Model(X, y[0], feature)
    con = svm_Model(X, y[1], feature)
    ext = svm_Model(X, y[2], feature)
    agr = svm_Model(X, y[3], feature)
    neu = svm_Model(X, y[4], feature)
    
    #logfile.write(feature)
    #logfile.close()
    session['user'] = user_name
    session['id'] = user_id
    session['opn'] = opn[0]
    session['con'] = con[0]
    session['ext'] = ext[0]
    session['agr'] = agr[0]
    session['neu'] = neu[0]

    return redirect(next_url)

@app.route("/logout")
def logout():
    pop_login_session()
    return redirect(url_for('index'))




# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# disconnect from server
#db.close()
#logfile.close()
