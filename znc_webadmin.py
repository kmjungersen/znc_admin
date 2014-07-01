import mechanize

# URI of ZNC server webdmin access
URI = "https://107.170.134.161:5001/"

class ZNCServer():

    def __init__(self, username, admin_password, uri=URI):
        """ Initialize a mechanize Browser object and login as an admin """

        # Create a mechanize Browser ob
        #TODO(asmacdo) specific factory required?
        self.br = mechanize.Browser(factory=mechanize.RobustFactory())

        # Ignore the robots.txt file
        self.br.set_handle_robots(False)

        # Login to the webadmin
        self.br.open(uri)
        self.br.select_form(nr=0)
        self.br.form['user'] = username
        self.br.form['pass'] = admin_password
        self.br.submit()

    @property
    def users(self):
        """
        :return: list of users
        """
        self.br.follow_link(text="List Users")

        return [link.url[14:] for link in self.br.links()
                if link.url.startswith("adduser?clone=")]

    def add_user(self, username, password):
        """ Add a user """

        resp = self.br.follow_link(text="Add User")
        # Clean up bad HTML
        resp.set_data(self.br.response().read().replace('datalist', 'select'))
        self.br.set_response(resp)

        # User info
        self.br.select_form(nr=0)
        self.br.form['user'] = self.br.form['nick'] = username
        self.br.form['altnick'] = username
        self.br.form['ident'] = self.br.form['realname'] = username
        self.br.form['password'] = self.br.form['password2'] = password
        self.br.find_control("modargs_webadmin").selected=True
        self.br.submit()

        # Add Network
        self.br.follow_link(text="List Users")
        self.br.follow_link(url="edituser?user=" + username)
        resp = self.br.follow_link(url="addnetwork?user=" + username)
        resp.set_data(self.br.response().read().replace('datalist', 'select'))
        self.br.set_response(resp)
        self.br.select_form(nr=0)
        self.br.form['network'] = "freenode"
        self.br.form['nick'] = self.br.form['altnick'] = username
        self.br.form['ident'] = self.br.form['realname'] = username
        self.br.form['servers'] = "holmes.freenode.net 6667"
        self.br.submit()

        # Add channel
        self.br.follow_link(url="editnetwork?user=" +
                            username + "&network=freenode")
        self.br.follow_link(url="addchan?user=" + username +
                            "&network=freenode")
        self.br.select_form(nr=0)
        self.br.form['name'] = "#cos"
        self.br.submit()