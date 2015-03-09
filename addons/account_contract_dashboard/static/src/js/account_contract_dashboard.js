(function () {
    'use strict';

    function get_filtered_contract_templates(){
      var filtered_contract_template_ids = [];
      $("input:checkbox[name=contract_template_filter]:checked").each(function(){
        filtered_contract_template_ids.push($(this).val());
      });
      return filtered_contract_template_ids;
    };

    openerp.website.if_dom_contains('div.stat-box', function() {


        // 1. MAIN DASHBOARD - Stat box with graph inside

        var QWeb = openerp.qweb;
        var website = openerp.website;

        openerp.account_contract_dashboard_boxes = {};
        
        openerp.account_contract_dashboard_boxes.Box = openerp.Widget.extend({
            init: function(box, start_date, end_date) {
                this.box = box;
                this.start_date = start_date;
                this.end_date = end_date;

                this.box_name = this.box.getAttribute("name");
                this.box_code = this.box.getAttribute("code");
                this.chart_div_id = 'chart_div_' + this.box_code;
            },
            start: function() {
                var self = this;
                var filtered_contract_template_ids = get_filtered_contract_templates();

                var compute_numbers = function(){
                    return openerp.jsonRpc('/account_contract_dashboard/calculate_stats_diff', 'call', {
                        'stat_type': self.box_code,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'filtered_contract_template_ids': filtered_contract_template_ids,
                    });
                };

                // var compute_graph = function(){
                //     return openerp.jsonRpc('/account_contract_dashboard/calculate_graph_stat', 'call', {
                //         'stat_type': self.box_code,
                //         'start_date' : start_date,
                //         'end_date': end_date,
                //         'filtered_contract_template_ids': filtered_contract_template_ids,
                //     });
                // };

                $.when(compute_numbers()) //, compute_graph())
                .done(function(compute_numbers){//, compute_graph){
                    console.log(compute_numbers);
                    self.value = compute_numbers['value'];
                    self.perc = compute_numbers['perc'];
                    self.color = compute_numbers['color'];

                    self.chart_div = 
                        '<div class="graph-box" id='+self.chart_div_id+'>'+
                        '</div>';
                    self.box.innerHTML = 
                        '<div style="position: relative;">'+
                            '<h2 style="color: #2693d5;">'+self.value+'</h2>'+
                            '<div class="trend">'+
                                '<h4 class="'+self.color+' mb0">'+self.perc+'%</h4>'+
                                '<span style="font-size: 10px;">30 Days Ago</span>'+
                            '</div>'+
                        '</div>'+
                        self.chart_div+
                        '<div>'+
                            '<h4 class="text-center mt32">'+self.box_name+'</h4>'+
                        '</div>';

                    // loadChart_stat('#'+self.chart_div_id, self.box_code, false, compute_graph[1], false);
                });
            },
        });


        var start_date = $('input[type="date"][name="start_date"]').val();
        var end_date = $('input[type="date"][name="end_date"]').val();

        for (var i=0; i<$('.stat-box').length; i++) {
            var self = $(this);
            var box = $('.stat-box')[i];

            var box_widget = new openerp.account_contract_dashboard_boxes.Box(box, start_date, end_date);
            box_widget.start();
        }
    });




    // 2. STAT DASHBOARD - GRAPHS



    openerp.website.if_dom_contains('#stat_chart_div', function() {

        var start_date = $('input[type="date"][name="start_date"]').val();
        var end_date = $('input[type="date"][name="end_date"]').val();
        var stat_type = $('input[type="hidden"][name="stat_type"]').val();

        var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
        $('#stat_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

        var filtered_contract_template_ids = get_filtered_contract_templates();

        debugger;

        openerp.jsonRpc('/account_contract_dashboard/calculate_graph_stat', 'call', {
            'stat_type': stat_type,
            'start_date' : start_date,
            'end_date': end_date,
            'filtered_contract_template_ids': filtered_contract_template_ids,
        }).then(function(result){
            loadChart_stat('#stat_chart_div', stat_type, result[0], result[1], true);
            $('#stat_chart_div div.loader').hide();
        });
    });

    function loadChart_stat(div_to_display, stat_type, key_name, result, show_legend){

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
              key: key_name,
              color: '#2693d5',
              area: true
            },
          ];
        console.log(myData);

        /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
        nv.addGraph(function() {
          var chart = nv.models.lineChart()
                        .x(function(d) { return getDate(d); })
                        .y(function(d) { return getValue(d); });
          if (show_legend){
              chart
                .margin({left: 100})  //Adjust chart margins to give the x-axis some breathing room.
                .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                .transitionDuration(350)  //how fast do you want the lines to transition?
                .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                .showYAxis(true)        //Show the y-axis
                .showXAxis(true)        //Show the x-axis
              ;
          }
          else {
            console.log('hide legend');
            chart
                .margin({left: 0, top: 0, bottom: 0, right: 0})  //Adjust chart margins to give the x-axis some breathing room.
                .useInteractiveGuideline(false)  //We want nice looking tooltips and a guideline!
                .transitionDuration(350)  //how fast do you want the lines to transition?
                .showLegend(false)       //Show the legend, allowing users to turn on/off line series.
                .showYAxis(false)        //Show the y-axis
                .showXAxis(false)        //Show the x-axis
                .interactive(false)
            ;
          }

          var tick_values = getPrunedTickValues(myData[0]['values'], 10);

          chart.xAxis
                .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                .tickValues(_.map(tick_values, function(d) { return getDate(d); }))
                .rotateLabels(55);

          chart.yAxis     //Chart y-axis settings
              .axisLabel(key_name)
              .tickFormat(d3.format('.02f'));

          var svg = d3.select(div_to_display)    //Select the <svg> element you want to render the chart in.   
              .append("svg");
          if (show_legend){
              svg.attr("height", '20em');
          }
          else {
              // svg.attr("height", '119px');
          }
          svg
              .datum(myData)         //Populate the <svg> element with chart data...
              .call(chart);          //Finally, render the chart!

          //Update the chart when window resizes.
          nv.utils.windowResize(function() { chart.update() });
          return chart;
        });

    }


    // openerp.website.if_dom_contains('#mrr_growth_chart_div', function() {

    //     var start_date = $('input[type="date"][name="start_date"]').val();
    //     var end_date = $('input[type="date"][name="end_date"]').val();

    //     var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
    //     $('#mrr_growth_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

    //     var filtered_contract_template_ids = get_filtered_contract_templates();

    //     openerp.jsonRpc('/account_contract_dashboard/calculate_graph_mrr_growth', 'call', {
    //         'start_date' : start_date,
    //         'end_date': end_date,
    //         'filtered_contract_template_ids': filtered_contract_template_ids,
    //     }).then(function(result){
    //         loadChart_mrr_growth_stat('#mrr_growth_chart_div', result);
    //         $('#mrr_growth_chart_div div.loader').hide();
    //     });
    // });

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