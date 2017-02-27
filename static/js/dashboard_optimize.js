$(document).ready(function() {

    // Optimize Balance Form //

    var goalProgram = -1;
    var i = 0;

    function changeGoal (e, li) {
        console.log(1);
        try {
            goalProgram = li.val();
        } catch(err) {}
    }

    $('#goal-program').editableSelect()
                      .on('select.editable-select', changeGoal)
                      .on('select.editable-select', listDetails);
    $('#goal-program').editableSelect({ effects: 'slide' });
    // End Update Balance Form //

    function showOptimization(results) {
        $("#run-optimize").removeAttr('disabled');
        $('#optimization-form').on('reset', removeElements);

        $("#optimization-results").after("<h5 class='to-remove results' id='results-message'>"+results.message+"</h5>");

        if ((results.message !== "You do not have enough points to achieve your goal.") && (results.message != "You've already achieved your goal.")) {
            for (var transfer in results.path) {
                if (results.path.hasOwnProperty(transfer)) {

                    var transferred = (results.path[transfer].amount * (results.path[transfer].numerator / results.path[transfer].denominator)).toLocaleString();

                    $("#optimization-results").append("<h5 class='to-remove results'>"+
                                                      transfer+
                                                      "Transfer "+
                                                      results.path[transfer].amount.toLocaleString()+
                                                      " points from "+
                                                      results.path[transfer].outgoing+
                                                      " at "+
                                                      results.path[transfer].denominator+
                                                      " : "+
                                                      results.path[transfer].numerator+
                                                      " ratio to "+
                                                      transferred+
                                                      " points at "+
                                                      results.path[transfer].receiving+
                                                      ".</h5>");
              }
            }
            $("#optimization-results").after("<h5 id='statement-6' class='to-remove results'> Would you like to commit this transfer?</h5>"+
            "<button type='button' class='btn btn-primary btn-sm to-remove results' id='yes-btn'>Yes</button><br class='to-remove results'>");

            $('#optimization-form').on('reset', removeElements);
            $("#yes-btn").on('click', commitTransfer);

            $("#optimization-form").on('submit', function () {
                $(".results").remove();
            });
        }

    }

    function showConfirmation(results) {
        $('#optimization-form').on('reset', removeElements);

        $("#results-message").after("<h5 class='to-remove' id='transfer-confirmation'>"+results.confirmation+"</h5>");
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
    }

    $('#optimization-form').on('reset', removeElements);

    function listDetails() {
        console.log(2);
        removeElements();

        try {
            var formValues = {
                "goal_program": goalProgram,
            };

            $.get("/optimize", formValues, function(results) {
                if (results) {

                    $("#goal-program").after("<h5 id='statement-2' class='to-remove'> You currently have "+results.display_program.balance.toLocaleString()+" points with "+results.display_program.program_name+".</h5>");

                    if (results.outgoing) {
                        $("#run-optimize").removeAttr('disabled');
                        
                        $("#reset-optimize-btn").before('<div class="form-group row"><label class="col-2 col-form-label to-remove" for="goal-amount">'+
                                                        '<h5 class="to-remove" id="statement-3"> Please enter your goal for this account</h5></label><br class="to-remove">'+
                                                        '<div class="col-10"><input class="form-control to-remove" type="number" name="amount" id="goal-amount" min="1" max="1000000000" maxlength="10" placeholder="Goal Points" required>'+
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
