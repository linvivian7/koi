$(document).ready(function() {

    function showOptimization(results) {
        console.log(results);
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

    $('#optimization-form').on('reset', function(evt) {
        $("#second-statement").remove();
        $("#third-statement").remove();
        $("#optimization-form li").remove();
        $("br").remove();
        $('#run-optimize').attr('disabled', 'disabled');
    });

    // Show ratio when program fields are filled out
    $("#goal-program").on("change", function() {
        
        $("#optimization-form li").remove();
        $("br").remove();
        $("#second-statement").remove();
        $("#third-statement").remove();
        $('#run-optimize').attr('disabled', 'disabled');
        var shownGoalProgram = $("#goal-program").val();

        try {
            var goalProgram = document.querySelector("#all-programs option[value='"+shownGoalProgram+"']").dataset.value;
            var formValues = {
                "goal_program": goalProgram,
            };

            $.get("/optimize", formValues, function(results) {

                console.log(1);
                console.log(results);
                if (results) {
                    $("#first-statement").after("<h5 id='second-statement'> You currently have "+results.display_program.balance.toLocaleString()+" points with "+results.display_program.program_name+".</h5>");

                    if (results.outgoing) {
                        $("#reset-optimize-btn").before("<h5 id='third-statement'> The program(s) listed below are your point source(s).</h5>");
                        $("#run-optimize").removeAttr('disabled');
                        
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
                                                            "</li><br>");
                        }
                    } else {
                        $("#second-statement").after("<h5 id='third-statement'>You currently have no transferable points.</h5>");
                    }
                }
            });
                
        } catch(err){}

    });

    $("#optimization-form").on('submit', optimizeTransfer);

} );
