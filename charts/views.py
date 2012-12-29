from django.http import HttpResponse
from django.shortcuts import render_to_response
from chart import Chart
from live_chart import LiveChart
import sqlite3
import cgi
import datetime
import time
import json
from dateutil.relativedelta import relativedelta
from django.template import RequestContext
from charts.models import Device

def index(request):
	return live(request)

def live(request):
	return render_to_response('charts/live.html', vars(), RequestContext(request))

def liveData(request):
	#import pdb; pdb.set_trace()
	if 'lastTick' in request.GET:
		last_tick_provided = datetime.datetime.fromtimestamp(int(request.GET["lastTick"])/1000)
		
		graphs = []

		for device in Device.objects.distinct():
			ticks = LiveChart.fetch_and_get_ticks_since(int(device.id), last_tick_provided)
			timetuples = {}
			timetuples.update({device.id : []})
			for tick in ticks:
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

		for device in Device.objects.distinct():
			chart.fetchTimeSeriesLiveView(device.id)
			timetuples = chart.getTimeSeriesLiveView(device.id)
			label = "Einspeisung WR %s (ID: %s)" % (device.model, device.id)
			graphs.append({"label": label, "data":timetuples})

		timeseries = json.dumps(graphs)
		plotsettings = json.dumps(chart.chartOptionsLiveView())
		#print "{'settings': '%s', 'timeseries': '%s'}" % (plotsettings,timeseries)
		
		return HttpResponse("{\"settings\": %s, \"timeseries\": %s}" % (plotsettings,timeseries))

def stats(request):
	#we use the data submitted by the form if empty
	timeframe = request.POST.get('timeframe','timeframe_mon')
	period = request.POST.get('period','period_day')
		
	if timeframe != "timeframe_cus":
		if timeframe == "timeframe_hrs":
			start = datetime.datetime.now()+relativedelta(minute=0, second=0, microsecond=0)
		elif timeframe == "timeframe_day":
			start = datetime.datetime.now()+relativedelta(hour=0, minute=0, second=0, microsecond=0)
		elif timeframe == "timeframe_mon":
			start = datetime.datetime.now()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
		elif timeframe == "timeframe_yrs":
			start = datetime.datetime.now()+relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
			print start
		
		end = datetime.datetime.now()
	else:
		start = datetime.datetime.strptime(request.POST.get('datepickers', datetime.datetime.now()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)), "%m/%d/%Y")
		end = datetime.datetime.strptime(request.POST.get('datepickere', datetime.datetime.now()), "%m/%d/%Y")
		
	heading=str(start)+" - "+str(end)+" | "+str(period)

	chart = Chart(time.mktime(start.timetuple()),time.mktime(end.timetuple()),period)

	graphs = []

	for i in chart.getDeviceIDList():
		chart.fetchTimeSeries(i)
		timetuples = chart.getTimeSeries(i)
		graphs.append({"label":"Einspeisung WR"+str(i), "data":timetuples})

	#graph = {"label":"Einspeisung", "data":timetuples}
	timeseries = json.dumps(graphs)
	plotsettings = json.dumps(chart.chartOptions())
	stats = chart.getStatTable()
	hd = heading

	chart.log.info(timetuples)

	return render_to_response('charts/stats.html', vars(), RequestContext(request))

