(function () {
    'use strict';
    openerp.website.add_template_file('/account_contract_dashboard/static/src/xml/templates.xml');
    var loader = '<i class="fa fa-spin fa-spinner fa-pulse" style="font-size: 3em;"></i>';

    openerp.website.ready().done(function() {

      // 0. DATETIME PICKERS
      openerp.website.if_dom_contains('#datetimepicker_start, #datetimepicker_end', function() {
          $('#datetimepicker_start').datetimepicker({
            format: 'YYYY-MM-DD',
            viewMode: 'months',
          });
          $('#datetimepicker_end').datetimepicker({
            format: 'YYYY-MM-DD',
            viewMode: 'months',
          });
          $("#datetimepicker_start").on("dp.change", function (e) {
              $('#datetimepicker_end').data("DateTimePicker").setMinDate(e.date);
          });
          $("#datetimepicker_end").on("dp.change", function (e) {
              $('#datetimepicker_start').data("DateTimePicker").setMaxDate(e.date);
          });
      });

      // 1. MAIN DASHBOARD - Stat box with graph inside
      openerp.website.if_dom_contains('div.stat-box, div.forecast-box', function() {

          var QWeb = openerp.qweb;
          var website = openerp.website;

          openerp.account_contract_dashboard_boxes = {};

          // Widget for stat
          openerp.account_contract_dashboard_boxes.StatBox = openerp.Widget.extend({
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
                  var filtered_contract_template_ids = getFilteredContractTemplates();

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
                          'nb_points': 30,
                          'filtered_contract_template_ids': filtered_contract_template_ids,
                      });
                  };

                  $.when(compute_numbers(), compute_graph())
                  .done(function(compute_numbers, compute_graph){
                      self.value = compute_numbers['value_2'];
                      self.perc = compute_numbers['perc'];
                      self.color = compute_numbers['color'];
                      self.added_symbol = compute_numbers['added_symbol']

                      var box_content = openerp.qweb.render('account_contract_dashboard.statBoxContent', {
                        'value': self.value,
                        'color': self.color,
                        'perc': self.perc,
                        'added_symbol': self.added_symbol,
                        'chart_div_id': self.chart_div_id,
                        'box_name': self.box_name,
                        'formatNumber': formatNumber,
                      });
                      self.box.innerHTML = box_content;
                      loadChart_stat('#'+self.chart_div_id, self.box_code, false, compute_graph[1], false);
                  });
              },
          });

          // Widget for forecast
          openerp.account_contract_dashboard_boxes.ForecastBox = openerp.Widget.extend({
              init: function(box, end_date) {
                  this.box = box;
                  this.end_date = end_date

                  this.box_name = this.box.getAttribute("name");
                  this.box_code = this.box.getAttribute("code");
                  this.chart_div_id = 'chart_div_' + this.box_code;
              },
              start: function() {
                  var self = this;

                  var compute_numbers = function(){
                      return openerp.jsonRpc('/account_contract_dashboard/get_default_values_forecast', 'call', {
                          'forecast_type': self.box_code,
                          'end_date': self.end_date,
                      });
                  }

                  $.when(compute_numbers())
                  .done(function(compute_numbers){

                    var compute_graph = calculateForecastValues(compute_numbers['starting_value'], compute_numbers['projection_time'], 'linear', compute_numbers['churn'], compute_numbers['growth_linear'], 0);

                    self.value = compute_graph[compute_graph.length - 1][1];

                    var box_content = openerp.qweb.render('account_contract_dashboard.forecastBoxContent', {
                      'value': parseInt(self.value),
                      'currency': compute_numbers['currency'],
                      'chart_div_id': self.chart_div_id,
                      'box_name': self.box_name,
                      'formatNumber': formatNumber,
                    });
                    self.box.innerHTML = box_content;
                    loadChart_stat('#'+self.chart_div_id, self.box_code, false, compute_graph, false);
                  });
              },
          });

          // Launch widgets

          var start_date = $('input[name="start_date"]').val();
          var end_date = $('input[name="end_date"]').val();

          for (var i=0; i<$('.stat-box').length; i++) {
              var self = $(this);
              var box = $('.stat-box')[i];

              var box_widget = new openerp.account_contract_dashboard_boxes.StatBox(box, start_date, end_date);
              box_widget.start();
          }

          for (var i=0; i<$('.forecast-box').length; i++) {
              var self = $(this);
              var box = $('.forecast-box')[i];

              var box_widget = new openerp.account_contract_dashboard_boxes.ForecastBox(box, end_date);
              box_widget.start();
          }
      });

      // 2.1 STAT DASHBOARD - HISTORY
      openerp.website.if_dom_contains('#stat-history-box', function() {
                
          var filtered_contract_template_ids = getFilteredContractTemplates();
          var start_date = $('input[name="start_date"]').val();
          var end_date = $('input[name="end_date"]').val();
          var stat_type = $('input[type="hidden"][name="stat_type"]').val();

          openerp.jsonRpc('/account_contract_dashboard/get_stats_history', 'call', {
            'stat_type': stat_type,
            'start_date': start_date,
            'end_date': end_date,
            'filtered_contract_template_ids': filtered_contract_template_ids,
          }).then(function (result) {

              function compute_rate(stat_types, stat_type, old_value, new_value){
                  var direction = stat_types[stat_type]['dir']
                  var value = 0
                  var color = 'oBlack'

                  if (old_value != 0) {value = 100.0 * (new_value-old_value) / old_value}
                  if (value && direction == 'up'){
                      color = (value > 0) && 'oGreen' || 'oRed'
                  }
                  if (value && direction != 'up'){
                      color = (value < 0) && 'oGreen' || 'oRed'
                  }
                  return [parseInt(value), color]
              }

              if (typeof result != 'undefined'){
                  var html = openerp.qweb.render('account_contract_dashboard.statsHistory', {
                    'stats_history': result[0],
                    'stat_type': stat_type,
                    'all_stats': result[1],
                    'currency': result[2],
                    'rate': compute_rate,
                    'value_now': parseInt($('#value_now').attr('value')),
                  });
                  $('#stat-history-box').append(html);
              }
              else {
                  $('#stat-history-box').html("<p></p>")
              }
          });
          $('#stats_by_plan').html('<div class="loading"><div id="big-circle"><div id="little-circle"></div></div></div>')
      });


      // 2.2 STAT DASHBOARD - GRAPHS
      openerp.website.if_dom_contains('#stat_chart_div', function() {

          var start_date = $('input[name="start_date"]').val();
          var end_date = $('input[name="end_date"]').val();
          var stat_type = $('input[type="hidden"][name="stat_type"]').val();

          $('#stat_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          var filtered_contract_template_ids = getFilteredContractTemplates();

          openerp.jsonRpc('/account_contract_dashboard/calculate_graph_stat', 'call', {
              'stat_type': stat_type,
              'start_date' : start_date,
              'end_date': end_date,
              'complete': true,
              'nb_points': 30,
              'filtered_contract_template_ids': filtered_contract_template_ids,
          }).then(function(result){
              loadChart_stat('#stat_chart_div', stat_type, result[0], result[1], true);
              $('#stat_chart_div div.loader').hide();
          });
      });

      // 2.3 STAT DASHBOARD - MRR GROWTH
      openerp.website.if_dom_contains('#mrr_growth_chart_div', function() {

          var start_date = $('input[name="start_date"]').val();
          var end_date = $('input[name="end_date"]').val();

          $('#mrr_growth_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          var filtered_contract_template_ids = getFilteredContractTemplates();

          openerp.jsonRpc('/account_contract_dashboard/calculate_graph_mrr_growth', 'call', {
              'start_date' : start_date,
              'end_date': end_date,
              'complete': true,
              'filtered_contract_template_ids': filtered_contract_template_ids,
          }).then(function(result){
              loadChart_mrr_growth_stat('#mrr_growth_chart_div', result[0], result[1]);
              $('#mrr_growth_chart_div div.loader').hide();
          });
      });

      // 4. STAT DASHBOARD - STATS BY PLAN
      openerp.website.if_dom_contains('#stats_by_plan', function() {
                
          var filtered_contract_template_ids = getFilteredContractTemplates();
          var start_date = $('input[name="start_date"]').val();
          var end_date = $('input[name="end_date"]').val();
          var stat_type = $('input[type="hidden"][name="stat_type"]').val();


          openerp.jsonRpc('/account_contract_dashboard/get_stats_by_plan', 'call', {
            'stat_type': stat_type,
            'start_date': start_date,
            'end_date': end_date,
            'filtered_contract_template_ids': filtered_contract_template_ids,
          }).then(function (result) {

              if (typeof result != 'undefined'){
                  var html = openerp.qweb.render('account_contract_dashboard.statsByPlan', {
                    'stats_by_plan': result[0],
                    'stat_type': stat_type,
                    'all_stats': result[1],
                    'currency': result[2],
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

      // 2.3 STAT DASHBOARD - MRR GROWTH
      openerp.website.if_dom_contains('#mrr_growth_salesman', function() {

          $('#datetimepicker_period').datetimepicker({
              viewMode: 'months',
              format: 'YYYY-MM-DD',
            });

          // var start_date = $('input[name="start_date"]').val();
          // var end_date = $('input[name="end_date"]').val();

          var salesman_id = $('input[name="salesman_id"]').val();
          var period = $('input[name="period"]').val();

          $('#mrr_growth_salesman').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          openerp.jsonRpc('/account_contract_dashboard/get_values_salesman', 'call', {
            'end_date': period,
            'salesman_id': salesman_id,
          }).then(function(result){
              loadChart_mrr_salesman('#mrr_growth_salesman', result);
              $('#mrr_growth_salesman div.loader').hide();

              displayContractsModifications(result[5]);
          });
      });

      function displayContractsModifications(modifications){
        var html = openerp.qweb.render('account_contract_dashboard.contractModifications', {
          'modifications': modifications,
        });
        $('#contract_modifications').append(html);
      }

      

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

          var currency;

          function default_values_forecast(forecast_type){
              return openerp.jsonRpc('/account_contract_dashboard/get_default_values_forecast', 'call', {
                  'forecast_type': forecast_type
              });
          };
          $.when(default_values_forecast('forecast_mrr'), default_values_forecast('forecast_contracts'))
          .done(function(default_values_forecast_mrr, default_values_forecast_contracts){

              default_starting_mrr = parseInt(default_values_forecast_mrr['starting_value']);
              default_revenue_growth_linear = parseInt(default_values_forecast_mrr['growth_linear']);
              default_revenue_growth_expon = parseInt(default_values_forecast_mrr['growth_expon']);
              default_revenue_churn = parseInt(default_values_forecast_mrr['churn']);
              default_starting_contracts = parseInt(default_values_forecast_contracts['starting_value']);
              default_contracts_growth_linear = parseInt(default_values_forecast_contracts['growth_linear']);
              default_contracts_growth_expon = parseInt(default_values_forecast_contracts['growth_expon']);
              default_contracts_churn = parseInt(default_values_forecast_contracts['churn']);
              default_projection_time = default_values_forecast_mrr['projection_time'];
              currency = default_values_forecast_mrr['currency'];

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


              starting_mrr = parseInt($('#starting_mrr').val());
              $('#starting_mrr').change(function(){starting_mrr = parseInt($('#starting_mrr').val()); reloadChart(1)});
              revenue_growth_type = $("input:radio[name=revenue_growth_type]:checked").val();
              $('input:radio[name=revenue_growth_type]').change(function(){
                revenue_growth_type = $("input:radio[name=revenue_growth_type]:checked").val();
                if (revenue_growth_type === 'linear') {
                  $('#revenue_growth_linear').parent().show();
                  $('#revenue_growth_expon').parent().hide();
                }
                else{
                  $('#revenue_growth_linear').parent().hide();
                  $('#revenue_growth_expon').parent().show();
                }
                reloadChart(1);
              });
              revenue_growth_linear = parseInt($('#revenue_growth_linear').val());
              $('#revenue_growth_linear').change(function(){revenue_growth_linear = parseInt($('#revenue_growth_linear').val()); reloadChart(1)});
              revenue_growth_expon = parseInt($('#revenue_growth_expon').val());
              $('#revenue_growth_expon').change(function(){revenue_growth_expon = parseInt($('#revenue_growth_expon').val()); reloadChart(1)});
              revenue_churn = parseInt($('#revenue_churn').val());
              $('#revenue_churn').change(function(){revenue_churn = parseInt($('#revenue_churn').val()); reloadChart(1)});
              revenue_projection_time = parseInt($('#revenue_projection_time').val());
              $('#revenue_projection_time').change(function(){revenue_projection_time = parseInt($('#revenue_projection_time').val()); reloadChart(1)});

              starting_contracts = parseInt($('#starting_contracts').val());
              $('#starting_contracts').change(function(){starting_contracts = parseInt($('#starting_contracts').val()); reloadChart(2)});
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
              contracts_growth_linear = parseInt($('#contracts_growth_linear').val());
              $('#contracts_growth_linear').change(function(){contracts_growth_linear = parseInt($('#contracts_growth_linear').val()); reloadChart(2)});
              contracts_growth_expon = parseInt($('#contracts_growth_expon').val());
              $('#contracts_growth_expon').change(function(){contracts_growth_expon = parseInt($('#contracts_growth_expon').val()); reloadChart(2)});
              contracts_churn = parseInt($('#contracts_churn').val());
              $('#contracts_churn').change(function(){contracts_churn = parseInt($('#contracts_churn').val()); reloadChart(2)});
              contracts_projection_time = parseInt($('#contracts_projection_time').val());
              $('#contracts_projection_time').change(function(){contracts_projection_time = parseInt($('#contracts_projection_time').val()); reloadChart(2)});

              reloadChart(1);
              reloadChart(2);

          });

          $('#revenue_forecast_chart_div, #contracts_forecast_chart_div').html("<div class='loader' style='position: relative; text-align:center; width: 100%; height: 300px;'>" + loader + "</div>");

          function reloadChart(chart_type){

            if (chart_type == 1){
              var values = calculateForecastValues(starting_mrr, revenue_projection_time, revenue_growth_type, revenue_churn, revenue_growth_linear, revenue_growth_expon);
              loadChartForecast('#revenue_forecast_chart_div', values);
              $('#revenue_forecast_summary').replaceWith('<h3 class="text-center mt32 mb32" id="revenue_forecast_summary">In <span class="oBlue">'+revenue_projection_time+'</span> months with <span class="oBlue">' + (revenue_growth_type === 'linear' ? revenue_growth_linear + currency : revenue_growth_expon + '%') + ' ' + revenue_growth_type + '</span> growth and <span class="oRed">' + revenue_churn + '%</span> churn, your MRR will be <span class="oGreen">' + parseInt(values[values.length - 1][1]) + currency +'</span></h3>');
            }
            else {
              var values = calculateForecastValues(starting_contracts, contracts_projection_time, contracts_growth_type, contracts_churn, contracts_growth_linear, contracts_growth_expon);
              loadChartForecast('#contracts_forecast_chart_div', values);
              $('#contracts_forecast_summary').replaceWith('<h3 class="text-center mt32 mb32" id="contracts_forecast_summary">In <span class="oBlue">'+contracts_projection_time+'</span> months with <span class="oBlue">' + (contracts_growth_type === 'linear' ? contracts_growth_linear + ' contracts' : contracts_growth_expon + '%') + ' ' + contracts_growth_type + '</span> growth and <span class="oRed">' + contracts_churn + '%</span> churn, your contract base will be <span class="oGreen">' + parseInt(values[values.length - 1][1]) + '</span></h3>');
            }

          }
      });

      function calculateForecastValues(starting_value, projection_time, growth_type, churn, growth_linear, growth_expon) {
        var values = [];
        var now = moment();
        var cur_value = starting_value;
        
        for(var i = 1; i <= projection_time ; i++) {
          var cur_date = moment().add(i, 'months');
          if (growth_type === 'linear') {
            cur_value = cur_value*(1-churn/100) + growth_linear;
          }
          else {
            cur_value = cur_value*(1-churn/100)*(1+growth_expon/100);
          }
          values.push({
            '0': cur_date.format('L'),
            '1': cur_value,
          });
        }
        return values;
      }

      function loadChartForecast(div_to_display, values){

        $(div_to_display).empty();

        var myData = [
            {
              values: values,
              color: '#2693d5',
              area: true
            },
          ];
        nv.addGraph(function() {
          var chart = nv.models.lineChart()
                        .interpolate("monotone")
                        .x(function(d) { return getDate(d); })
                        .y(function(d) { return getValue(d); });
            chart
              .margin({left: 100})
              .useInteractiveGuideline(true)
              .transitionDuration(350)
              .showLegend(false)
              .showYAxis(true)
              .showXAxis(true)
            ;

          var tick_values = getPrunedTickValues(myData[0]['values'], 10);

          chart.xAxis
                .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                .tickValues(_.map(tick_values, function(d) { return getDate(d); }))
                .rotateLabels(55);

          chart.yAxis
              .tickFormat(d3.format('.02f'));

          var svg = d3.select(div_to_display)
              .append("svg");

          svg.attr("height", '20em');

          svg
              .datum(myData)
              .call(chart);
          nv.utils.windowResize(function() { chart.update() });
          return chart;
        });
      }


      function loadChart_stat(div_to_display, stat_type, key_name, result, show_legend){

          var myData = [
            {
              values: result,
              key: key_name,
              color: '#2693d5',
              area: true
            },
          ];
          nv.addGraph(function() {
            var chart = nv.models.lineChart()
                          .interpolate("monotone")
                          .forceY([getMinY(result)])
                          .x(function(d) { return getDate(d); })
                          .y(function(d) { return getValue(d); });
            if (show_legend){
                chart
                  .margin({left: 100})
                  .useInteractiveGuideline(true)
                  .transitionDuration(350)
                  .showLegend(true)
                  .showYAxis(true)
                  .showXAxis(true)
                ;
            }
            else {
              chart
                  .margin({left: 0, top: 0, bottom: 0, right: 0})
                  .useInteractiveGuideline(false)
                  .transitionDuration(350)
                  .showLegend(false)
                  .showYAxis(false)
                  .showXAxis(false)
                  .interactive(false)
              ;
            }

            var tick_values = getPrunedTickValues(myData[0]['values'], 10);

            chart.xAxis
                  .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                  .tickValues(_.map(tick_values, function(d) { return getDate(d); }))
                  .rotateLabels(55);

            chart.yAxis
                .axisLabel(key_name)
                .tickFormat(d3.format('.02f'));

            var svg = d3.select(div_to_display)
                .append("svg");
            if (show_legend){
                svg.attr("height", '20em');
            }
            svg
                .datum(myData)
                .call(chart);

            nv.utils.windowResize(function() { chart.update() });
            return chart;
          });
      }


      function loadChart_mrr_growth_stat(div_to_display, result, currency){

          var myData = [
              {
                values: result[0],
                key: 'New MRR',
                color: '#26b548',
              },
              {
                  values: result[1],
                  key: 'Churned MRR',
                  color: '#df2e28',
              },
              {
                  values: result[2],
                  key: 'Expansion MRR',
                  color: '#fed049',
              },
              {
                  values: result[3],
                  key: 'Down MRR',
                  color: '#ffa500',
              },
              {
                  values: result[4],
                  key: 'Net New MRR',
                  color: '#2693d5',
              }
            ];

          nv.addGraph(function() {
            var chart = nv.models.lineChart()
                          .interpolate("monotone")
                          .x(function(d) { return getDate(d); })
                          .y(function(d) { return getValue(d); })
                          .margin({left: 100})
                          .useInteractiveGuideline(true)
                          .transitionDuration(350)
                          .showLegend(true)
                          .showYAxis(true)
                          .showXAxis(true)
            ;

            var tick_values = getPrunedTickValues(myData[0]['values'], 10);

            chart.xAxis
                  .tickFormat(function(d) { return d3.time.format("%m/%d/%y")(new Date(d)); })
                  .tickValues(_.map(tick_values, function(d) {return getDate(d); }))
                  .rotateLabels(55);

            chart.yAxis
                .axisLabel('MRR ('+currency+')')
                .tickFormat(d3.format('.02f'));

            var svg = d3.select(div_to_display)
                .append("svg")
                .attr("height", '20em')
            svg
                .datum(myData)
                .call(chart);
            nv.utils.windowResize(function() { chart.update() });
            return chart;

          });
      }
      
      function loadChart_mrr_salesman(div_to_display, result){

          var myData = [
            {
              key: "MRR Growth",
              values: [
                { 
                  "label" : "New MRR" ,
                  "value" : result[0]
                } , 
                { 
                  "label" : "Churned MRR" , 
                  "value" : result[1]
                } , 
                { 
                  "label" : "Expansion MRR" , 
                  "value" : result[2]
                } , 
                { 
                  "label" : "Down MRR" , 
                  "value" : result[3]
                } , 
                { 
                  "label" : "Net New MRR" ,
                  "value" : result[4]
                } ,
              ]
            }
          ];

          nv.addGraph(function() {
            var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.label })    //Specify the data accessors.
                .y(function(d) { return d.value })
                .staggerLabels(true)    //Too many bars and not enough room? Try staggering labels.
                .tooltips(false)        //Don't show tooltips
                .showValues(true)       //...instead, show the bar value right on top of each bar.
                .transitionDuration(350)
                ;

            var svg = d3.select(div_to_display)
                .append("svg")
                .attr("height", '20em')
            svg
                .datum(myData)
                .call(chart);

            nv.utils.windowResize(chart.update);

            return chart;
          });
      }
  });

  function formatNumber(number) {
      if (number > 999999){
        return (parseInt(number/1000000)).toString() + 'M';
      }
      else if (number > 99999){
        return (parseInt(number/1000)).toString() + 'K';
      }
      return number;
  }

  function getMinY(l) {
      var min = Math.min.apply(Math,l.map(function(o){return o[1];}));
      var max = Math.max.apply(Math,l.map(function(o){return o[1];}));
      return Math.max(0, min - (max-min)/2);
  }
  function getDate(d) { return new Date(d[0]); }
  function getValue(d) { return d[1]; }
  function getPrunedTickValues(ticks, nb_desired_ticks) {
      var nb_values = ticks.length;
      var keep_one_of = Math.max(1, Math.floor(nb_values / nb_desired_ticks));

      return _.filter(ticks, function(d, i) {
          return i % keep_one_of == 0;
      });
  }
  function getFilteredContractTemplates(){
    var filteredContractTemplateIds = [];
    $("input:checkbox[name=contract_template_filter]:checked").each(function(){
      filteredContractTemplateIds.push($(this).val());
    });
    return filteredContractTemplateIds;
  };

})();