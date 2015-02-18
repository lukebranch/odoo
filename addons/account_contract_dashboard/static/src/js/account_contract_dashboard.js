$(document).ready(function () {

    if ($('#chart_div').length > 0){

        start_date = $('input[type="date"][name="date_from"]').val()
        end_date = $('input[type="date"][name="date_to"]').val()
        stat_type = $('input[type="hidden"][name="stat_type"]').val()

        debugger;

        // var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
        // $('#chart_div').html("<div style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

        loadChart('chart_div', stat_type, start_date, end_date);
    }

    function loadChart(div_to_display, stat_type, start_date, end_date){

        // Load the Visualization API and the piechart package.
        google.load('visualization', '1', {'callback':function() {
            openerp.jsonRpc('/account_contract_dashboard/calculate', 'call', {
                'stat_type': stat_type,
                'start_date' : start_date,
                'end_date': end_date,
            }).then(function(result){

                console.log(result);

                // ANIMATION WORKS ON THIS
                var data = [];
                data = new google.visualization.DataTable();
                data.addColumn('string', 'Day');
                data.addColumn('number', stat_type.toUpperCase());
                data.addRows(result);

                var options = {
                  title: '',
                  pointSize : 5,
                //   focusTarget: 'category',
                //   // allowContainerBoundaryTextCufoff: true,

                //     chartArea: {
                //         width: '90%', 
                //         height: '50%',

                //     },
                //     backgroundColor:"#FAFAFA",

                // animation:{
                //     duration: 1000,
                //     easing: 'out',
                //   },
                //   hAxis: {
                //     title: '',
                //     textPosition:"out",
                //     //showTextEvery: result.length - 1,
                //     showTextEvery: 2,

                //     textStyle: {
                //         color: '#333',
                //         fontName: 'Lato',
                //         fontSize: 12
                //         }
                //     },
                //   vAxis: {0: {logScale: false},
                //           1: {logScale: false, maxValue: 2}
                //           },
                //   series:{
                //     0:{
                //         type:'area',
                //         targetAxisIndex:0,
                //         color:"rgb(5, 141, 199)",
                //         lineWidth:"3",
                //         areaOpacity:0.1
                //     },
                //     1:{
                //         type:'line',
                //         targetAxisIndex:1,
                //         lineWidth:"3",
                //         color:'rgb(247, 153, 28)'

                //     },
                //   },
      
                //   annotations: {
                //     textStyle: {
                //       fontName: 'Lato',
                //       fontSize: 18,
                //       bold: true,
                //       highContrast: false,
                //       italic: false,
                //       color: '#888888',
                //       opacity: 0.8,
                //     }
                //   }
                };

                var chart = new google.visualization.AreaChart(document.getElementById(div_to_display));

                function drawChart() {
                    chart.draw(data, options);
                }

                drawChart();

                window.onload = drawChart();
                window.onresize = drawChart();
               
            });

        }, 'packages':['corechart']});
    }
});