$(document).ready(function() {

    // LOGIN //

    function validateForm() {

        jQuery.validator.setDefaults({
            debug: true,
            success: "valid"
        });

        $('#login-form').validate({

            // Specify validation rules
            rules: {

                email: {
                    required: true,
                    email: true
                },
                password: {
                    required: true,
                }
            },

            // Specify validation error messages
            messages: {
                email: {
                    required: "Please enter your email address",
                    email: "Please enter a valid email address"
                },
                password: {
                    required: "Please provide a password",
                }
            }

        });
    }

    $('#login-form').on('keyup', function() {
        var validated = $('#login-form').valid();

        // if neither fields are valid
        if (($("#email-field").valid() === 0) && ($("#password-field").valid() === 0)) {
            $('#submit-login-btn').attr('disabled', 'disabled');
            $('#submit-login-btn').css('margin-top', '-0.8em');
            $('#password-field').css('margin-top', '-0.8em');

        // if both are valid
        } else if (validated) {
            $('#submit-login-btn').removeAttr('disabled');
            $('#submit-login-btn').css('margin-top', '0.4em');
            $('#password-field').css('margin-top', '0.8em');

        // if only email is valid
        } else if ($("#email-field").valid() === 1) {
            $('#submit-login-btn').attr('disabled', 'disabled');
            $('#submit-login-btn').css('margin-top', '-0.5em');
            $('#password-field').css('margin-top', '0.9em');

        // if only password is valid
        } else if ($("#password-field").valid() === 1) {
            $('#submit-login-btn').attr('disabled', 'disabled');
            $('#submit-login-btn').css('margin-top', '0.4em');
            $('#password-field').css('margin-top', '-0.8em');
        }
    });


    // Log in user
    function checkLogin(evt) {
        evt.preventDefault();

        var email = $("#email-field").val();
        var password = $("#password-field").val();

        var formValues = {
            "email": email,
            "password": password
        };
            $.post("/login", formValues, loginUser);
        }

    function loginUser(results) {
        if (results === "This email has not been registered" ||
            results === "This is not a valid email/password combination") {
                $('.modal-content').prepend("<div class='alert alert-warning' id='login-flash'>"+results+"</div>");
                $('#login-form #password-field').val("");

                setTimeout(function () {
                    $('.alert-warning').remove();}, 1000);
        } else {
            $(location).attr('href', '/dashboard');
        }
    }

    $("#submit-login-btn").on('click', checkLogin);

    $("#login-btn").on('click', validateForm);

    $("#dashboard-btn").on('click', function () {
        $(location).attr('href', '/dashboard');
    });

    // END LOGIN //


    // CONTACT US //

    $("#feedback-type").on('change', function() {
        $(".all-feedback").hide();
        
        var type = ".category-"+ $("#feedback-type").val();

        $(type).show();

        if (parseInt($("#feedback-type").val(), 10) > 0) {
            $("#submit-feedback-btn").show();
        }
    });


});