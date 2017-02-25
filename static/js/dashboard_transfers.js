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
                { "data": "transfer_id", "title": "Id" },
                { "data": "outgoing", "title": "From" },
                { "data": "outgoing_amount", "title": "Transferred Amount", "class": "center" },
                { "data": "receiving", "title": "T0", "class": "center" },
                { "data": "receiving_amount", "title": "Received Amount", "class": "center" },
                { "data": "timestamp", "title": "Timestamp", "class": "center",  "type":'datetime', "format":'dddd D MMMM YYYY',},
            ],

            "columnDefs": [{
                "targets": 5,
                    "data": "timestamp",
                    "render": function (data, type, full, meta) {
                    return moment(data).format('M/D/YYYY, h:mm a');
                }
            }]

        });

        table.show();

    });
});