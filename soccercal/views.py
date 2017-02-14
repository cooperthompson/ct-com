from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from soccercal.models import *
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta, date
from django.core.urlresolvers import reverse
import pdb
import shortuuid
import urllib
import pytz


def home(request):
    leagues = League.objects.filter(is_active=True)
    leagues.prefetch_related('teams')

    today = date.today()
    tomorrow = today + timedelta(days=1)
    todays_games = Game.objects.filter(time__gte=today)
    todays_games = todays_games.filter(time__lt=tomorrow)
    todays_games = todays_games.order_by("time", "field")

    next_week = today + timedelta(days=7)
    upcoming_games = Game.objects.filter(time__gte=tomorrow)
    upcoming_games = upcoming_games.filter(time__lt=next_week)
    upcoming_games = upcoming_games.order_by("time", "field")

    domain = request.build_absolute_uri()
    http_url = urlparse(domain)
    webcal_url = http_url.geturl().replace(http_url.scheme, 'webcal', 1)
    full_ics = '%s%s.ics' % (webcal_url, 'ics/Master')

    leagues = League.objects.filter(name__icontains="coed")
    if leagues is None:
        leagues = League.objects.all()

    if len(leagues) > 0:
        this_league = leagues[0]

    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'leagues': leagues,
        'todays_games': todays_games,
        'upcoming_games': upcoming_games,
        'ics': full_ics,
        'league': this_league
    })
    return HttpResponse(template.render(context))


def team(request, team_id):
    leagues = League.objects.filter(is_active=True)
    leagues.prefetch_related('teams')

    try:
        this_team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return home(request)

    home_games = Game.objects.filter(home_team=this_team)
    away_games = Game.objects.filter(away_team=this_team)

    teams = Team.objects.filter(league=this_team.league)

    games = home_games | away_games
    games = games.order_by("time", "field")

    team_ics = this_team.get_webcal_url(request)

    template = loader.get_template('team.html')
    context = RequestContext(request, {
        'team': this_team,
        'teams': teams,
        'leagues': leagues,
        'games': games,
        'ics': team_ics,
    })
    return HttpResponse(template.render(context))


def league(request, league_id):
    leagues = League.objects.filter(is_active=True)
    leagues.prefetch_related('teams')

    this_league = League.objects.get(id=league_id)
    league_ics = this_league.get_webcal_url(request)

    template = loader.get_template('league.html')
    context = RequestContext(request, {
        'leagues': leagues,
        'league': this_league,
        'ics': league_ics
    })
    return HttpResponse(template.render(context))


def calendar_picker(request):
    teams = Team.objects.all()

    template = loader.get_template('calendar_form.html')
    context = RequestContext(request, {
        'teams': teams
    })
    return HttpResponse(template.render(context))


def calendar_launcher(request):
    team_id = request.GET.get('team')

    this_team = Team.objects.get(id=team_id)
    team_page = reverse('team', args=(team_id,))

    domain = request.build_absolute_uri()
    http_url = urlparse(domain)
    team_webcal = '{0}://{1}{2}{3}.ics'.format('webcal', http_url.netloc, team_page, this_team.slug)

    if request.GET.get('subscribe'):
        cal_url = team_webcal
    if request.GET.get('google'):
        cal_url = "http://www.google.com/calendar/render?{0}".format(urllib.urlencode({'cid': team_webcal}))
    if request.GET.get('online'):
        cal_url = team_page

    template = loader.get_template('calendar_redirector.html')
    context = RequestContext(request, {
        'iframe_redirect_url': cal_url
    })
    return HttpResponse(template.render(context))


def breakaway_mock(request):
    template = loader.get_template('breakaway_mock.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))


def ics(request, team_id=None, team_name=None):

    if team_id:
        this_team = Team.objects.get(id=team_id)
    elif team_name:
        this_team = Team.objects.get(name=team_name)

    home_games = Game.objects.filter(home_team=this_team)
    away_games = Game.objects.filter(away_team=this_team)

    games = home_games | away_games
    games = games.order_by("time", "field")

    cal = Calendar()
    cal.add('prodid', '-//Breakway Schedules//Soccer Calendars//EN')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', this_team.name)
    cal.add('X-WR-TIMEZONE', 'CST6CDT')
    cal.add('X-WR-CALDESC', 'Breakaway Team Schedule')

    now_dt = datetime.now()
    now_string = "%04d%02d%02dT%02d%02d%02d" % (
        now_dt.year,
        now_dt.month,
        now_dt.day,
        now_dt.hour,
        now_dt.minute,
        now_dt.second
    )

    for game in games:
        event = Event()
        try:
            summary = '%s vs. %s' % (game.home_team, game.away_team)
        except Exception:
            summary = 'Breakaway game'

        if game.color_conflict:
            desc = 'Color conflict! (%s vs. %s)' % (game.away_team.color, game.home_team.color)
            summary += ' (color conflict)'
            event.add('description', desc)

        event.add('summary', summary)

        event.add('dtstart', game.time)
        event.add('dtend', game.time + timedelta(hours=1))
        event.add('dtstamp', datetime.now())
        event.add('location', "BreakAway Field %s" % game.field)
        event['uid'] = '%s/%s@breakawaysports.com' % (now_string, shortuuid.uuid())
        event.add('priority', 5)

        alarm = Alarm()
        alarm.add("TRIGGER;RELATED=START", "-PT{0}M".format('45'))
        alarm.add('action', 'display')
        alarm.add('description', 'Breakaway game')

        event.add_component(alarm)
        cal.add_component(event)

    return HttpResponse(cal.to_ical(), content_type='text/calendar')


def master_ics(request):
    cal = Calendar()
    cal.add('prodid', '-//Breakway Schedules//mxm.dk//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', "Breakaway Games")
    cal.add('X-WR-TIMEZONE', 'CST6CDT')
    cal.add('X-WR-CALDESC', 'Breakaway League Schedule')

    now_dt = datetime.now()
    now_string = "%04d%02d%02dT%02d%02d%02d" % (
        now_dt.year,
        now_dt.month,
        now_dt.day,
        now_dt.hour,
        now_dt.minute,
        now_dt.second
    )
    games = Game.objects.filter(home_team__league__is_active=True)
    games = games.order_by("time", "field")
    for game in games:
        event = Event()
        try:
            event.add('summary', '%s vs. %s' % (game.home_team, game.away_team))
        except Exception as e:
            print e
            pdb.set_trace()

        event.add('dtstart', game.time)
        event.add('dtend', game.time + timedelta(hours=1))
        event.add('dtstamp', datetime.now())
        event.add('location', "BreakAway Field %s" % game.field)
        event['uid'] = '%s/%s@breakawaysports.com' % (now_string, shortuuid.uuid())
        event.add('priority', 5)
        cal.add_component(event)

    return HttpResponse(cal.to_ical(), content_type='text/calendar')