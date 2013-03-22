$(document).ready(function() {

	timezoneJS.timezone.zoneFileBasePath = '/static/timezones';
	timezoneJS.timezone.defaultZoneFile = 'europe';
	timezoneJS.timezone.init();
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
