$(document).ready(function() {

    $("[href]").each(function() {
        if (this.href == window.location.href) {
            $(this).addClass("active");
        }
    });


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
                      vendorNames = results["vendor_name"],
                      programNames = results["program_name"];

                  for (i = 0; i < programIds.length; i++) {
                      $("#receiving").append("<option class='remove' value="+programIds[i]+">"+vendorNames[i]+" | "+programNames[i]+"</option>");
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
            $("#transfer-form").after("<div class='alert alert-warning alert-message'>"+results+".</div>");

            setTimeout(function() {
              $(".alert-message").fadeOut();
            }, 1000);
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

          $.post("/transfer-balance", formValues).success(updateBalanceTransfer).fail(alertUser);
      }
      catch(err) {
      }
      $('#transfer-form')[0].reset();
      $("#transfer-form li").addClass('es-visible');
      $("#transfer-form li").css("display","block");
      outgoingProgram = -1;
  }
  function alertUser() {
      $("#transfer-form").after("<div class='alert alert-warning alert-message'>Please select a valid program. </div>");

      setTimeout(function() {
        $(".alert-message").fadeOut();
      }, 1000);
  }

  function removeReceiving() {
    $("#ratio").hide();
    $('#receiving').editableSelect('destroy');
    $('.remove').remove();
    $("#transfer-form li").addClass('es-visible');
    $("#transfer-form li").css("display","block");
  }

  $("#transfer-form").on('submit', transferBalance);

} );
