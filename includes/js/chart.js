data = [];
options = {};

function drawPlot() {
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

function autoUpdate()
{
	$.getJSON('liveData', function(data) {
		addPlot(data["timeseries"]);
		//document.write(JSON.stringify(data["timeseries"]));
		applySettings(data["settings"]);
	});
}
