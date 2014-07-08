import mechanize
from local import URI, ADMIN_USERNAME, ADMIN_PASSWORD

class ZNCServer():

    def __init__(self, admin_username=ADMIN_USERNAME, admin_password=ADMIN_PASSWORD, uri=URI):
        """ Initialize a mechanize Browser object and login as an admin """

        # Create a mechanize Browser ob
        #TODO(asmacdo) specific factory required?
        self.br = mechanize.Browser(factory=mechanize.RobustFactory())

        # Ignore the robots.txt file
        self.br.set_handle_robots(False)

        # Login to the webadmin
        self.br.open(uri)
        self.br.select_form(nr=0)
        self.br.form['user'] = admin_username
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
        """ Add a user
         :param username will be used both as the username for ZNC and the
                         NICK for IRC
         :param password
         """

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