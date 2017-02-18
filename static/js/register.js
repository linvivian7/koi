$(document).ready(function() {

    function validateForm() {

        jQuery.validator.setDefaults({
            debug: true,
            success: "valid"
        });

        $('#signup-form').validate({

            // Specify validation rules
            rules: {
                password: {
                    minlength: 6
                },
            },

            // Specify validation error messages
            messages: {
                password: {
                    minlength: "Your password must be at least 6 characters long"
                }
            },

            submitHandler: function(form)
             {
                form.submit();
             }
        });
    }

    $('#signup-form').on('keyup', function() {
        var minLength = $('#signup-form').valid();

        // if neither fields are valid
        if (minLength) {
            $('#submit-signup-btn').css('margin-top', '0.4em');
            $('#submit-signup-btn').removeAttr('disabled');
        } else {
            $('#submit-signup-btn').css('margin-top', '-0.8em');
            $('#submit-signup-btn').attr('disabled', 'disabled');
        }
    });


    validateForm();

});