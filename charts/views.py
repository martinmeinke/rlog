from django.http import HttpResponse
from django.shortcuts import render_to_response
from chart import Chart
from live_chart import LiveChart
import datetime
from dateutil.tz import tzlocal
import calendar
from django.core.serializers.json import json, DjangoJSONEncoder
from charts.forms import StatsForm, CustomStatsForm
from dateutil.relativedelta import relativedelta
from django.template import RequestContext
from charts.models import Device
from charts.models import SolarEntryTick, SmartMeterEntryTick
from django.utils.translation import ugettext as _

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
    
    chart = LiveChart()
    graphs = []
    ticksWR = None
    ticksSM = None

    if 'lastTick' in request.GET:
        last_tick_provided = datetime.datetime.utcfromtimestamp(int(request.GET["lastTick"])/1000)
        # WR data
        ticksWR = SolarEntryTick.objects.filter(time__gt=last_tick_provided).order_by("time")
        for device in Device.objects.order_by("id").distinct():
            graphs.append({"data": chart.fetchTimeSeriesLiveView(device.id, ticksWR)})
        # smart meter data
        ticksSM = SmartMeterEntryTick.objects.filter(time__gt=last_tick_provided).order_by("-time")
        graphs.append({"data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase1) for tick in ticksSM]})
        graphs.append({"data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase2) for tick in ticksSM]})
        graphs.append({"data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase3) for tick in ticksSM]})
        
        return HttpResponse("{\"timeseries\": %s}" % json.dumps(graphs, cls=DjangoJSONEncoder))
    
    else:
        start = datetime.datetime.now(tzlocal())-relativedelta(minutes=int(request.GET["timeframe"]), second=0, microsecond=0)
        if int(request.GET["timeframe"]) == 1440:
             start = datetime.datetime.now(tzlocal()) + relativedelta(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.datetime.now(tzlocal())
        ticksWR = SolarEntryTick.objects.filter(time__range=(start, end)).order_by('-time')
        ticksSM = SmartMeterEntryTick.objects.filter(time__range=(start, end)).order_by('-time')
        
        for device in Device.objects.order_by("id").distinct():
            timetuples = chart.fetchTimeSeriesLiveView(device.id, ticksWR)
            label = "Erzeugung WR %s (ID: %s)" % (device.model, device.id)
            graphs.append({"label": label, "data":timetuples})
        
        graphs.append({"label" : "Nutzung VSM-102 Phase 1", "data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase1) for tick in ticksSM]})
        graphs.append({"label" : "Nutzung VSM-102 Phase 2", "data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase2) for tick in ticksSM]})
        graphs.append({"label" : "Nutzung VSM-102 Phase 3", "data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase3) for tick in ticksSM]})

        timeseries = json.dumps(graphs, cls=DjangoJSONEncoder)
        plotsettings = json.dumps(chart.chartOptionsLiveView(), cls=DjangoJSONEncoder)
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
                    start = datetime.datetime.strptime(request.POST.get('startfrom', datetime.datetime.now(tzlocal())+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)), "%m/%d/%Y")
                    end = datetime.datetime.strptime(request.POST.get('endby', datetime.datetime.now(tzlocal())), "%m/%d/%Y")
                    
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
                if timeframe == "timeframe_hrs": # I think this has been kicked out
                    start = datetime.datetime.now(tzlocal())+relativedelta(minute=0, second=0, microsecond=0)
                    end = datetime.datetime.now(tzlocal())
                elif timeframe == "timeframe_day":
                    start = datetime.datetime.now(tzlocal()) + relativedelta(hour=0, minute=0, second=0, microsecond=0)
                    end = start + relativedelta(hour = 23, minute = 59)
                elif timeframe == "timeframe_mon":
                    start = datetime.datetime.now(tzlocal())+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end = start + relativedelta(day = calendar.monthrange(start.year, start.month)[1], hour = 23, minute = 59)
                elif timeframe == "timeframe_yrs":
                    start = datetime.datetime.now(tzlocal())+relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    end = start + relativedelta(month = 12, day = calendar.monthrange(start.year, start.month)[1], hour = 23, minute = 59)
        else:
            print "Invalid form input"
            print form.errors
            return render_to_response('charts/stats.html', vars(), RequestContext(request))

    #user navigates to stats from main menu
    else:   
        preselect_period = True     
        timeframe = timeframe_url
        
        #determine start and end date for the chart
        if timeframe != "timeframe_cus":
            if timeframe == "timeframe_hrs":
                start = datetime.datetime.now(tzlocal())+relativedelta(minute=0, second=0, microsecond=0)
                end = datetime.datetime.now(tzlocal())
                period = 'period_min'
            elif timeframe == "timeframe_day":
                start = datetime.datetime.now(tzlocal())-relativedelta(hour=0, minute=0, second=0, microsecond=0)
                end = start + relativedelta(hour = 23, minute = 59)
                period = 'period_min'
            elif timeframe == "timeframe_week":
                start = datetime.datetime.now(tzlocal())-relativedelta(day=7, hour=0, minute=0, second=0, microsecond=0)
                end = start + relativedelta(day = 7, hour = 23, minute = 59)
                period = 'period_day'
            elif timeframe == "timeframe_mon":
                start = datetime.datetime.now(tzlocal())+relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
                end = start + relativedelta(day = calendar.monthrange(start.year, start.month)[1], hour = 23, minute = 59)
                period = 'period_day'
            elif timeframe == "timeframe_yrs":
                start = datetime.datetime.now(tzlocal())+relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end = start + relativedelta(month = 12, day = calendar.monthrange(start.year, start.month)[1], hour = 23, minute = 59)
                period = 'period_mon'  
        else:
            regular_form.fields["timeframe"].initial = timeframe   
            return render_to_response('charts/stats.html', vars(), RequestContext(request))

    #TODO: DRY
    regular_form.fields["timeframe"].initial = timeframe   
    regular_form.fields["period"].initial = period

    #create a chart and fetch its data
    chart = Chart(start, end, period)
    graphs = []

    #custom bar
    #colors = ["","#FF0000", "#00FF00", "#0000FF"]
    #"color":""+colors[i],

    for i in chart.getDeviceIDList():
        chart.fetchTimeSeries(i)
        timetuples = chart.getTimeSeries(i)
        if len(timetuples) > 0:
            graphs.append({"label":_("Erzeugung WR"+str(i)), "data":timetuples, "lines": {"fillColor": "rgba(0,255,0,0.3)"}, "stack":"WR", "bars": {"order": "0"}})
    
    ticksSM = chart.getSmartMeterTimeSeries()
    if len(ticksSM) > 0:
        graphs.append({"label" : "Nutzung Phase 1", "data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase1) for tick in ticksSM], "lines": {"fillColor": "rgba(255,0,0,0.3)"}, "stack":"SmartMeter", "bars": {"order": "1"}})
        graphs.append({"label" : "Nutzung Phase 2", "data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase2) for tick in ticksSM], "lines": {"fillColor": "rgba(255,0,0,0.3)"}, "stack":"SmartMeter", "bars": {"order": "1"}})
        graphs.append({"label" : "Nutzung Phase 3", "data": [(calendar.timegm(tick.time.timetuple()) * 1000, tick.phase3) for tick in ticksSM], "lines": {"fillColor": "rgba(255,0,0,0.3)"}, "stack":"SmartMeter", "bars": {"order": "1"}})

    #sets the boundaries for plotting
    chart.setChartBoundaries()
    timeseries = json.dumps(graphs, cls=DjangoJSONEncoder)

    #print timeseries
    plotsettings = json.dumps(chart.chartOptions(), cls=DjangoJSONEncoder)

    #TODO: the next couple of lines are pretty ugly
    stat_items = chart.getStatItems()
    ui_begin = _("Begin: " + start.strftime(chart._formatstring))
    ui_end = _("End: " + end.strftime(chart._formatstring))
    
    return render_to_response('charts/stats.html', vars(), RequestContext(request))

def overview(request):
    return render_to_response('charts/overview.html', vars(), RequestContext(request))
