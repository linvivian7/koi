$(document).ready(function() {

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
        var shownGoalProgram = $("#goal-program").val();

        try {
            var goalProgram = document.querySelector("#all-programs option[value='"+shownGoalProgram+"']").dataset.value;
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

        var shownGoalProgram = $("#goal-program").val();

        try {
            var goalProgram = document.querySelector("#all-programs option[value='"+shownGoalProgram+"']").dataset.value;
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
        $("#optimization-form li").remove();
        $(".to-remove").remove();
        $('#run-optimize').attr('disabled', 'disabled');
    }

    $('#optimization-form').on('reset', removeElements);

    $("#goal-program").on("change", function() {
        
        removeElements();

        var shownGoalProgram = $("#goal-program").val();

        try {
            var goalProgram = document.querySelector("#all-programs option[value='"+shownGoalProgram+"']").dataset.value;
            var formValues = {
                "goal_program": goalProgram,
            };

            $.get("/optimize", formValues, function(results) {

                if (results) {

                    $("#all-programs").after("<h5 id='statement-2' class='to-remove'> You currently have "+results.display_program.balance.toLocaleString()+" points with "+results.display_program.program_name+".</h5>");

                    if (results.outgoing) {
                        $("#run-optimize").removeAttr('disabled');
                        
                        $("#reset-optimize-btn").before("<label for='goal-amount'><h5 class='to-remove' id='statement-3'> Please enter your goal for this account</h5></label><br class='to-remove'>"+
                                                        '<input type="number" name="balance" class="to-remove" id="goal-amount" min="1" max="1000000000" maxlength="10" placeholder="Goal Points" required></input><br class="to-remove">');

                        $("#reset-optimize-btn").before("<h5 id='statement-4' class='to-remove'> The program(s) listed below are your point source(s).</h5><br class='to-remove'>");

                        for (var program in results.outgoing) {
                            $("#reset-optimize-btn").before("<li id='"+
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

    });

    $("#optimization-form").on('submit', optimizeTransfer);

} );
