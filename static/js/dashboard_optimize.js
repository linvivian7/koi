$(document).ready(function() {

    // function updateBalanceTransfer(results) {

    //     if ((results === "Not enough outstanding points for this transfer") || (results === "Please enter a transferable amount. See ratio above")) {
    //         alert(results);
    //         $('#transfer-form')[0].reset();
    //     } else{
    //         if (($("#program-balance").text().indexOf(results.outgoing.program_name) == -1 && $("#program-balance").text().indexOf(results.receiving.program_name) == -1)) {
    //             window.location.reload();
    //         } else if ($("#program-balance").text().indexOf(results.outgoing.program_name) != -1) {
    //             $("#" + results.outgoing.program_id + " td.current_balance").html(results.outgoing.current_balance.toLocaleString());
    //             $("#" + results.outgoing.program_id + " td.updated_at").html(moment(results.outgoing.updated_at).format('M/D/YYYY, h:mm a'));

    //             if ($("#program-balance").text().indexOf(results.receiving.program_name) != -1) {
    //                 $("#" + results.receiving.program_id + " td.current_balance").html(results.receiving.current_balance.toLocaleString());
    //                 $("#" + results.receiving.program_id + " td.updated_at").html(moment(results.receiving.updated_at).format('M/D/YYYY, h:mm a'));
    //             }
    //         }
    //     }
    // }

    // function transferBalance(evt) {
    //     evt.preventDefault();

    //     var shownOutgoing = $("#outgoing").val();
    //     var shownReceiving = $("#receiving").val();

    //     try {
    //         var outgoingId = document.querySelector("#all-outgoing-programs option[value='"+shownOutgoing+"']").dataset.value;
    //         var receivingId = document.querySelector("#all-receiving-programs option[value='"+shownReceiving+"']").dataset.value;
    //         var formValues = {
    //             "outgoing": outgoingId,
    //             "receiving": receivingId,
    //             "amount": $("#transfer-amount").val()
    //           };

    //         $.post("/transfer-balance", formValues, updateBalanceTransfer);
    //     }
    //     catch(err) {
    //       alert("Please enter a valid loyalty program");
    //     }
    //     $('#transfer-form')[0].reset();
    // }
    $('#optimization-form').on('reset', function(evt) {
        $("#second-statement").remove();
        $("#third-statement").remove();
        $("input[type='checkbox']").remove();
        $("label").remove();
        $("br").remove();
        $('#submit-optimize').attr('disabled', 'disabled');
    });

    // Show ratio when program fields are filled out
    $("#goal-program").on("change", function() {

        $("#second-statement").remove();
        $("#third-statement").remove();
        $('#submit-optimize').attr('disabled', 'disabled');
        var shownGoalProgram = $("#goal-program").val();

        try {
            var goalProgram = document.querySelector("#all-programs option[value='"+shownGoalProgram+"']").dataset.value;
            var formValues = {
                "goal_program": goalProgram,
            };

            $.get("/optimize", formValues, function(results) {
                if (results) {
                    $("#first-statement").after("<h5 id='second-statement'> I currently have "+results.display_program.balance.toLocaleString()+" points with "+results.display_program.program_name+".</h5>");

                    if (results.outgoing) {
                        $("#reset-optimize-btn").before("<h5 id='third-statement'> Select one or more from program(s) listed below to have as point source(s).</h5>");
                        $("#submit-optimize").removeAttr('disabled');
                        for (var program in results.outgoing) {
                            $("#reset-optimize-btn").before("<input type='checkbox' id='"+
                                                            program+
                                                            "' value='"+
                                                            program+
                                                            "'> <label for='"+
                                                            program+
                                                            "''>"+
                                                            results.outgoing[program]["program_name"]+
                                                            " (current balance: "+
                                                            results.outgoing[program]["balance"].toLocaleString()+
                                                            ")"+
                                                            "</label><br>");
                        }
                    } else {
                        $("#second-statement").after("<h5 id='third-statement'>You currently have no transferable points to "+shownGoalProgram+".</h5>");
                    }

                }
            });
                
        } catch(err){}

    });


    //   $("#receiving").on("change", function() {

    //     var shownOutgoing = $("#outgoing").val();
    //     var shownReceiving = $("#receiving").val();

    //     try{
    //       var outgoingId = document.querySelector("#all-outgoing-programs option[value='"+shownOutgoing+"']").dataset.value;
    //       var receivingId = document.querySelector("#all-receiving-programs option[value='"+shownReceiving+"']").dataset.value;
    //       var formValues = {
    //         "outgoing": outgoingId,
    //         "receiving": receivingId,
    //           };

    //       var request = $.get("/ratio-info", formValues, function(results) {
    //         if (results) {
    //               $("#ratio").html("Ratio: " + results);
    //               $("#ratio").show();
    //             }
    //           });
    //     } catch(err){
    //       $("#ratio").hide();
        // }
      // });

    // $("#transfer-form").on('submit', transferBalance);

} );
