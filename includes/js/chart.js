plot = null;
plotdata = [];
options = {};
original_options = {};
latestPosition = null;
last_time_rendered = 0;
checkedItems = {};

function addPlot(json) {
  plotdata = json;
}

function drawPlot(event) {
    var currentData = [];
    if(event)
	    checkedItems[event.target.dataset["id"]] = event.target.checked;
    
    $.each(plotdata, function(idx, data) {
		if (checkedItems[data.label] == true) {
		    currentData.push(data);
		} else {
			currentData.push({label: data.label, data: []});
		}
	});
			

	if (currentData.length > 0) {
        plot = $.plot($(".chart")[0], currentData, options);
        insertCheckboxesIfApplicable();
    }
    
    // add overlay if necessary
    if(plot != null){
        max_len = 0;
        jQuery.each(currentData, function(){
            max_len = currentData.length > max_len ? currentData.length : max_len;
        });
        if(max_len == 0){
            add_disabled_overlay("Es sind momentan keine Daten zur Anzeige verfügbar")
        }else{
            remove_overlay();
        }
    }
}

function insertCheckboxesIfApplicable(){
    $.each(plotdata, function(idx, data) {
        if("bars" in original_options.series){ // disable line selection when using barchart because orderBars.js can't handle missing bars right now
            $(".legendLabel")[idx].innerHTML = data.label + " <span></span>"
        } else {
            var checked = checkedItems[data.label] == true ? "checked='checked' " : "";
            $(".legendLabel")[idx].innerHTML = "<input type='checkbox' name='" + data.label + "' " + 
                checked + "id='id" + data.label + "' data-id='" + data.label + "'></input>" +
		        "<label for='id" + data.label + "'>" + data.label + "</label> <span></span>";
		}
    });
    $(".legend").find("input").click(drawPlot);
}

function add_disabled_overlay(message) {
    var msg_width = message.length * 8;
    var msg_height = 50;

    var canvas_width = $('.chart').first().width();
    var canvas_height = $('.chart').first().height();

    var newCanvas = 
        $('<canvas/>',{'class':'chart_overlay'})
        .width(canvas_width)
        .height(canvas_height);

    $('.chart').first().append(newCanvas);
    var appended = document.getElementsByClassName('chart_overlay')[0];
    appended.width = canvas_width;
    appended.height = canvas_height;
    var ctx=appended.getContext("2d");

    var msg_box_x = canvas_width / 2 - msg_width / 2;
    var msg_box_y = canvas_height / 2 - msg_height / 2;

    ctx.fillStyle = "rgba(200, 200, 200, 0.7)";
    ctx.fillRect(0, 0, canvas_width, canvas_height);

    ctx.fillStyle = "rgba(27, 27, 27, 1)";
    ctx.fillRect(msg_box_x, msg_box_y, msg_width, msg_height);

    ctx.fillStyle = "rgba(255, 255, 255, 1)";
    ctx.font = "16px Arial";
    ctx.fillText(message, msg_box_x + 10, msg_box_y + 30);
    return 0;
}

function remove_overlay() {
    $('.chart_overlay').remove();
}

function applySettings(json) {
	options = json;
	//alert(JSON.stringify(json));
	//	alert(lB);
	//	options["series"] = json;
	options["xaxis"]["min"] = eval(options["xaxis"]["min"]); /* WOOHOOO this is eval :) */
	options["xaxis"]["max"] = eval(options["xaxis"]["max"]);	
	//document.write(JSON.stringify(options));
	//console.log("Optionen", options);
    original_options = options
}

function getLatestTick(){
	var current = 0;
	$.each(plotdata, function(idx, data) { // data sets
	    if(data["data"].length > 0){
			if(data["data"][data["data"].length -1][0] > current){
				current = data["data"][data["data"].length -1][0];
			}
		}
	});
	return current;
}

