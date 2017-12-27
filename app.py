import os
import json
import re
import random
import operator
import numpy as np
from sklearn import svm
from sklearn import decomposition
from sklearn.multiclass import OneVsRestClassifier
from flask import Flask, render_template, send_from_directory
from flask import url_for, request, session, redirect
from flask_oauth import OAuth
from flask_sqlalchemy import SQLAlchemy


SECRET_KEY = os.urandom(24)
FACEBOOK_APP_ID = '1309139539100169'
FACEBOOK_APP_SECRET = '05ad2dab2c8cf4a6e7ec919f63b05073'


# initialization
app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300
'''database url for heroku server'''
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dtspyortohlevx:R4sLteXpCGMY1WdZ3KORtnIylP@ec2-54-243-190-37.compute-1.amazonaws.com:5432/d72udbjagl2df0'
'''database url for localhost'''
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bikash:asdf@localhost/userdata'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config.update(
    DEBUG = False,
)
app.secret_key = SECRET_KEY

oauth = OAuth()

db = SQLAlchemy(app)

# defining the class for database fields
class Users(db.Model):
   __tablename__ = 'users'
   id = db.Column('id', db.Integer, primary_key = True)
   userID = db.Column(db.String(50), unique = True)
   name = db.Column(db.String(100))
   opn = db.Column(db.Integer)
   con = db.Column(db.Integer)
   ext = db.Column(db.Integer)
   agr = db.Column(db.Integer)
   neu = db.Column(db.Integer)
   wordCount = db.Column(db.Integer)
   wordList = db.Column(db.String(12000))
   # review = db.Column(db.String(20))


   def __init__(self, userID, name, opn, con, ext, agr, neu, wordCount, wordList):

        self.userID = userID
        self.name = name
        self.opn = opn
        self.con = con
        self.ext = ext
        self.agr = agr
        self.neu = neu
        self.wordCount = wordCount
        self.wordList = wordList

# setting the oauth for facebook integration
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': ('public_profile, email, user_posts')}
)

# loading the dataset from static file
data = np.loadtxt("static/trainingFeature.txt", delimiter =' ')
X = data[:, 0:13099]

#pca = decomposition.PCA(n_components = 10).fit(X)
#X = pca.transform(X)

y = data[:, 13099:13104]
y = y.transpose()

# defining the our svm model for prediction
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
#end

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

# getting the stopwords stored in static file
st = open('static/project/stopwords.txt', 'r')
stopwords = getStopWordList('static/project/stopwords.txt')

# getting the bag of words stored in static file
tot = open('static/bagofword.txt', 'r').read()
totalbagofwords = eval(tot)



#processing the status here and finding the usermap i.e bag of words of the user
#getting each status of the user and pre processing it using processStatus and getFeatureVector functions
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
    return usermap

# getting the actual feature vectors that is input to the model using the usermap(BOW of user)
def getFeatures(usermap):

    if (len(usermap)<10):
        feature = [0]
        return feature
    # calculating the tf-idf values here
    else:
        maxcount = {}
        for i in usermap:
            if i not in maxcount:
                maxcount[i] = 0
            maxcount[i] = max(maxcount[i], usermap[i])

        feature = [.5 + .5 * usermap[j] / (0 if j not in maxcount else maxcount[j])  if j in usermap else 0 for j in totalbagofwords]
        return feature

# controllers
#that defines what to do when a link is clicked
#render_template function render the html templates
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/<userid>")
def result_sec(userid):
    myUser = Users.query.filter_by(userID=userid).first()
    return render_template('index.html', myUser=myUser, wordlist=eval(myUser.wordList))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

@app.route("/privacy")
def privacy():
    return render_template('privacy.html')

@app.route("/tos")
def tos():
    return render_template('tos.html')

# No cacheing at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response
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
    session.clear()
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):

    next_url = request.args.get('next') or url_for('index')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)

    session['logged_in'] = True
    session['oauth_token'] = (resp['access_token'], '')

    # getting the user public profile
    getme = facebook.get('/me')
    me = getme.data

    # getting the user's recent 1000 posts
    getposts = facebook.get('/me/posts?limit=1000')
    if getposts.status == 200:
        data = getposts.data
    else:
        getposts =None
        flash('Unable to load the posts from facebook.')

    # getting the user's profile picture
    user_photo = facebook.get('/me/picture?type=large&redirect=false').data
    photo_url = user_photo['data']['url']
    session['url'] = photo_url
    posts = [] #to store the user's statuses only

    # getting user name
    if 'id' in me and 'name' in me:
        user_id = int(me['id'])
        user_name = str(me['name'].encode('utf-8'))

    # getting user status only from all the posts
    print 'data', data
    for i in data['data']:
        for k in i:
            if k == 'message':
                msg = i['message']
                posts.append(str(msg.encode('utf-8')))


    usermap = getStatus(posts)
    feature = getFeatures(usermap)
    #testpca = decomposition.PCA(n_components = 10).fit(feature)
    #Xt = testpca.transform(feature)
    if len(feature) < 2:
        opn=con=ext=agr=neu=[1,0]
    else:
        opn = svm_Model(X, y[0], feature)
        con = svm_Model(X, y[1], feature)
        ext = svm_Model(X, y[2], feature)
        agr = svm_Model(X, y[3], feature)
        neu = svm_Model(X, y[4], feature)


    check_user = Users.query.filter_by(userID=str(user_id)).first()

    if not check_user:
        new_user = Users(str(user_id), me['name'], int(opn[0]), int(con[0]), int(ext[0]), int(agr[0]), int(neu[0]), int(len(usermap)), str(usermap))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('result_sec', userid=str(user_id)))
    else:
        check_user.opn = int(opn[0])
        check_user.con = int(con[0])
        check_user.ext = int(ext[0])
        check_user.agr = int(agr[0])
        check_user.neu = int(agr[0])
        check_user.wordCount = int(len(usermap))
        check_user.wordList = str(usermap)
        db.session.commit()
        return redirect(url_for('result_sec', userid=str(user_id)))


@app.route("/logout")
def logout():
    pop_login_session()
    session.clear()
    return redirect(url_for('index'))




# launch
if __name__ == "__main__":
    db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
