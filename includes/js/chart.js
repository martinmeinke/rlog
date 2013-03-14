data = [];
options = {};
liveTicks = 100;

function drawPlot() {
	setTimeout(drawIt, 1000);
	plot = $.plot($(".chart")[0], data, options);
}

function drawIt()
{
	plot = $.plot($(".chart")[0], data, options);
}

function addPlot(json) {
	data = json;
}

function applySettings(json) {
	options = json;
	//alert(JSON.stringify(json));
	//	alert(lB);
	//	options["series"] = json;
	options["xaxis"]["min"] = eval(options["xaxis"]["min"]);
	options["xaxis"]["max"] = eval(options["xaxis"]["max"]);	
	//document.write(JSON.stringify(options));
	drawPlot();
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
  	function(data) {
		addPlot(data["timeseries"]);	
		applySettings(data["settings"]);
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
    		if(newData["timeseries"][0]["data"].length > 0)
			{
	    		var i = 0;
				jQuery.each(data, function()
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
				});
			  	drawPlot();
		  	}
		  	window.setTimeout(autoUpdate, 3000);
	  })
	}else{
	  window.setTimeout(autoUpdate, 500);
	};
}
