$(document).ready(function () {

    if ($('.stat-box').length > 0){
        start_date = $('input[type="date"][name="start_date"]').val();
        end_date = $('input[type="date"][name="end_date"]').val();

        openerp.jsonRpc('/account_contract_dashboard/calculate_stats_diff', 'call', {
            'start_date': start_date,
            'end_date': end_date,
        }).done(function(result){

            for (i=0; i<$('.stat-box').length; i++) {
                box = $('.stat-box')[i];
                box_name = box.getAttribute("name");
                box_code = box.getAttribute("code");
                chart_div_id = 'chart_div_' + box_code;

                // value_start = result[box_code]['value_start'];
                value = result[box_code]['value'];
                perc = result[box_code]['perc'];
                color = result[box_code]['color'];

                chart_div = 
                    '<div style="position: absolute; top: 0; left: 0; opacity: 0.3;" id='+chart_div_id+'>'+
                    '</div>';
                graph = []
                box.innerHTML = 
                    '<div style="position: relative;">'+
                        '<h1 style="font-size: 42px; color: #2693d5;">'+value+'</h1>'+
                        '<div class="trend">'+
                            '<h2 class="'+color+' mb0">'+perc+'%</h2>'+
                            '<span style="font-size: 10px;">30 Days Ago</span>'+
                        '</div>'+
                    '</div>'+
                    chart_div+
                    '<div>'+
                        '<h4 class="text-center mt32">'+box_name+'</h4>'+
                    '</div>';

                // loadChart(chart_div_id, box_code, start_date, end_date, true);
            }
        });
    }

    if ($('#chart_div').length > 0){

        start_date = $('input[type="date"][name="start_date"]').val();
        end_date = $('input[type="date"][name="end_date"]').val();
        stat_type = $('input[type="hidden"][name="stat_type"]').val();

        var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
        $('#chart_div').html("<div style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

        loadChart('chart_div', stat_type, start_date, end_date, false);
    }

    function loadChart(div_to_display, stat_type, start_date, end_date, hide_legend){

        // Load the Visualization API and the piechart package.
        google.load('visualization', '1', {'callback':function() {
            openerp.jsonRpc('/account_contract_dashboard/calculate_graph', 'call', {
                'stat_type': stat_type,
                'start_date' : start_date,
                'end_date': end_date,
            }).then(function(result){

                // ANIMATION WORKS ON THIS
                var data = [];
                data = new google.visualization.DataTable();
                data.addColumn('string', 'Day');
                data.addColumn('number', stat_type.toUpperCase());
                data.addRows(result);
                var options = {
                    title: '',
                    pointSize : 3,
                    allowContainerBoundaryTextCufoff: true,
                    // backgroundColor:"#FAFAFA",

                    legend: {
                        position: 'none'
                    },

                    animation:{
                        duration: 1000,
                        easing: 'out',
                    },
                    hAxis: {
                        title: '',
                        textPosition:"out",
                        showTextEvery: 2,

                        textStyle: {
                            color: '#333',
                            fontName: 'Lato',
                            fontSize: 12
                        }
                    },
                };

                if (hide_legend){
                    options['legend'] = {position: 'none'};
                    options['hAxis'] = {textPosition: 'none'};
                    options['vAxis'] = {textPosition: 'none', gridlines: {color: 'transparent'}};
                    options['curveType'] = 'function';
                    options['focusTarget'] = 'none';
                    options['tooltip'] = {trigger: 'none'};
                    options['pointSize'] = 0;
                    options['enableInteractivity'] = false;
                }

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