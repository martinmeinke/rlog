from django.http import HttpResponse
from django.shortcuts import render_to_response
from chart import Chart
from live_chart import LiveChart
import sqlite3
import cgi
import datetime
import time
import json
from charts.forms import StatsForm
from dateutil.relativedelta import relativedelta
from django.template import RequestContext
from charts.models import Device
from charts.models import SolarEntryTick

def index(request):
	return live(request)

def live(request):
	return render_to_response('charts/live.html', vars(), RequestContext(request))

def liveData(request):
	#import pdb; pdb.set_trace()
	#import logging
	#l = logging.getLogger('django.db.backends')
	#l.setLevel(logging.DEBUG)
	#l.addHandler(logging.StreamHandler())

	if 'lastTick' in request.GET:
		last_tick_provided = datetime.datetime.fromtimestamp(int(request.GET["lastTick"])/1000)
		
		graphs = []

		ticks = SolarEntryTick.objects.filter(time__gt=last_tick_provided).order_by("-time")
		for device in Device.objects.distinct():
			#ticks = LiveChart.fetch_and_get_ticks_since(int(device.id), last_tick_provided)
			timetuples = {}
			timetuples.update({device.id : []})

			tempid = tick.device.id
			for tick in ticks:
				if tempid == device.id:
					t = (time.mktime(tick.time.timetuple()) * 1000, int(tick.lW))
					timetuples[device.id].append(t)
			graphs.append({"data": timetuples[device.id]})

		timeseries = json.dumps(graphs)
		return HttpResponse("{\"timeseries\": %s}" % timeseries)

	else:
		#perform the chart initialization
		start = datetime.datetime.utcnow()-relativedelta(minutes=int(request.GET["timeframe"]), second=0, microsecond=0)
		end = datetime.datetime.utcnow()

		chart = LiveChart(start, end)
		graphs = []

		ticks = SolarEntryTick.objects.filter(time__range=(start, end)).order_by('-time')

		for device in Device.objects.distinct():
			chart.fetchTimeSeriesLiveView(device.id, ticks)
			timetuples = chart.getTimeSeriesLiveView(device.id)
			label = "Einspeisung WR %s (ID: %s)" % (device.model, device.id)
			graphs.append({"label": label, "data":timetuples})

		timeseries = json.dumps(graphs)
		plotsettings = json.dumps(chart.chartOptionsLiveView())
		#print "{'settings': '%s', 'timeseries': '%s'}" % (plotsettings,timeseries)
		
		return HttpResponse("{\"settings\": %s, \"timeseries\": %s}" % (plotsettings,timeseries))

def stats(request, timeframe_url):
	#get form data
	if request.method == 'POST':
		form = StatsForm(request.POST)
		if form.is_valid():
			timeframe = form.cleaned_data["timeframe"]
			period = form.cleaned_data["period"]
		else:
			print "Invalid form input"
	else:		
		timeframe = 'timeframe_day'
		period = 'period_hrs'
		
	#determine start and end date for the chart
	if timeframe != "timeframe_cus":
		if timeframe == "timeframe_hrs":
			start = datetime.datetime.utcnow()+relativedelta(minute=0, second=0, microsecond=0)
		elif timeframe == "timeframe_day":
			start = datetime.datetime.utcnow()+relativedelta(hour=0, minute=0, second=0, microsecond=0)
		elif timeframe == "timeframe_mon":
			start = datetime.datetime.utcnow()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
		elif timeframe == "timeframe_yrs":
			start = datetime.datetime.utcnow()+relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
			print start
		
		end = datetime.datetime.utcnow()
	else:
		start = datetime.datetime.strptime(request.POST.get('datepickers', datetime.datetime.now()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)), "%m/%d/%Y")
		end = datetime.datetime.strptime(request.POST.get('datepickere', datetime.datetime.now()), "%m/%d/%Y")
		
	#create a chart and fetch its data
	chart = Chart(start, end, period)
	graphs = []

	for i in chart.getDeviceIDList():
		chart.fetchTimeSeries(i)
		timetuples = chart.getTimeSeries(i)
		graphs.append({"label":"Einspeisung WR"+str(i), "data":timetuples})

	timeseries = json.dumps(graphs)
	plotsettings = json.dumps(chart.chartOptions())

	#TODO: the next couple of lines are pretty ugly
	stats = chart.getStatTable()
	hd =str(start)+" - "+str(end)+" | "+str(period)
	form = StatsForm()

	#set the initial selection to what the url gave us
	form.fields["timeframe"].initial = timeframe_url
	
	return render_to_response('charts/stats.html', vars(), RequestContext(request))

def overview(request):
	return render_to_response('charts/overview.html', vars(), RequestContext(request))
