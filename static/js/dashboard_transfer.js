$(document).ready(function() {

  // Transfer Balance Form //
  var outgoingProgram = -1;
  var receivingProgram = -1;

  $('#outgoing').editableSelect({ effects: 'slide' })
                .on('select.editable-select', updateOutgoingProgram)
                .on('select.editable-select', removeReceiving)
                .on('select.editable-select', getReceiving);

  // End Transfer Balance Form //

    function getReceiving() {
     try {
          var formValues = {
              "outgoing": outgoingProgram,
          };

          $.get("/ratio.json", formValues, function(results) {
              if (results) {
                  var programIds = results["program_id"],
                      programNames = results["program_name"];

                  for (i = 0; i < programIds.length; i++) {
                      $("#receiving").append("<option class='remove' value="+programIds[i]+">"+programNames[i]+"</option>");
                  }

              $('#receiving').editableSelect({ effects: 'slide' })
                             .on('select.editable-select', updateReceivingProgram)
                             .on('select.editable-select', getRatio);
              }
          });
              
      } catch(err){}
 
    }

    function getRatio() {

      try {
        var formValues = {
          "outgoing": outgoingProgram,
          "receiving": receivingProgram,
            };

        var request = $.get("/ratio.json", formValues, function(results) {
          if (results) {
                $("#ratio").html("Ratio: " + results);
                $("#ratio").show();
              }
            });
        $("#transfer-form").on('reset', removeReceiving);
      } catch (err) {
        $("#ratio").hide();
      }
    }


    function updateReceivingProgram(e, li) {
      receivingProgram = li.val();
    }

    function updateOutgoingProgram(e, li) {
      outgoingProgram = li.val();
    }

    function updateBalanceTransfer(results) {

        if ((results === "Not enough outstanding points for this transfer") || (results === "Please enter a transferable amount. See ratio above")) {
            alert(results);
            $('#transfer-form')[0].reset();
        } else{
            if (($("#program-balance").text().indexOf(results.outgoing.program_name) == -1 && $("#program-balance").text().indexOf(results.receiving.program_name) == -1)) {
                window.location.reload();
            } else if ($("#program-balance").text().indexOf(results.outgoing.program_name) != -1) {
                $("#" + results.outgoing.program_id + " td.current_balance").html(results.outgoing.current_balance.toLocaleString());
                $("#" + results.outgoing.program_id + " td.updated_at").html(moment(results.outgoing.updated_at).format('M/D/YYYY, h:mm a'));

                if ($("#program-balance").text().indexOf(results.receiving.program_name) != -1) {
                    $("#" + results.receiving.program_id + " td.current_balance").html(results.receiving.current_balance.toLocaleString());
                    $("#" + results.receiving.program_id + " td.updated_at").html(moment(results.receiving.updated_at).format('M/D/YYYY, h:mm a'));
                }
            }
        }
    }

  function transferBalance(evt) {
      evt.preventDefault();

      try {
          var formValues = {
              "outgoing": outgoingProgram,
              "receiving": receivingProgram,
              "amount": $("#transfer-amount").val()
            };

          $.post("/transfer-balance", formValues, updateBalanceTransfer);
      }
      catch(err) {
        alert("Please enter a valid loyalty program");
      }
      $('#transfer-form')[0].reset();
  }


  function removeReceiving() {
    $('#receiving').editableSelect('destroy');
    $('.remove').remove();
  }

  $("#transfer-form").on('submit', transferBalance);

} );
