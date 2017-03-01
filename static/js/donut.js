$(document).ready(function () {

    var options = {
      responsive: true,
      animateRotate: true,
      title: {
        display: true,
        text: 'Point Distribution',
        position: 'left',
        fontSize: 25,
      },
      legend: {
        display: true,
        position: 'right',
      },
    };

    // Make Donut Chart of percent of point distribution across programs
    var ctx_donut = $("#donutChart").get(0).getContext("2d");

    $.get("/balance-distribution.json", function (data) {
      var myDonutChart = new Chart(ctx_donut, {
                                              type: 'doughnut',
                                              data: data,
                                              options: options
                                            });

    });

});

