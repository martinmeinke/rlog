plot = null;
data = [];
options = {};
liveTicks = 100;
latestPosition = null;
last_time_rendered = 0;
crosshair_data_list_created = false;

function addPlot(json) {
  data = json;
}

function drawPlot() {
	plot.setData(data);
	plot.setupGrid()
	plot.draw(); 
}


function applySettings(json) {
	options = json;
	//alert(JSON.stringify(json));
	//	alert(lB);
	//	options["series"] = json;
	options["xaxis"]["min"] = eval(options["xaxis"]["min"]);
	options["xaxis"]["max"] = eval(options["xaxis"]["max"]);	
	//document.write(JSON.stringify(options));
	//console.log("Optionen", options);
}

function getLatestTick()
{
	var current = 0;
	jQuery.each(data, function()
	{
		jQuery.each(this["data"], function()
		{
			if(this[0] > current)
			{
				current = this[0];
			}
		});
	});

	return current;
}

function autoUpdateInitial(minutes)
{
  $('.chart').append('<img src="/static/img/ajax-loader.gif" alt="loading ..." class="loadingGIF">');
	$.getJSON('liveData', 
	{
		//last x minutes
		timeframe: minutes
  	},
  	function(returnedJson) {
		data = returnedJson["timeseries"];	
		applySettings(returnedJson["settings"]);
		plot = $.plot($(".chart")[0], data, options);
		if(!crosshair_data_list_created){
		  crosshair_data_list_created = true;
		  dataset = plot.getData();
		  for(i = 0; i < dataset.length; i++){
		    $("#crosshairdata").append('<li style="color:' + dataset[i].color + '">Keine Daten vorhanden</li>');
		  }
	    $(".chart").bind("plothover",  function (event, pos, item) {
	      latestPosition = pos;
	      if(new Date().getTime() - last_time_rendered > 77)
          updateLegend();
      });
      window.onbeforeunload = function () { $('.loadingGIF')[0].style.display = "block"; };
    }
    $('.chart').append('<img src="/static/img/ajax-loader.gif" alt="loading ..." class="loadingGIF" style="display: none;">');
	});
}

function comparator(a, b){
  if (a[0] < b[0]) return -1;
  if (a[0] > b[0]) return 1;
  return 0;
}

function autoUpdate()
{
	var d = new Date();
	if(getLatestTick() != 0){
		console.log("lastTick is: "+getLatestTick());
	  	$.getJSON('liveData', 
	  	{
		  	//get the last tick timestamp from current plot
		  	lastTick: getLatestTick()
    	},
    	function(newData) {
    		console.log("newData is :"+JSON.stringify(newData));
        	var i = 0;
			    jQuery.each(data, function(){
		    		if(newData["timeseries"][i]["data"].length > 0)
		    		{
				        //console.log($("#live_timeframe").val());
				        var oldestTick = this["data"][0][0];
				        var timeframeInMs = $("#live_timeframe").val()*60*1000;
				        var newestTickMinusTimeframe = newData["timeseries"][i]["data"][0][0]-timeframeInMs;

				        /*console.log("Oldest: "+oldestTick);
				        console.log("Timeframeinms: "+timeframeInMs);
				        console.log("Newest: "+newestTickMinusTimeframe);*/

				        while(oldestTick < newestTickMinusTimeframe)
				        {
					        this["data"].shift();
					        oldestTick = this["data"][this["data"].length-1][0];
				        }

				        var y = 0;
				        for(; y < newData["timeseries"][i]["data"].length; y++)
				        {
					        data[i]["data"].unshift(newData["timeseries"][i]["data"][y]);
				        }
				        data[i]["data"] = data[i]["data"].sort(comparator);
				        i++;
				    }
			    });
			drawPlot();
		  	window.setTimeout(autoUpdate, 3000);
	    }).error(function() { console.log("Server Error"); window.setTimeout(autoUpdate, 10000);});
	}else{
	  window.setTimeout(autoUpdate, 500);
	};
}

function updateLegend() {    
    var pos = latestPosition;
    
    var axes = plot.getAxes();
    
    if (pos.x < axes.xaxis.min || pos.x > axes.xaxis.max ||
        pos.y < axes.yaxis.min || pos.y > axes.yaxis.max)
        return;

    var i, j, dataset = plot.getData();
    for (i = 0; i < dataset.length; ++i) {
        var series = dataset[i];
       
       if(series.data.length != 0){
          // find first time that is later than pos.x
          for (j = 0; j < series.data.length && series.data[j][0] < pos.x; ++j);

          // get closest value
          var p, p1 = series.data[j - 1], p2 = series.data[j];
          if(j == 0) // cursor is left of leftmost point -> take first point
            p = p2; 
          else if(j == series.data.length) // cursor is right of rightmost point -> take last point
            p = p1;
          else // cursor is between two points
            if((pos.x - p1[0]) > (p2[0] - pos.x)) // take the point right of the cursor
              p = p2;
             else  // take the point left of the cursor
              p = p1;
              
         var d1 = new Date(p[0]);
         var curr_year = d1.getFullYear();

          var curr_month = d1.getMonth() + 1; //Months are zero based
          if (curr_month < 10)
              curr_month = "0" + curr_month;

          var curr_date = d1.getDate();
          if (curr_date < 10)
              curr_date = "0" + curr_date;
          var newtimestamp = curr_date + "." + curr_month + "." + curr_year;

          var curr_hour = d1.getHours();
          if (curr_hour < 10)
              curr_hour = "0" + curr_hour;
          if(curr_hour != "00")
             newtimestamp += " um " + curr_hour;

          var curr_min = d1.getMinutes();
          if (curr_min < 10)
              curr_min = "0" + curr_min;
          if(curr_min != "00" || d1.getSeconds() != 0)
              newtimestamp += ":" + curr_min;
              
          var curr_sec = d1.getSeconds();     
          if (curr_sec < 10)
              curr_sec = "0" + curr_sec;
          if(curr_sec != "00")
             newtimestamp += ":" + curr_sec;
          if(curr_hour != "00")
             newtimestamp += " Uhr";

         //console.log(dataset[i].label + ": time: " + newtimestamp + ", value: " + y);
         $("#crosshairdata").children()[i].innerHTML = dataset[i].label + " " + newtimestamp + ": " + p[1];
       } else
         $("#crosshairdata").children()[i].innerHTML = "Keine Daten vorhanden";
       last_time_rendered = new Date().getTime();
    }
}
