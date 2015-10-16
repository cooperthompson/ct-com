from datetime import date
from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from urlparse import urlparse


class Organization(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Season(models.Model):
    name = models.CharField(max_length=100)
    iscurrent = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class League(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    season = models.ForeignKey('Season', related_name='leagues', null=True, blank=True)
    org = models.ForeignKey('Organization', related_name='org', null=True, blank=True)
    key = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s" % self.name

    def get_webcal_url(self, request):
        if request:
            domain = request.build_absolute_uri()
            self.domain = domain

        http_url = urlparse(domain)
        webcal_url = http_url.geturl().replace(http_url.scheme, 'webcal', 1)

        return '%s%s.ics' % (webcal_url, self.name.replace(' ', '_'))


class Team(models.Model):
    number = models.IntegerField()
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    color = models.CharField(max_length=100)
    league = models.ForeignKey('League', related_name='teams')

    class Meta:
        ordering = ['number']

    def __unicode__(self):
        return u"[%s] %s" % (self.number, self.name)

    # TODO: refactor into base class
    def get_webcal_url(self, request):
        if request:
            domain = request.build_absolute_uri()
            self.domain = domain

        http_url = urlparse(domain)
        webcal_url = http_url.geturl().replace(http_url.scheme, 'webcal', 1)
        return '%s%s.ics' % (webcal_url, self.slug)


class Game(models.Model):
    league = models.ForeignKey(League)
    home_team = ChainedForeignKey(Team,
                                  chained_field='league',
                                  chained_model_field='league',
                                  related_name='home_team')
    away_team = ChainedForeignKey(Team,
                                  chained_field='league',
                                  chained_model_field='league',
                                  related_name='away_team')

    time = models.DateTimeField()
    field = models.IntegerField(default=1)

    @property
    def is_today(self):
        if self.time.date() == date.today():
            return True
        else:
            return False

    @property
    def color_conflict(self):
        if self.home_team.color.upper() == self.away_team.color.upper():
            return True
        else:
            return False

    class Meta:
        ordering = ['time']

    def __unicode__(self):
        return u"%s vs. %s @ %s" % (self.home_team.name, self.away_team.name, self.time)
