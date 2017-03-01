$(document).ready(function() {

    $(".menu-toggle").on('click', function () {
        $(".menu-toggle").toggle();
      });

    $("[href]").each(function() {
        if (this.href == window.location.href) {
            $(this).addClass("active");
        }
    });

    function loadTransactions() {

        $.get( "/activity.json", function(data) {
            var table = $("#transaction-history");
            var userData = [];

            for(var i in data){
                userData.push(data[i]);
            }

            table.dataTable({
                "dom": '<"top"lf>rt<"bottom"ip><"clear">',
                "deferRender": true,
                "select": true,
                "data": userData, // array with the data objects
                "columns": [
                    { "data": "index", "title": "", "class": "dt-body-center"},
                    { "data": "type", "title": "Type", "class": "dt-center"},
                    { "data": "program", "title": "Program" },
                    { "data": "beginning", "title": "Beginning Balance", "class": "dt-body-right expand-width", "type": "formatted-num" },
                    { "data": "change", "title": "Change", "class": "dt-body-right expand-width", "type": "formatted-num" },
                    { "data": "ending", "title": "Ending Balance", "class": "dt-body-right expand-width", "type": "formatted-num" },
                    { "data": "timestamp", "title": "Timestamp", "class": "dt-right",  "type":'datetime', "format":'dddd D MMMM YYYY',},
                ],
                "columnDefs": [{
                    "targets": 6,
                        "data": "timestamp",
                        "render": function (data, type, full, meta) {
                            return moment(data).format('M/D/YYYY, h:mm a');
                    }
                },
                ],

                initComplete: function () {
                    this.api().columns([1, 2, 3, 4, 5]).every( function () {
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

            table.show();

            new $.fn.dataTable.FixedHeader(table,{
            });

            new $.fn.dataTable.ColReorder(table,{
            });

        });
    }

    loadTransactions();
});