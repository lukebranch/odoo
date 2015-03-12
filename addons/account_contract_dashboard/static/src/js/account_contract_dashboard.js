(function () {
    'use strict';

    var value_now = 0;    

    openerp.website.ready().done(function() {

   // 1. MAIN DASHBOARD - Stat box with graph inside

      openerp.website.if_dom_contains('div.stat-box', function() {

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
                      return openerp.jsonRpc('/account_contract_dashboard/calculate_stats_diff_30_days_ago', 'call', {
                          'stat_type': self.box_code,
                          'start_date': self.start_date,
                          'end_date': self.end_date,
                          'filtered_contract_template_ids': filtered_contract_template_ids,
                      });
                  };

                  var compute_graph = function(){
                      return openerp.jsonRpc('/account_contract_dashboard/calculate_graph_stat', 'call', {
                          'stat_type': self.box_code,
                          'start_date' : start_date,
                          'end_date': end_date,
                          'complete': false,
                          'filtered_contract_template_ids': filtered_contract_template_ids,
                      });
                  };

                  $.when(compute_numbers(), compute_graph())
                  .done(function(compute_numbers, compute_graph){
                      // console.log(compute_numbers);
                      self.value = compute_numbers['value_2'];
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

                      loadChart_stat('#'+self.chart_div_id, self.box_code, false, compute_graph[1], false);
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

          // var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
          var loader = '<i class="fa fa-spin fa-refresh" style="font-size: 7em;"></i>';
          $('#stat_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          var filtered_contract_template_ids = get_filtered_contract_templates();

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

      // 3. STAT DASHBOARD - MRR GROWTH

      openerp.website.if_dom_contains('#mrr_growth_chart_div', function() {

          var start_date = $('input[type="date"][name="start_date"]').val();
          var end_date = $('input[type="date"][name="end_date"]').val();

          // var loader = '<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>';
          var loader = '<i class="fa fa-spin fa-refresh" style="font-size: 7em;"></i>';
          $('#mrr_growth_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          var filtered_contract_template_ids = get_filtered_contract_templates();

          openerp.jsonRpc('/account_contract_dashboard/calculate_graph_mrr_growth', 'call', {
              'start_date' : start_date,
              'end_date': end_date,
              'filtered_contract_template_ids': filtered_contract_template_ids,
          }).then(function(result){
              loadChart_mrr_growth_stat('#mrr_growth_chart_div', result);
              $('#mrr_growth_chart_div div.loader').hide();
          });
      });

      // 4. STAT DASHBOARD - STATS BY PLAN

      openerp.website.add_template_file('/account_contract_dashboard/static/src/xml/templates.xml');
      openerp.website.if_dom_contains('#stats_by_plan', function() {
                
          var filtered_contract_template_ids = get_filtered_contract_templates();
          var end_date = $('input[type="date"][name="end_date"]').val();
          var stat_type = $('input[type="hidden"][name="stat_type"]').val();


          openerp.jsonRpc('/account_contract_dashboard/get_stats_by_plan', 'call', {
            'stat_type': stat_type,
            'date': end_date,
            'filtered_contract_template_ids': filtered_contract_template_ids,
          }).then(function (result) {

              if (typeof result != 'undefined'){
                  var html = openerp.qweb.render('account_contract_dashboard.statsByPlan', {
                    'stats_by_plan': result[0],
                    'stat_type': stat_type,
                    'all_stats': result[1],
                    'value_now': $('#value_now').attr('value'),
                  });
                  $('#stats_by_plan').replaceWith(html);
              }
              else {
                  $('#stats_by_plan').html("<p></p>") 
              }
          });
          $('#stats_by_plan').html('<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>')        


      });

      // 5. FORECAST - GRAPH 1

      openerp.website.if_dom_contains('#revenue_forecast_chart_div, #contracts_forecast_chart_div', function() {

          // REVENUE
          var default_starting_mrr;
          var default_revenue_growth_linear;
          var default_revenue_growth_expon;
          var default_revenue_churn;
          var default_projection_time;
          var starting_mrr;
          var revenue_growth_type;
          var revenue_growth_linear;
          var revenue_growth_expon;
          var revenue_churn;
          var revenue_projection_time;
          
          // CONTRACTS
          var default_starting_contracts;
          var default_contracts_growth_linear;
          var default_contracts_growth_expon;
          var default_contracts_churn;
          var starting_contracts;
          var contracts_growth_type;
          var contracts_growth_linear;
          var contracts_growth_expon;
          var contracts_churn;
          var contracts_projection_time;

          openerp.jsonRpc('/account_contract_dashboard/get_default_values_forecast', 'call', {
          }).then(function(result){

              default_starting_mrr = result['starting_mrr'];
              default_revenue_growth_linear = result['revenue_growth_linear'];
              default_revenue_growth_expon = result['revenue_growth_expon'];
              default_revenue_churn = result['revenue_churn'];
              default_starting_contracts = result['starting_contracts'];
              default_contracts_growth_linear = result['contracts_growth_linear'];
              default_contracts_growth_expon = result['contracts_growth_expon'];
              default_contracts_churn = result['contracts_churn'];
              default_projection_time = result['projection_time'];

              $('#starting_mrr').val(default_starting_mrr);
              $('#revenue_growth_linear').val(default_revenue_growth_linear);
              $('#revenue_growth_expon').val(default_revenue_growth_expon);
              $('#revenue_churn').val(default_revenue_churn);
              $('#revenue_projection_time').val(default_projection_time);


              $('#starting_contracts').val(default_starting_contracts);
              $('#contracts_growth_linear').val(default_contracts_growth_linear);
              $('#contracts_growth_expon').val(default_contracts_growth_expon);
              $('#contracts_churn').val(default_contracts_churn);
              $('#contracts_projection_time').val(default_projection_time);


              starting_mrr = parseFloat($('#starting_mrr').val());
              $('#starting_mrr').change(function(){starting_mrr = parseFloat($('#starting_mrr').val()); reloadChart(1)});
              revenue_growth_type = $("input:radio[name=revenue_growth_type]:checked").val();
              $('input:radio[name=revenue_growth_type]').change(function(){
                revenue_growth_type = $("input:radio[name=revenue_growth_type]:checked").val();
                if (revenue_growth_type === 'linear') {
                  $('#revenue_growth_linear').show();
                  $('#revenue_growth_expon').hide();
                }
                else{
                  $('#revenue_growth_linear').hide();
                  $('#revenue_growth_expon').show();
                }
                reloadChart(1);
              });
              revenue_growth_linear = parseFloat($('#revenue_growth_linear').val());
              $('#revenue_growth_linear').change(function(){revenue_growth_linear = parseFloat($('#revenue_growth_linear').val()); reloadChart(1)});
              revenue_growth_expon = parseFloat($('#revenue_growth_expon').val());
              $('#revenue_growth_expon').change(function(){revenue_growth_expon = parseFloat($('#revenue_growth_expon').val()); reloadChart(1)});
              revenue_churn = parseFloat($('#revenue_churn').val());
              $('#revenue_churn').change(function(){revenue_churn = parseFloat($('#revenue_churn').val()); reloadChart(1)});
              revenue_projection_time = parseFloat($('#revenue_projection_time').val());
              $('#revenue_projection_time').change(function(){revenue_projection_time = parseFloat($('#revenue_projection_time').val()); reloadChart(1)});

              starting_contracts = parseFloat($('#starting_contracts').val());
              $('#starting_contracts').change(function(){starting_contracts = parseFloat($('#starting_contracts').val()); reloadChart(2)});
              contracts_growth_type = $("input:radio[name=contracts_growth_type]:checked").val();
              $('input:radio[name=contracts_growth_type]').change(function(){
                contracts_growth_type = $("input:radio[name=contracts_growth_type]:checked").val();
                if (contracts_growth_type === 'linear') {
                  $('#contracts_growth_linear').show();
                  $('#contracts_growth_expon').hide();
                }
                else{
                  $('#contracts_growth_linear').hide();
                  $('#contracts_growth_expon').show();
                }
                reloadChart(2);
              });
              contracts_growth_linear = parseFloat($('#contracts_growth_linear').val());
              $('#contracts_growth_linear').change(function(){contracts_growth_linear = parseFloat($('#contracts_growth_linear').val()); reloadChart(2)});
              contracts_growth_expon = parseFloat($('#contracts_growth_expon').val());
              $('#contracts_growth_expon').change(function(){contracts_growth_expon = parseFloat($('#contracts_growth_expon').val()); reloadChart(2)});
              contracts_churn = parseFloat($('#contracts_churn').val());
              $('#contracts_churn').change(function(){contracts_churn = parseFloat($('#contracts_churn').val()); reloadChart(2)});
              contracts_projection_time = parseFloat($('#contracts_projection_time').val());
              $('#contracts_projection_time').change(function(){contracts_projection_time = parseFloat($('#contracts_projection_time').val()); reloadChart(2)});

              reloadChart(1);
              reloadChart(2);

          });

          var loader = '<i class="fa fa-spin fa-refresh" style="font-size: 7em;"></i>';
          $('#revenue_forecast_chart_div, #contracts_forecast_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          
          function reloadChart(chart_type){

            var values = calculateForecastValues(chart_type);
            console.log(values);

            if (chart_type == 1){
              loadChart_forecast('#revenue_forecast_chart_div', values);
              $('#revenue_forecast_summary').text('In '+revenue_projection_time+' months with ' + (revenue_growth_type === 'linear' ? revenue_growth_linear : revenue_growth_expon + '%') + ' ' + revenue_growth_type + ' growth and ' + revenue_churn + '% churn, your MRR will be ' + parseInt(values[values.length - 1][1]));
            }
            else {
              loadChart_forecast('#contracts_forecast_chart_div', values);
              $('#contracts_forecast_summary').text('In '+contracts_projection_time+' months with ' + (contracts_growth_type === 'linear' ? contracts_growth_linear : contracts_growth_expon + '%') + ' ' + contracts_growth_type + ' growth and ' + contracts_churn + '% churn, your contract base will be ' + parseInt(values[values.length - 1][1]));
            }

          }

          function calculateForecastValues(chart_type) {
            var values = [];
            var now = moment();
            if (chart_type == 1){
              var cur_value = starting_mrr;
              for(var i = 1; i <= revenue_projection_time ; i++) {
                var cur_date = moment().add(i, 'months');
                if (revenue_growth_type === 'linear') {
                  cur_value = cur_value*(1-revenue_churn/100) + revenue_growth_linear;
                }
                else {
                  cur_value = cur_value*(1-revenue_churn/100)*(1+revenue_growth_expon/100);
                }
                values.push({
                  '0': cur_date.format('L'),
                  '1': cur_value,
                });
              }
            }
            else {
              var cur_value = starting_contracts;
              for(var i = 1; i <= contracts_projection_time ; i++) {
                var cur_date = moment().add(i, 'months');
                if (contracts_growth_type === 'linear') {
                  cur_value = cur_value*(1-contracts_churn/100) + contracts_growth_linear;
                }
                else {
                  cur_value = cur_value*(1-contracts_churn/100)*(1+contracts_growth_expon/100);
                }
                values.push({
                  '0': cur_date.format('L'),
                  '1': cur_value,
                });
              }
            }
            return values;
          }


          function loadChart_forecast(div_to_display, values){

            $(div_to_display).empty();

            var myData = [
                {
                  values: values,
                  // key: key_name,
                  color: '#2693d5',
                  area: true
                },  
              ];

            /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
            nv.addGraph(function() {
              var chart = nv.models.lineChart()
                            .interpolate("monotone")
                            .x(function(d) { return getDate(d); })
                            .y(function(d) { return getValue(d); });
                chart
                  .margin({left: 100})  //Adjust chart margins to give the x-axis some breathing room.
                  .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                  .transitionDuration(350)  //how fast do you want the lines to transition?
                  .showLegend(false)       //Show the legend, allowing users to turn on/off line series.
                  .showYAxis(true)        //Show the y-axis
                  .showXAxis(true)        //Show the x-axis
                ;

              var tick_values = getPrunedTickValues(myData[0]['values'], 10);

              chart.xAxis
                    .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                    .tickValues(_.map(tick_values, function(d) { return getDate(d); }))
                    .rotateLabels(55);

              chart.yAxis     //Chart y-axis settings
                  // .axisLabel(key_name)
                  .tickFormat(d3.format('.02f'));

              var svg = d3.select(div_to_display)    //Select the <svg> element you want to render the chart in.   
                  .append("svg");
              
              svg.attr("height", '20em');

              svg
                  .datum(myData)         //Populate the <svg> element with chart data...
                  .call(chart);          //Finally, render the chart!

              //Update the chart when window resizes.
              nv.utils.windowResize(function() { chart.update() });
              return chart;
            });
          };
      });




      function loadChart_stat(div_to_display, stat_type, key_name, result, show_legend){

          console.log(result);

          var myData = [
              {
                values: result,
                key: key_name,
                color: '#2693d5',
                area: true
              },  
            ];
          // console.log(myData);

          /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
          nv.addGraph(function() {
            var chart = nv.models.lineChart()
                          .interpolate("monotone")
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
              // console.log('hide legend');
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

          // setTimeout(function() {
          //     console.log('coucou');
          //     $(div_to_display + ' .nv-lineChart circle.nv-point').attr("r", "3.5");
          // }, 500);

      }

      function loadChart_mrr_growth_stat(div_to_display, result){

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


      

  });

  function getDate(d) { return new Date(d[0]); }
  function getValue(d) { return d[1]; }
  function getPrunedTickValues(ticks, nb_desired_ticks) {
      var nb_values = ticks.length;
      var keep_one_of = Math.max(1, Math.floor(nb_values / nb_desired_ticks));

      return _.filter(ticks, function(d, i) {
          return i % keep_one_of == 0;
      });
  }

  function get_filtered_contract_templates(){
    var filtered_contract_template_ids = [];
    $("input:checkbox[name=contract_template_filter]:checked").each(function(){
      filtered_contract_template_ids.push($(this).val());
    });
    return filtered_contract_template_ids;
  };

})();