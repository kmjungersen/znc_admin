#WARNING
=-=-=-=-=-=-=-=-=--=-=

THIS BRANCH IS IN DEVELOPMENT AND IS CURRENTLY __NOT__ OPERATIONAL!

=-=-=-=-=-=-=-=-=--=-=


### Registering with the COS IRC Network
For future reference, all of the links to these services are [here](http://107.170.134.161:5000/).

1. Register a username [here](http://107.170.134.161:5000/register)
    * Note: This username should ideally be registered (or available to register) with the NickServ on IRC.  This is how your name will be displayed, so **make it something logical!!!** Some clients, including Kiwi are capable of logging you into NicServ as well if you make this the same password.

2. Log into IRC. You can use your favorite client if you would like, but we have a browser based service (Kiwi) running [here](http://107.170.134.161:7778/). Use the Nick and password you just registered. If you would like to user a different client, see below for more details. 

3. Chat away!!!  It's recommended to bookmark these links and that you review some IRC basics below. 


### IRC Basics
Note: please add to this!

* Join channels like so:

`/join #cos`

* You can create channels with any name you like!  (If you aren't familiar with IRC, channels function just like chat rooms.) Creating a channel is the same syntax as joining:

`/join #my_really_cool_new_channel_name`

* We are using ZNC which is a bouncer service. When you create an account, ZNC logs into IRC. What does that mean??  It means while you're not actively logged into an IRC channel, ZNC will be logged in for you, and will give you a history of messages you missed while not logged in.  It's pretty cool! 
* You can change your bouncer settings here (including changing your password): [Web admin console](https://107.170.134.161:5001)

* Register your nick with Freenode's NickServ. This username will belong reserved for you on the freenode network

`/msg NickServ REGISTER <password> <email>`

* /msg <username> opens a private message with that person. Kiwi also allows you to click a user and chat with them directly. This Essentially opens a new channel that is just a chat between the two of you.

NickServ will send you an email. Follow those instructions to complete the registration.

* If you join or leave a channel in Kiwi, ZNC will also join or leave. If you want ZNC to stay and listen while you are away, simply close your browser tab or logout without leaving the rooms.
        

###Alternate Configurations

*  Pointing your IRC client to the ZNC bouncer is different based on the client. The basic details you need:

    |Network name: | anything you want!|
    |server:| 107.170.134.161|
    |port:| 5001|
    |SSL:| yes|

    * Nickname and Login name are the ones you just registered, as well as the server password.

    * Nickserv Password: this only applies if you've registered your Nick with Freenode's NickServ
        * If you've already registered with NickServ, you should use that to log in.

    * Some clients require that you change settings via IRC commands:
        `/server 107.170.134.161 +5001 username:password`
The server is using SSL. For some clients, this is indicated by the '+'. You may need to add to the command otherwise.
