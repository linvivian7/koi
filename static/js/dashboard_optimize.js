$(document).ready(function() {

    $(".menu-toggle").on('click', function () {
        $(".menu-toggle").toggle();
      });

    $("[href]").each(function() {
        if (this.href == window.location.href) {
            $(this).addClass("active");
        }
    });


    // Optimize Balance Form //
    var goalProgram = -1;
    var i = 0;

    function changeGoal (e, li) {
        try {
            goalProgram = li.val();
        } catch(err) {}
    }

    $('#goal-program').editableSelect({ effects: 'slide' })
                      .on('select.editable-select', changeGoal)
                      .on('select.editable-select', listDetails);
    // End Update Balance Form //

    function showOptimization(results) {
        $("#run-optimize").removeAttr('disabled');
        $('#optimization-form').on('reset', removeElements);

        if (results.message === "There are currently no known relationship between your goal program and those in your profile." || results.message === "You've already achieved your goal.") {
            $("#optimization-results").append("<div class='alert alert-warning to-remove results' id='results-message'>"+results.message+"</div>");
        } else {
            for (var transfer in results.path) {
                if (results.path.hasOwnProperty(transfer)) {

                    var transferred = (results.path[transfer].amount * (results.path[transfer].numerator / results.path[transfer].denominator)).toLocaleString();

                    $("#optimization-results").append("<h5 class='to-remove results results-color'>"+
                                                      transfer+
                                                      "Transfer "+
                                                      results.path[transfer].amount.toLocaleString()+
                                                      " point(s) from "+
                                                      results.path[transfer].outgoing+
                                                      " at "+
                                                      results.path[transfer].denominator+
                                                      " : "+
                                                      results.path[transfer].numerator+
                                                      " ratio to "+
                                                      transferred+
                                                      " point(s) at "+
                                                      results.path[transfer].receiving+
                                                      ".</h5>");
              }
            }

            $("#optimization-results").append("<div class='alert alert-warning to-remove results' id='results-message'>"+results.message+
                                              "<br class='to-remove results'></div>");

            $("#optimization-results").append("<br class='to-remove results'><button type='button' class='btn btn-info to-remove results' id='yes-btn'>Yes</button>");

            $('#optimization-form').on('reset', removeElements);
            $("#yes-btn").on('click', commitTransfer);

            $("#optimization-form").on('submit', function () {
                $(".results").remove();
            });
        }
    }

    function showConfirmation(results) {
        $('#optimization-form').on('reset', removeElements);

        $("#results-message").html(results.confirmation);
    }


    function commitTransfer() {

        try {
            var formValues = {
                "goal_program": goalProgram,
                "goal_amount": $("#goal-amount").val(),
                "commit": true,
              };

            $.post("/optimization.json", formValues, showConfirmation);
        }
        catch(err) {
          alert("Please enter a valid loyalty program");
        }
    }

    function optimizeTransfer(evt) {
        evt.preventDefault();
        $(".results").remove();

        try {
            var formValues = {
                "goal_program": goalProgram,
                "goal_amount": $("#goal-amount").val(),
              };

            $.post("/optimization.json", formValues, showOptimization);
        }
        catch(err) {
          alert("Please enter a valid loyalty program");
        }

        $('#run-optimize').attr('disabled', 'disabled');
    }

    function removeElements() {
        $(".to-remove").remove();
        $('#run-optimize').attr('disabled', 'disabled');
        $("#optimization-form li").addClass('es-visible');
        $("#optimization-form li").css("display","block");
    }

    $('#optimization-form').on('reset', removeElements);

    function listDetails() {
        removeElements();

        try {
            var formValues = {
                "goal_program": goalProgram,
            };

            $.get("/optimize", formValues, function(results) {
                if (results) {

                    $("#goal-program").after("<h5 id='statement-2' class='to-remove'> You currently have <span id='npoints'>"+results.display_program.balance.toLocaleString()+"</span> point(s) with "+results.display_program.program_name+".</h5>");

                    if (results.outgoing) {
                        $("#run-optimize").removeAttr('disabled');
                        
                        $("#reset-optimize-btn").before('<div class="form-group row to-remove"><label class="col-2 col-form-label to-remove" for="goal-amount">'+
                                                        '<h5 class="to-remove" id="statement-3"> Please enter your goal for this account</h5></label><br class="to-remove">'+
                                                        '<input class="form-control to-remove" type="number" name="amount" id="goal-amount" min="1" max="1000000000" maxlength="10" placeholder="Goal Points" required>'+
                                                        '<br class="to-remove"></div>');

                        $("#reset-optimize-btn").before("<h5 id='statement-4' class='to-remove'> The program(s) listed below are your point source(s).</h5><br class='to-remove'>");

                        for (var program in results.outgoing) {
                            $("#reset-optimize-btn").before("<li class='to-remove' id='"+
                                                            program+
                                                            "' value='"+
                                                            program+
                                                            "'>"+
                                                            results.outgoing[program]["program_name"]+
                                                            " (current balance: "+
                                                            results.outgoing[program]["balance"].toLocaleString()+
                                                            ")"+
                                                            "</li><br class='to-remove'>");
                        }

                        $('#optimization-form').on('reset', removeElements);
                    
                    } else {
                        $("#second-statement").after("<h5 id='statement-2' class='to-remove'>You currently have no transferable points.</h5>");
                    }
                }
            });
                
        } catch(err){}
    }

    $("#optimization-form").on('submit', optimizeTransfer);

} );
