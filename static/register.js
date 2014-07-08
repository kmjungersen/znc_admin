$(function() {

    console.log('Page loaded.');

    var SERVER = null;
    var LOCALHOST = null;
    var USERNAME_CHARACTERS = null;
    var PASSWORD_CHARACTERS = null;

    $.ajax({
        type: "GET",
        url: "/register/config/",
        success: function (data) {
            SERVER =  data.URI+':'+data.REGISTER_PORT;
            LOCALHOST = 'http://127.0.0.1:'+data.REGISTER_PORT;
            USERNAME_CHARACTERS = data.USERNAME_CHARACTERS;
            PASSWORD_CHARACTERS = data.PASSWORD_CHARACTERS;
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.log("failed!!!");
            console.log(jqXHR.status);
        }
    });

    $( "form" ).submit(function(event) {

        event.preventDefault();

        //Variable Declarations

        var username = $( "#username" ).val();
        var password = $( "#pwd1" ).val();
        var verify_password = $( "#pwd2").val();

        var usernameArray = username.split("");
        var passwordArray = password.split("");

        var userCheck = true;
        var passCheck = true;
        var check = true;
        var errors = [];

        if (!(password === verify_password)) {

            check = false;
            errors.push("Error: Passwords do not match");
        }

        if ((username.length < 6) || (username.length > 16)) {

            check = false;
            errors.push("Error: Username length is not within limits");
        }

        if (password.length < 6) {

            check = false;
            errors.push("Error: Password length is not within limits");
        }

        $.each (usernameArray, function( value ) {

            if (!(USERNAME_CHARACTERS.indexOf(usernameArray[value]) >= 0)) {
                userCheck = false;
            }
        });

        if (userCheck === false) {

            check = false;
            errors.push("Error: Invalid character(s) in username");
        }

        $.each (passwordArray, function( value ) {

            if (!(PASSWORD_CHARACTERS.indexOf(passwordArray[value]) >= 0)) {
                passCheck = false;
            }
        });

        if (passCheck === false) {

            check = false;
            errors.push("Error: Invalid character(s) in password");
        }

        if (check) {

            var info = "{ \"username\" : \"" + username + "\" , "
                    + " \"password\" : \"" + password + "\" }";

            var Sock = new SockJS(LOCALHOST);

            Sock.onopen = function () {

                console.log('Opened sock!');
                Sock.send(info);
            };

            Sock.onmessage = function (e) {
                // On incoming messages
                if (!(e.data.charAt(0) === '{')) {

                    // Message recieved, sock needs to be closed
                    // ASAP to leave the line open
                    Sock.close();

                    // On success
                    if (e.data.charAt(0) === 'S') {
                        alert(e.data);
                        $("#status").text("");
                        //redirect to homepage
                        window.location.href = "/";
                    // On fail
                    } else { $("#status").text(e.data); }
                }
            };

            Sock.onclose = function () {

                console.log('disconnected.');
                Sock = null;

            };

        }

        else {
            $( "#status").html(errors.join("</br>"));
        }

    }); //form submission

}); //on page load