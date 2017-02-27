$(document).ready(function() {

  // Update Balance Form //

  var updateProgram = -1;

  $('#program').editableSelect()
               .on('select.editable-select', function (e, li) {
                  updateProgram = li.val();
        });

  $('#program').editableSelect({ effects: 'slide' });
  // End Update Balance Form //


    // Setup - add a text input to each footer cell
    $('#program-balance tfoot th').each( function () {
        var title = $(this).text();

        if (title !== "") {
            $(this).html( '<input type="text" class="'+title+'-search" placeholder="Search '+title+'" />' );
          }
    });
 
    // DataTable
    var table = $('#program-balance').DataTable();
 
    // Apply the search
    table.columns().every( function () {
        var that = this;
        $( 'input', this.footer() ).on( 'keyup change', function () {
            if ( that.search() !== this.value ) {
                that
                    .search( this.value )
                    .draw();
            }
        } );
    } );

    function appendNew(data) {

        if ($("#program-balance").text().indexOf(data.program_name) == -1) {

          var index = parseInt($("#program-balance tr:last td.index").html(),10);

          if (isNaN(index)) {
            index = 1;
            $("#program-balance tr:last").after("<tr id="+data.program_id+"><td class='remove'><span class='glyphicon glyphicon-minus-sign'></span></td><td class='index'>"+(index)+"</td><td class='program_name'>"+data.program_name+"</td><td class='current_balance'>"+data.current_balance.toLocaleString()+"</td><td class='updated_at'>"+moment().format('M/D/YYYY, h:mm a')+"</td></tr>");
          } else {
            $("#program-balance tr:last").after("<tr id="+data.program_id+"><td class='remove'><span class='glyphicon glyphicon-minus-sign'></span></td><td class='index'>"+(index + 1)+"</td><td class='program_name'>"+data.program_name+"</td><td class='current_balance'>"+data.current_balance.toLocaleString()+"</td><td class='updated_at'>"+moment().format('M/D/YYYY, h:mm a')+"</td></tr>");
          }

          $("#"+data.program_id+" .remove").on('click', removeBalance);
        } else {
          $("#" + data.program_id + " td.current_balance").html(data.current_balance.toLocaleString());

          $("#" + data.program_id + " td.updated_at").html(moment(data.updated_at).format('M/D/YYYY, h:mm a'));

      }
    }

    function updateBalance(evt) {
        evt.preventDefault();

        try {
          var formValues = {
            "program": updateProgram,
            "balance": $("#current-balance").val()
          };

            $.post("/update-balance", formValues, appendNew);
        }
        catch(err) {
          console.log(formValues);
          alert("Please enter a valid loyalty program");
        }

        $('#update-balance-form')[0].reset();
    }

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

    $("#update-balance-form").on('submit',updateBalance);
    $("td.remove").on('click', removeBalance);
} );
