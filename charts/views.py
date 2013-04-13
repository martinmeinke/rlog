from django.http import HttpResponse
from django.shortcuts import render_to_response
from chart import Chart
from live_chart import LiveChart
import sqlite3
import cgi
import datetime
import time
import json
from charts.forms import StatsForm, CustomStatsForm
from dateutil.relativedelta import relativedelta
from django.template import RequestContext
from charts.models import Device
from charts.models import SolarEntryTick
import calendar

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
        last_tick_provided = datetime.datetime.utcfromtimestamp(int(request.GET["lastTick"])/1000)
        
        graphs = []

        ticks = SolarEntryTick.objects.filter(time__gt=last_tick_provided).order_by("-time")
        for device in Device.objects.distinct():
            #ticks = LiveChart.fetch_and_get_ticks_since(int(device.id), last_tick_provided)
            timetuples = {}
            timetuples.update({device.id : []})

            for tick in ticks:
                if tick.device_id == device.id:
                    t = (calendar.timegm(tick.time.utctimetuple()) * 1000, int(tick.lW))
                    timetuples[device.id].append(t)
            graphs.append({"data": timetuples[device.id]})

        timeseries = json.dumps(graphs)
        return HttpResponse("{\"timeseries\": %s}" % timeseries)

    else:
        #perform the chart initialization
        start = datetime.datetime.today()-relativedelta(minutes=int(request.GET["timeframe"]), second=0, microsecond=0)
        end = datetime.datetime.today()

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
    regular_form = StatsForm()
    custom_form = CustomStatsForm()

    #get form data if user already has been on stats page
    if request.method == 'POST':
        form = StatsForm(request.POST)
        if form.is_valid():
            timeframe = form.cleaned_data["timeframe"]
            period = form.cleaned_data["period"]

            if(timeframe == "timeframe_cus"):
                custom_stats_form = CustomStatsForm(request.POST)
                if custom_stats_form.is_valid():
                    start = datetime.datetime.strptime(request.POST.get('startfrom', datetime.datetime.today()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)), "%m/%d/%Y")
                    end = datetime.datetime.strptime(request.POST.get('endby', datetime.datetime.today()), "%m/%d/%Y")
                    
                    custom_form.fields["startfrom"].initial = start
                    custom_form.fields["endby"].initial = end
                    
                    #we usually mean the end of that day
                    end += relativedelta(days=1, hour=0, minute=0, second=0, microsecond=0) 
                    end -= relativedelta(day=0, hour=0, minute=0, seconds=1, microsecond=0)

                else:
                    print "Invalid form input"
                    print form.errors
                    return render_to_response('charts/stats.html', vars(), RequestContext(request))
            else:
                if timeframe == "timeframe_hrs":
                    start = datetime.datetime.today()+relativedelta(minute=0, second=0, microsecond=0)
                elif timeframe == "timeframe_day":
                    if period == 'period_min' or period == 'period_hrs':
                        localTime = datetime.datetime.today()
                        localMidnight = datetime.datetime.combine(localTime, datetime.time(0))
                        timeSinceStartOfDay = localTime - localMidnight
                        start = datetime.datetime.today() - timeSinceStartOfDay # local midnight in UTC
                    else:
                        start = datetime.datetime.today() + relativedelta(hour=0, minute=0, second=0, microsecond=0) # UTC midnight (1:00 here in Germany))
                elif timeframe == "timeframe_mon":
                    start = datetime.datetime.today()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
                elif timeframe == "timeframe_yrs":
                    start = datetime.datetime.today()+relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end = datetime.datetime.today()
        else:
            print "Invalid form input"
            print form.errors
            return render_to_response('charts/stats.html', vars(), RequestContext(request))

    #user navigates to stats from main menu
    else:        
        timeframe = timeframe_url
        
        #determine start and end date for the chart
        if timeframe != "timeframe_cus":
            if timeframe == "timeframe_hrs":
                start = datetime.datetime.today()+relativedelta(minute=0, second=0, microsecond=0)
                period = 'period_min'
            elif timeframe == "timeframe_day":
                start = datetime.datetime.today()+relativedelta(hour=0, minute=0, second=0, microsecond=0)
                period = 'period_hrs'
            elif timeframe == "timeframe_mon":
                start = datetime.datetime.today()+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
                period = 'period_day'
            elif timeframe == "timeframe_yrs":
                start = datetime.datetime.today()+relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                period = 'period_mon'  
            end = datetime.datetime.today()
        else:
            regular_form.fields["timeframe"].initial = timeframe   
            return render_to_response('charts/stats.html', vars(), RequestContext(request))

    #TODO: DRY
    regular_form.fields["timeframe"].initial = timeframe   
    regular_form.fields["period"].initial = period

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
    
    return render_to_response('charts/stats.html', vars(), RequestContext(request))

def overview(request):
    return render_to_response('charts/overview.html', vars(), RequestContext(request))
