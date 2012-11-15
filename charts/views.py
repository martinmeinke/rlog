from django.http import HttpResponse
from django.shortcuts import render_to_response
from chart import Chart
import sqlite3
import cgi
import datetime
import time
import json
from dateutil.relativedelta import relativedelta
from django.template import RequestContext

def index(request):
	return live(request)

def live(request):
	return render_to_response('charts/live.html', vars(), RequestContext(request))

def liveData(request):
	import pdb; pdb.set_trace()
	start = datetime.datetime.now()-relativedelta(minutes=30, second=0, microsecond=0)
	end = datetime.datetime.now()

	chart = Chart(time.mktime(start.timetuple()),time.mktime(end.timetuple()),"period_min")

	graphs = {}

	for i in chart.getDeviceIDList():
		chart.fetchTimeSeriesLiveView(i)
		timetuples = chart.getTimeSeriesLiveView(i)
		graphs.update({"label":"Einspeisung #"+str(i), "data":timetuples});

	timeseries = json.dumps(graphs)
	plotsettings = json.dumps(chart.chartOptionsLiveView())

	print "{'settings': '%s', 'timeseries': '%s'}" % (plotsettings,timeseries)
	
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
	chart.fetchTimeSeries()

	timetuples = chart.getTimeSeries()
	graph = {"label":"Einspeisung", "data":timetuples}
	timeseries = json.dumps(graph)
	plotsettings = json.dumps(chart.chartOptions())
	stats = chart.getStatTable()
	hd = heading

	chart.log.info(timetuples)

	return render_to_response('charts/stats.html', vars(), RequestContext(request))

