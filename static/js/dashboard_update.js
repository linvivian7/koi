$(document).ready(function() {

  // Toggle between transfer and update forms

  $(".toggle-btn").on('click', function () {
    $("#balance-form-section").toggle();
    $("#transfer-form-section").toggle();
    $(".toggle-btn").toggle();
  });

  // Loading and updating program balance table //

  function loadBalances() {

        $.get( "/balances.json", function(data) {
            var table = $("#program-balance");
            var userData = [];

            for(var i in data){
                userData.push(data[i]);
            }

            table.dataTable({
                "rowId": 'program_id',
                "deferRender": true,
                "select": true,
                "data": userData, // array with the data objects
                "columns": [
                    { "data": "index", "title": "", "class": "dt-body-center index no-space"},
                    { "data": null, "class": "no-space", "defaultContent": "<button type=button' class='btn btn-danger'><i class='fa fa-times' aria-hidden='true'></i></button>"},
                    { "data": "vendor", "title": "Vendor", "class": "dt-left expand-width" },
                    { "data": "program", "title": "Program", "class": "dt-left expand-width" },
                    { "data": "balance", "title": "Current Balance", "class": "dt-body-right expand-width current-balance", "type": "formatted-num" },
                    { "data": "timestamp", "title": "Timestamp", "class": "dt-right updated-at",  "type":'datetime', "format":'dddd D MMMM YYYY',},
                ],
                "columnDefs": [{
                    "targets": 5,
                        "data": "timestamp",
                        "render": function (data, type, full, meta) {
                            return moment(data).format('M/D/YYYY, h:mm a');
                    },
                },
                ],

                initComplete: function () {
                    this.api().columns([2, 3, 4]).every( function () {
                        var column = this;
                        var select = $('<select><option value=""></option></select>')
                            .appendTo( $(column.footer()).empty() )
                            .on( 'change', function () {
                                var val = $.fn.dataTable.util.escapeRegex(
                                    $(this).val()
                                );
         
                                column
                                    .search( val ? '^'+val+'$' : '', true, false )
                                    .draw();
                            } );
         
                         column.data().unique().sort().each( function ( d, j ) {
                            if(column.search() === '^'+d+'$'){
                                select.append( '<option value="'+d+'" selected="selected">'+d+'</option>' );
                            } else {
                                select.append( '<option value="'+d+'">'+d+'</option>' );
                            }
                        } );
                    } );
                }
            });

            $('#program-balance').on( 'click', 'button', removeBalance);

            function removeBalance() {

              if (confirm("Delete this program balance?") === true) {
                var $this = $(this);
                var trId = $this.closest('tr').prop('id');

                var data = {
                  "program_id": $this.closest('tr').prop('id')
                };

                $.post("/remove-balance", data, function(results) {
                  $('#'+trId+"").remove();
                });
              }
            }

            table.show();
            new $.fn.dataTable.FixedHeader(table,{});
            new $.fn.dataTable.ColReorder(table,{});

            $("#update-balance-form").on('submit', updateBalance);
            $("#update-balance-form").on('reset', clearFields);

            function clearFields() {
                $("#update-balance-form li").addClass('es-visible');
                $("#update-balance-form li").css("display","block");
              }

            // Update Balance Form //
            var updateProgram = -1;

            $('#program').editableSelect({ effects: 'slide' })
                         .on('select.editable-select', updateProgramVar);

            function updateProgramVar(e, li) {
              updateProgram = li.val();
            }

            // End Update Balance Form //

            function updateBalance(evt) {
                evt.preventDefault();

                try {
                  var formValues = {
                    "program": updateProgram,
                    "balance": $("#current-balance").val()
                  };

                  $.post("/update-balance", formValues).success(appendNew).fail(alertUser);
                } catch(err) {
                }

                $('#update-balance-form')[0].reset();
                $("#transfer-form li").addClass('es-visible');
                $("#transfer-form li").css("display","block");
                updateProgram = -1;
            }

            function alertUser() {
                $("#update-balance-form").after("<div class='alert alert-warning alert-message'>Please select a valid program. </div>");

                setTimeout(function() {
                  $(".alert-message").fadeOut();
                }, 2000);
            }

            function appendNew(data) {
                if ($("#program-balance").text().indexOf(data.program_name) == -1) {

                  var index = parseInt($("#program-balance tr:last td.index").html(),10);

                  // When there are no programs on the table
                  if (isNaN(index)) {
                    index = 1;
                    $("#program-balance tr:last").after('<tr id='+data.program_id+
                                                        ' role="row" class="even">'+
                                                        '<td class="dt-body-center sorting_1">'+index+'</td>'+
                                                        '<td class=" dt-left">'+data.program_name+'</td>'+
                                                        '<td class=" dt-body-right expand-width current-balance">'+data.current_balance.toLocaleString()+'</td>'+
                                                        '<td class=" dt-right updated-at">'+moment().format('M/D/YYYY, h:mm a')+'</td>'+
                                                        '<td class=" dt-body-center">16</td></tr>');
                  } else {
                    $("#program-balance tr:last").after('<tr id='+data.program_id+
                                                        ' role="row" class="even">'+
                                                        '<td class="dt-body-center sorting_1">'+(index + 1)+'</td>'+
                                                        '<td class=" dt-left">'+data.program_name+'</td>'+
                                                        '<td class=" dt-body-right expand-width current-balance">'+data.current_balance.toLocaleString()+'</td>'+
                                                        '<td class=" dt-right updated-at">'+moment().format('M/D/YYYY, h:mm a')+'</td>'+
                                                        '<td class=" dt-body-center">16</td></tr>');                  }

                } else {
                  $("#" + data.program_id + " td.current-balance").html(data.current_balance.toLocaleString());
                  $("#" + data.program_id + " td.updated-at").html(moment(data.updated_at).format('M/D/YYYY, h:mm a'));
              }
            }
        });
    }

    loadBalances();

    // End loading and updating program balance table //

} );