function autoUpdateInitial(minutes) {
    $('.chart').append('<img src="/static/img/ajax-loader.gif" alt="loading ..." class="loadingGIF">');
	$.getJSON('liveData', {
		    timeframe: minutes
  	    },
  	    function(returnedJson) {
		    plotdata = returnedJson["timeseries"];	
		    applySettings(returnedJson["settings"]);

		    for (i = 0; i < plotdata.length; i++)
		      plotdata[i]["data"] = plotdata[i]["data"].sort(comparator);
		      
		    // fill the checkedItems object
		    $.each(plotdata, function(idx, data) {
		        checkedItems[data.label] = true;
		    });
			
		    drawPlot(null);

	        oneTimeStuffDone = true;

            $(".chart").bind("plothover", function (event, pos, item) {
              latestPosition = pos;
              if(new Date().getTime() - last_time_rendered > 77)
                updateLegend();
            });

            $(".chart").bind("plotselected", function (event, ranges) {
                options = $.extend(true, {}, options, {
                    xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to }
                });
                drawPlot(null);
            });

            $(".chart").bind("plotunselected", function (event) {
                options = original_options;
                drawPlot(null);
            });

            window.onbeforeunload = function () { $('.loadingGIF')[0].style.display = "block"; };
            
            $('.chart').append('<img src="/static/img/ajax-loader.gif" alt="loading ..." class="loadingGIF" style="display: none;">');
	    });
}

function comparator(a, b){
    if (a[0] < b[0]) return -1;
    if (a[0] > b[0]) return 1;
    return 0;
}

// actually this should not be necessary as there are no dups
function removeDuplicates() {
    $.each(plotdata, function(idx, data){
        var dupFree = [];
        $.each(data["data"], function(i, el) {
            if($.inArray(el, dupFree) === -1) dupFree.push(el);
        });
        data["data"] = dupFree;
    });
}

function autoUpdate() {
    console.log("autoUpdate");
	var d = new Date();
	if(getLatestTick() != 0){
		console.log("lastTick is: " + getLatestTick());
	  	$.getJSON('liveData', {
		  	lastTick: getLatestTick()
    	},
    	function(newData) {
    		console.log("newData is :" + JSON.stringify(newData));
		    $.each(plotdata, function(idx, data){
		        /*
		        // sanity check (currently impossible because labels are not transmitted again)
		        if(newData["timeseries"][idx]["label"] != data.label)
		            console.log("WHOOPS: label don't match! idx = " + idx + "data.label = " + data.label + "newData[idx].label = " + newData["timeseries"][idx]["label"]);
		        // contine bussiness		        
		        */
	    		if(newData["timeseries"][idx]["data"].length > 0){ // if there is new data for this device
	    		    if(data.length > 0){ // if there is old data for this device
			            var oldestTick = data[0][0];
			            var timeframeInMs = $("#live_timeframe").val() * 60 * 1000;
			            var oldestTickDeadline = new Date().getTime() - timeframeInMs;

			            while(data["data"].length > 0 && oldestTick < oldestTickDeadline){
				            data["data"].shift();
				            oldestTick = data["data"][0][0];
			            }
			        }
                    data["data"].concat(newData["timeseries"][idx]["data"]);
			        plotdata[idx]["data"] = data["data"].sort(comparator);
			    }
		    });
		    removeDuplicates();
            drawPlot(null);
            updateLegend();
		    window.setTimeout(autoUpdate, 3000);
	    }).error(function() { 
            console.log("Server Error"); 
            window.setTimeout(autoUpdate, 3000);
      });
	} else {
        drawPlot(null);
	    window.setTimeout(autoUpdate, 500);
	}
}

function updateLegend() {
    var pos = latestPosition;
    
    var axes = plot.getAxes();
    
    /* if (pos.x < axes.xaxis.min || pos.x > axes.xaxis.max ||
        pos.y < axes.yaxis.min || pos.y > axes.yaxis.max)
        return;
     */

    var i, j, dataset = plot.getData();
    for (i = 0; i < dataset.length; ++i) {
        var series = dataset[i];
       
       if(series.data.length != 0 && pos != null){
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
         
         //this one gives the date in localtime... we don't want that since we're treating utc as it was localtime
         var d1_tmp = new Date(p[0]);
         //now actually get the localtime
         var d1 = new Date(d1_tmp.getUTCFullYear(), d1_tmp.getUTCMonth(), d1_tmp.getUTCDate(),  d1_tmp.getUTCHours(), d1_tmp.getUTCMinutes(), d1_tmp.getUTCSeconds());

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
         $(".legendLabel span")[i].innerHTML = " am " + newtimestamp + ": " + Math.round(p[1] * 100) / 100;
       } else
         $(".legendLabel span")[i].innerHTML = " Keine Daten vorhanden";
    }
    last_time_rendered = new Date().getTime();
}
