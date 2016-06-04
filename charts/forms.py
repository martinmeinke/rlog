from django import forms
from django.forms import extras
from django.core.exceptions import ValidationError

class StatsForm(forms.Form):
    timeframe = forms.ChoiceField(
    	choices = [
    		["timeframe_day", "Heute"],
    		["timeframe_mon", "Diesen Monat"],
    		["timeframe_week", "Diese Woche"],
    		["timeframe_yrs", "Dieses Jahr"],
    		["timeframe_cus", "Anderer Zeitraum"]
    	],
    	initial = "timeframe_mon",
    	label = "Zeitraum",
        required = True,
        widget=forms.Select(attrs={'onchange': 'check_custom_timeframe(0, 0)'})
    )    
    period = forms.ChoiceField(
    	choices = [
                ["period_tick", "Ticks"],
    		["period_min", "Minuetlich"],
    		["period_hrs", "Stuendlich"],
    		["period_day", "Taeglich"],
    		["period_mon", "Monatlich"],
    		["period_yrs", "Jaehrlcih"]
    	], 
    	initial = "period_day",
    	label = "Periode",
        required = True
    ) 

class CustomStatsForm(forms.Form):
    startfrom = forms.DateField(
        label = "Beginn",
        input_formats=['%d/%m/%Y', '%m/%d/%Y',], 
        widget=forms.DateInput(format = '%m/%d/%Y'),
        required = True
    )
    startfrom.widget.attrs.update({'class':'datePicker'})

    endby = forms.DateField(
        label = "Ende",
        input_formats=['%d/%m/%Y', '%m/%d/%Y',], 
        widget=forms.DateInput(format = '%m/%d/%Y'),
        required = True
    )
    endby.widget.attrs.update({'class':'datePicker'})
