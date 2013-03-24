from django import forms

class StatsForm(forms.Form):
    timeframe = forms.ChoiceField(
    	choices = [
    		["timeframe_day", "Heute"],
    		["timeframe_mon", "Diesen Monat"],
    		["timeframe_yrs", "Dieses Jahr"],
    		["timeframe_cus", "Anderer Zeitraum"]
    	],
    	initial = "timeframe_mon",
    	label = "Zeitraum",
        widget=forms.Select(attrs={'onchange': 'if($("#id_timeframe option:selected").val() == "timeframe_cus"){$("#custom_date_area").css("display", "block")}else{$("#custom_date_area").css("display", "none")}'})
    )    
    period = forms.ChoiceField(
    	choices = [
    		["period_min", "Minuetlich"],
    		["period_hrs", "Stuendlich"],
    		["period_day", "Taeglich"],
    		["period_mon", "Monatlich"],
    		["period_yrs", "Jaehrlcih"]
    	], 
    	initial = "period_day",
    	label = "Periode"
    )    