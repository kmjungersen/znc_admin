### Registering with the COS IRC Network

* Register a username [here](http://107.170.134.161:5000)
    * Note: This username should ideally be registered (or available to register) with the NickServ on IRC.  This is how your name will be displayed, so **make it something logical!!!**

*  Login to IRC using the client of your choice. We will be adding a KIWI client shortly.  Pointing your IRC client to the ZNC bouncer is different based on the client.
    
    |Limechat|  |
    |-------|-------|
    |Network name: | anything you want!|
    |server:| 107.170.134.161|
    |port:| 5001|
    |SSL:| yes|

    * Nickname and Login name are the ones you just registered, as well as the server password.

    * Nickserv Password: this only applies if you've registered your Nick with Freenode's NickServ
        * If you've already registered with NickServ, you should use that to log in.

    * Other clients (including KIWI):
            /server 107.170.134.161 +5001 username:password

* Join channels like so:

    `/join #cos`

    * You can create channels with any name you like!  (If you aren't familiar with IRC, channels function just like chat rooms.)

    `/join #my_really_cool_new_channel_name!`

* You can configure your settings via the webadmin interface. Here you can add channels other than #cos to be bounced.
    * *What does that mean??*  It means while you're not actively logged into an IRC channel, ZNC will be logged in for you, and will give you a history of messages you missed while not logged in.  It's pretty cool!
    * [Web admin console](https://107.170.134.161:5001)

* Register your nick with Freenode's NickServ. This username will belong reserved for you on the freenode network

        /msg NickServ <password> <email>

