$(document).ready(function() {

    // Setup - add a text input to each footer cell
    $('#transaction-history tfoot th').each( function () {
        var title = $(this).text();
        if (title !== ""){
            $(this).html( '<input type="text" class="'+title+'-search" placeholder="Search '+title+'" />' );
        }
    } );
 
    // DataTable
    var table = $('#transaction-history').DataTable();
 
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
} );

