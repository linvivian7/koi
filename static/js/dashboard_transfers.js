$(document).ready(function() {

    $.get( "/transfers.json", function(data) {
        var table = $("#transfer-history");
        var userData = [];

        for(var i in data){
            userData.push(data[i]);
        }

        table.dataTable({
            "data": userData, // array with the data objects
            "columns": [
                { "data": "transfer_id", "title": "id" },
                { "data": "outgoing", "title": "From" },
                { "data": "outgoing_amount", "title": "Transferred Amount", "class": "center", "type": "numeric-comma" },
                { "data": "ratio", "title": "Ratio", "class": "center" },
                { "data": "receiving", "title": "To", "class": "center" },
                { "data": "receiving_amount", "title": "Received Amount", "class": "center" },
                { "data": "timestamp", "title": "Timestamp", "class": "center",  "type":'datetime', "format":'dddd D MMMM YYYY',},
            ],

            "language": {
                "thousands": ",",
            },

            "columnDefs": [{
                "targets": 6,
                    "data": "timestamp",
                    "render": function (data, type, full, meta) {
                        return moment(data).format('M/D/YYYY, h:mm a');
                }
            },
                {
                 "targets": 2,
                    "data": "outgoing_amount",
                    "render": function (data, type, full, meta) {
                        return data;
                }
            }]
        });

        table.show();

        new $.fn.dataTable.FixedHeader(table,{
        });

        new $.fn.dataTable.ColReorder(table,{
        });
    });
});