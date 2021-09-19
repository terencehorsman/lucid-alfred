from flask import Flask, render_template, request, redirect
from requests_oauthlib import OAuth1Session
import xml.etree.ElementTree as ET
import json

# global class to maintain LucidChart OAuth information.
class Lucid:
    def __init__(self) -> None:
        pass
    
    def authenticate(self, key, secret):
            # 1. OAuth endpoints given in the lucidchart API documentation
            self.request_token_url = 'https://www.lucidchart.com/oauth/requestToken'
            self.authorization_base_url = 'https://www.lucidchart.com/oauth/authorize'
            self.access_token_url = 'https://www.lucidchart.com/oauth/accessToken'
            self.key = key
            self.secret = secret

            # 2. Fetch a request token
            self.lucidchart = OAuth1Session(self.key, client_secret=self.secret,
                    callback_uri='http://127.0.0.1:5000/cb')
            self.lucidchart.fetch_request_token(self.request_token_url)

            # 3. Redirect user to lucidchart for authorization
            authorization_url = self.lucidchart.authorization_url(self.authorization_base_url)
            return authorization_url

    def update_xml(self, redirect_response):
            # 4. Get the authorization verifier code from the callback url
            self.redirect_response = redirect_response
            self.lucidchart.parse_authorization_response(self.redirect_response)

            # 5. Fetch the access token
            token = self.lucidchart.fetch_access_token(self.access_token_url)

            # 6. Fetch a protected resource, i.e. user profile
            r = self.lucidchart.get('https://lucid.app/documents/docs')
            xml = '<xml> ' + str(r.content) +  ' </xml>'
            f = open( 'documents.xml', 'w' )
            f.write(xml)
            f.close()

    def update_json(self):
            data = []
            column_names = ["name", "href"]

            # initialise the xml file
            tree = ET.parse('documents.xml')
            root = tree.getroot()

            title = ''
            editUrl = ''

            # Loop for variables required
            for child in root.iter('*'):
                    if child.tag == 'title':
                            title = child.text
                    if child.tag == 'editUrl':
                            editUrl = child.text
                            data.append({'name': title, 'href': editUrl})

            jsonStr = '{  "links": ' + json.dumps(data) + " }"
            file = open("links.json", "w")
            file.write(jsonStr)
            file.close


# flask application initialisation
app = Flask(__name__)
app.lucid_session = Lucid()

# method for when done with programme
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

#routing for home page
@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        key = request.form["key"]
        secret = request.form["secret"]
        return_url = app.lucid_session.authenticate(key, secret)
        return redirect(return_url)
    else:    
        return render_template("home.html")

# callback from OAuth API integration
@app.route("/cb", methods=['GET', 'POST'])
def callback():
    if request.method == 'GET':
        oauth_token = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')
        redirect_response = "http://127.0.0.1:5000/cb?oauth_token=" + oauth_token + "&oauth_verifier=" + oauth_verifier + "&oauth_origin="
        app.lucid_session.update_xml(redirect_response)
        app.lucid_session.update_json()
        return render_template("complete.html")
    else:
        # kill the app once done.
        shutdown_server()
        return 'Set up Complete. This tab can now be closed.'

if __name__ == "__main__":
    app.run()
