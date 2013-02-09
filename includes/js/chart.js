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
				current = this[0]
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
		//document.write(JSON.stringify(data["timeseries"]));
		applySettings(data["settings"]);
	});
}

function autoUpdate()
{
	var d = new Date();
	$.getJSON('liveData', 
	{
		//get the last tick timestamp from current plot
		lastTick: getLatestTick()
  	},
  	function(newData) {
  		var i = 0;
		jQuery.each(data, function()
		{
			//alert(JSON.stringify(newData["timeseries"][i]["data"]))
			this["data"] = newData["timeseries"][i]["data"].concat(this["data"]);
			i++;
		});
		drawPlot();
	});
}
