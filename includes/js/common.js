$(document).ready(function() {
  		timezoneJS.timezone.zoneFileBasePath = '/static/timezones';
	    timezoneJS.timezone.defaultZoneFile = 'europe';
	    timezoneJS.timezone.init({async: false});
	/*
	 * $("#header").mouseover(function() { $("#header").animate({
	 * "margin-top":"0px" }, 500 ); $("#header").clearQueue();
	 * }).mouseout(function() { $("#header").animate({ "margin-top":"-100px" },
	 * 500 ); $("#header").clearQueue(); });
	 */

	$(".menuitem").mouseenter(function(event) {
		$(event.target).animate({
			"margin-left" : "100px"
		}, 500);
		$(".menuitem").clearQueue();
	}).mouseleave(function(event) {
		$(event.target).animate({
			"margin-left" : "0px"
		}, 500);
		$(".menuitem").clearQueue();
	});

	//$("#timeframe").buttonset();
	$("input[name='timeframe']").change(function() {
		if ($("#timeframe_cus").is(':checked')) {
			$("#datepickerArea").css("display", "block");
		} else {
			$("#datepickerArea").css("display", "none");
		}
	});

	//$("#period").buttonset();
	//$("#live_timeframe").buttonset();

	$("#checkGraph").button();
	$("#checkStats").button();
	$("#checkList").button();

	$("input:submit").button();

	/*
	 * $("#datepickers").datepicker({ showButtonPanel : true, changeMonth :
	 * true, changeYear : true }); $("#datepickere").datepicker({
	 * showButtonPanel : true, changeMonth : true, changeYear : true });
	 */

	htmlDatePickerize($("#datepickers"));
	htmlDatePickerize($("#datepickere"));

	$(".datePicker").datepicker();

	/*$("#header").tabs({
		collapsible : true
	});

	$("#stats").tabs({
		collapsible : true
	});*/
});

function htmlDatePickerize(selector) {
	$(selector).each(function(e) {
		var dateValue = $(this).attr('value');
		var formName = $(this).attr('name');
		var hiddenInput = document.createElement('input');
		hiddenInput.name = formName;
		hiddenInput.value = dateValue;
		hiddenInput.type = 'hidden';
		$(this).after(hiddenInput);
		$(this).datepicker({
			showButtonPanel : true,
			changeMonth : true,
			changeYear : true,
			onSelect : function(dateText, inst) {
				hiddenInput.value = dateText;
			}
		}).datepicker("setDate", dateValue);
	});
}

/*
create the choices
*/
function update_period_choices(timeframe, set_current, period)
{
	if(set_current)
		console.log("SET CURREN");

	var hrsOptions = {
	    "period_min" : "Minuetlich"
	};

	var dayOptions = {
	    "period_min" : "Minuetlich",
        "period_hrs" : "Stuendlich"
	};

	var monOptions = {
        "period_hrs" : "Stuendlich",
        "period_day" : "Taeglich"
	};

	var yrsOptions = {
        "period_day" : "Taeglich",
        "period_mon" : "Monatlich"
	};

	var cusOptions = {
	    "period_min" : "Minuetlich",
        "period_hrs" : "Stuendlich",
        "period_day" : "Taeglich",
        "period_mon" : "Monatlich",
        "period_yrs" : "Jaehrlich"
	};

	var select = $('#id_period');
	var options = select.prop('options');

	$('option', select).remove();

	if(timeframe == "timeframe_hrs")
	{
		$.each(hrsOptions, function(val, text) {
		    options[options.length] = new Option(text, val);
		});

		if(set_current)
		{
			$('#id_period').val("period_min");
		}else{
			$('#id_period').val(period);
		}
	}else if(timeframe == "timeframe_day")
	{
		$.each(dayOptions, function(val, text) {
		    options[options.length] = new Option(text, val);
		});

		if(set_current)
		{
			$('#id_period').val("period_hrs");
		}else{
			$('#id_period').val(period);
		}
	}else if(timeframe == "timeframe_mon")
	{
		$.each(monOptions, function(val, text) {
		    options[options.length] = new Option(text, val);
		});

		if(set_current)
		{
			$('#id_period').val("period_day");
		}else{
			$('#id_period').val(period);
		}
	}else if(timeframe == "timeframe_yrs")
	{
		$.each(yrsOptions, function(val, text) {
		    options[options.length] = new Option(text, val);
		});

		if(set_current)
		{
			$('#id_period').val("period_mon");
		}else{
			$('#id_period').val(period);
		}
	}
	else if(timeframe == "timeframe_cus")
	{
		$.each(cusOptions, function(val, text) {
		    options[options.length] = new Option(text, val);
		});

		if(set_current)
		{
			$('#id_period').val("period_day");
		}else{
			$('#id_period').val(period);
		}
	}
}

function check_custom_timeframe(set_current, period)
{
	console.log("sel");
	var selected_timeframe = $("#id_timeframe option:selected").val();

	if(selected_timeframe == "timeframe_cus"){
		$(".custom_date_area").css("display", "block");
	}else{
		$(".custom_date_area").css("display", "none");
		update_period_choices(selected_timeframe, set_current, period);
	}
}