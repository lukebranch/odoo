(function () {
   'use strict';

    openerp.website.if_dom_contains('div.stat-box', function() {


    // 1. MAIN DASHBOARD - Stat box with graph inside


    // if ($('.stat-box').length > 0){

        console.log('coucou');

        var start_date = $('input[type="date"][name="start_date"]').val();
        var end_date = $('input[type="date"][name="end_date"]').val();

        openerp.jsonRpc('/account_contract_dashboard/calculate_stats_diff', 'call', {
            'start_date': start_date,
            'end_date': end_date,
        }).done(function(result){

            for (var i=0; i<$('.stat-box').length; i++) {
                var box = $('.stat-box')[i];
                var box_name = box.getAttribute("name");
                var box_code = box.getAttribute("code");
                var chart_div_id = 'chart_div_' + box_code;

                // value_start = result[box_code]['value_start'];
                var value = result[box_code]['value'];
                var perc = result[box_code]['perc'];
                var color = result[box_code]['color'];

                var chart_div = 
                    '<div style="position: absolute; top: 0; left: 0; opacity: 0.3;" id='+chart_div_id+'>'+
                    '</div>';
                var graph = []
                box.innerHTML = 
                    '<div style="position: relative;">'+
                        '<h2 style="color: #2693d5;">'+value+'</h2>'+
                        '<div class="trend">'+
                            '<h4 class="'+color+' mb0">'+perc+'%</h4>'+
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
    });




    // 2. STAT DASHBOARD - GRAPHS



    openerp.website.if_dom_contains('#stat_chart_div', function() {

        var start_date = $('input[type="date"][name="start_date"]').val();
        var end_date = $('input[type="date"][name="end_date"]').val();
        var stat_type = $('input[type="hidden"][name="stat_type"]').val();

        var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
        $('#stat_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

        openerp.jsonRpc('/account_contract_dashboard/calculate_graph_stat', 'call', {
            'stat_type': stat_type,
            'start_date' : start_date,
            'end_date': end_date,
        }).then(function(result){
            loadChart_stat('#stat_chart_div', stat_type, result, false);
            $('#stat_chart_div div.loader').hide();
        });
    });

    function loadChart_stat(div_to_display, stat_type, result, hide_legend){

        function getDate(d) { return new Date(d[0]); }
        function getValue(d) { return d[1]; }
        function getPrunedTickValues(ticks, nb_desired_ticks) {
            var nb_values = ticks.length;
            var keep_one_of = Math.max(1, Math.floor(nb_values / nb_desired_ticks));

            return _.filter(ticks, function(d, i) {
                return i % keep_one_of == 0;
            });
        }

        var myData = [
            {
              values: result,
              key: stat_type,
              color: '#2693d5',
              area: true
            },
          ];

        /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
        nv.addGraph(function() {
          var chart = nv.models.lineChart()
                        .x(function(d) { return getDate(d); })
                        .y(function(d) { return getValue(d); })
                        .margin({left: 100})  //Adjust chart margins to give the x-axis some breathing room.
                        .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                        .transitionDuration(350)  //how fast do you want the lines to transition?
                        .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                        .showYAxis(true)        //Show the y-axis
                        .showXAxis(true)        //Show the x-axis
          ;

          var tick_values = getPrunedTickValues(myData[0]['values'], 10);

          chart.xAxis
                .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                .tickValues(_.map(tick_values, function(d) { return getDate(d); }))
                .rotateLabels(55);

          chart.yAxis     //Chart y-axis settings
              .axisLabel('MRR (€)')
              .tickFormat(d3.format('.02f'));

          var svg = d3.select(div_to_display)    //Select the <svg> element you want to render the chart in.   
              .append("svg")
              .attr("height", '20em')
          svg
              .datum(myData)         //Populate the <svg> element with chart data...
              .call(chart);          //Finally, render the chart!

          //Update the chart when window resizes.
          nv.utils.windowResize(function() { chart.update() });
          return chart;
        });

    }


    openerp.website.if_dom_contains('#mrr_growth_chart_div', function() {

        var start_date = $('input[type="date"][name="start_date"]').val();
        var end_date = $('input[type="date"][name="end_date"]').val();

        var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
        $('#mrr_growth_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

        openerp.jsonRpc('/account_contract_dashboard/calculate_graph_mrr_growth', 'call', {
            'start_date' : start_date,
            'end_date': end_date,
        }).then(function(result){
            loadChart_mrr_growth_stat('#mrr_growth_chart_div', result);
            $('#mrr_growth_chart_div div.loader').hide();
        });
    });

    function loadChart_mrr_growth_stat(div_to_display, result){

        function getDate(d) { return new Date(d[0]); }
        function getValue(d) { return d[1]; }
        function getPrunedTickValues(ticks, nb_desired_ticks) {
            var nb_values = ticks.length;
            var keep_one_of = Math.max(1, Math.floor(nb_values / nb_desired_ticks));

            return _.filter(ticks, function(d, i) {
                return i % keep_one_of == 0;
            });
        }

        var myData = [
            {
              values: result[0],
              key: 'New MRR',
              color: '#26b548',
            },
            {
                values: result[1],
                key: 'Expansion MRR',
                color: '#fed049',
            },
            {
                values: result[2],
                key: 'Churned MRR',
                color: '#df2e28',
            },
            {
                values: result[3],
                key: 'Net New MRR',
                color: '#2693d5',
            }
          ];
        // var bisectDate = d3.bisector(function(d) { return d.date; }).left;
        // function mousemove(d) {
        //     console.log('coucou');
        //     debugger;
            // var x0 = x.invert(d3.mouse(this)[0]),
            //     i = bisectDate(data, x0, 1),
            //     d0 = data[i - 1],
            //     d1 = data[i],
            //     d = x0 - d0.date > d1.date - x0 ? d1 : d0;
            // focus.attr("transform", "translate(" + x(d.date) + "," + y(d.close) + ")");
        // }

        /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
        nv.addGraph(function() {
          var chart = nv.models.lineChart()
                        .x(function(d) { return getDate(d); })
                        .y(function(d) { return getValue(d); })
                        .margin({left: 100})  //Adjust chart margins to give the x-axis some breathing room.
                        .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                        .transitionDuration(350)  //how fast do you want the lines to transition?
                        .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                        .showYAxis(true)        //Show the y-axis
                        .showXAxis(true)        //Show the x-axis
          ;

          var tick_values = getPrunedTickValues(myData[0]['values'], 10);

          chart.xAxis
                .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                .tickValues(_.map(tick_values, function(d) {return getDate(d); }))
                .rotateLabels(55);

          chart.yAxis     //Chart y-axis settings
              .axisLabel('MRR (€)')
              .tickFormat(d3.format('.02f'));

          var svg = d3.select(div_to_display)    //Select the <svg> element you want to render the chart in.   
              .append("svg")
              .attr("height", '20em')
          svg
              .datum(myData)         //Populate the <svg> element with chart data...
              .call(chart);          //Finally, render the chart!

          //Update the chart when window resizes.
          nv.utils.windowResize(function() { chart.update() });
          return chart;

        });
    }

})();