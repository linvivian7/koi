$(document).ready(function() {

    function showOptimization(results) {
        console.log(results.path);
        // debugger;
        $("#run-optimize").removeAttr('disabled');

        for (var transfer in results.path) {
            if (results.path.hasOwnProperty(transfer)) {
                $("#optimization-results").append("<h5 class='to-remove'>"+results.path[transfer].outgoing+results.path[transfer].receiving+results.path[transfer].amount+results.path[transfer].denominator+"</h5>");
            console.log(transfer + " -> " + results.path[transfer].outgoing);
          }
        }
    }

    function optimizeTransfer(evt) {
        evt.preventDefault();

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
