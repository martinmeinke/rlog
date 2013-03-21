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
		    $("#crosshairdata").append('<li style="color:' + dataset[i].color + '">Test</li>');
		  }
	    $(".chart").bind("plothover",  function (event, pos, item) {
	      latestPosition = pos;
	      if(new Date().getTime() - last_time_rendered > 77)
          updateLegend();
      });
    }
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

        // find the nearest points, x-wise
        for (j = 0; j < series.data.length; ++j)
            if (series.data[j][0] > pos.x)
                break;
        
        // now interpolate
        var y, p1 = series.data[j - 1], p2 = series.data[j];
        if (p1 == null)
            y = p2[1];
        else if (p2 == null)
            y = p1[1];
        else
            y = p1[1] + (p2[1] - p1[1]) * (pos.x - p1[0]) / (p2[0] - p1[0]);

       var d1 = new Date(pos.x);
       var curr_year = d1.getFullYear();

        var curr_month = d1.getMonth() + 1; //Months are zero based
        if (curr_month < 10)
            curr_month = "0" + curr_month;

        var curr_date = d1.getDate();
        if (curr_date < 10)
            curr_date = "0" + curr_date;

        var curr_hour = d1.getHours();
        if (curr_hour < 10)
            curr_hour = "0" + curr_hour;

        var curr_min = d1.getMinutes();
        if (curr_min < 10)
            curr_min = "0" + curr_min;

        var curr_sec = d1.getSeconds();     
        if (curr_sec < 10)
            curr_sec = "0" + curr_sec;

        var newtimestamp = curr_date + "." + curr_month + "." + curr_year + " um " + curr_hour + ":" + curr_min + ":" + curr_sec + " Uhr";
       //console.log(dataset[i].label + ": time: " + newtimestamp + ", value: " + y);
       $("#crosshairdata").children()[i].innerHTML =  dataset[i].label + " " + newtimestamp + ": " + y.toFixed(2);
       last_time_rendered = new Date().getTime();
    }
}
