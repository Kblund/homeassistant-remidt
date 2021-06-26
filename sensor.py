#!/usr/bin/env python3
"""
Sensor component for Cryptoinfo
Author: Johnny Visser

ToDo:
- Add documentation and reference to coingecko
- Add to hacs repo
https://api.coingecko.com/api/v3/simple/price?ids=neo&vs_currencies=usd
https://api.coingecko.com/api/v3/simple/price?ids=neo&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true
"""

import requests
import voluptuous as vol
from datetime import datetime, date, timedelta
import urllib.error

from .const.const import (
    _LOGGER,
    CONF_ADDRESS,
    CONF_KOMMUNE,
    CONF_UPDATE_FREQUENCY,
    SENSOR_PREFIX,
    ATTR_LAST_UPDATE,
    ATTR_PAPIR,
    ATTR_RESTAVFALL,
    ATTR_NESTE_TOMMING,
    API_ENDPOINT,
    CONF_ID,
)

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_RESOURCES
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

# NSR:StopPlace:43964 = Buvika
# NSR:StopPlace:41660 = Torget Orkanger
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS, default="Tverrvegen 6B"): cv.string,
        vol.Required(CONF_KOMMUNE, default="Skaun"): cv.string,
        vol.Required(CONF_UPDATE_FREQUENCY, default=60): cv.string,
        vol.Optional(CONF_ID, default = ""): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup ReMidt sensor")

    id_name = config.get(CONF_ID)
    address = config.get(CONF_ADDRESS).lower().strip()
    kommune = config.get(CONF_KOMMUNE).lower().strip()
    update_frequency = timedelta(minutes=(int(config.get(CONF_UPDATE_FREQUENCY))))

    entities = []

    try:
        entities.append(
            ReMidtsensor(
                address, kommune, update_frequency, id_name
            )
        )
    except urllib.error.HTTPError as error:
        _LOGGER.error(error.reason)
        return False

    add_entities(entities)

class ReMidtsensor(Entity):
    def __init__(
        self, address, kommune, update_frequency, id_name
    ):
        self.address = address
        self.address_ID = ''
        self.kommune = kommune
        self._datarest = []
        self._datapapir = []
        self.dates = None
        self.update = Throttle(update_frequency)(self._update)
        self._name = SENSOR_PREFIX + (id_name + " " if len(id_name) > 0  else "")
        self._icon = "mdi:bus"
        self._device_class = 'timestamp'
        self._state = None
        self._last_update = None
        self._papir = None
        self._restavfall = None
        self._neste_tomming = None

    def getAddressID(self):
        baseline_url = (
            API_ENDPOINT
            )
        alternate = 'alternateSearchResults'
        full_url = baseline_url + self.address.replace(' ', '%20')
        _LOGGER.debug(full_url)
        r = requests.get(full_url)
        multipleaddresses= list(r.json())[0] #Første nøkkel i dictionary, 'SearchResults'
        if len(r.json()[multipleaddresses]):
            alternate = 'searchResults'
        if len(r.json()[alternate]) == 0:
            raise ValueError("The address returns no match")

        for address in r.json()[alternate]:
            if self.kommune in address['subTitle'].lower():
                self.address_ID = address['id']
                _LOGGER.debug(self.address_ID)
        self.getDays()


    def getDays(self):
        _LOGGER.debug(self.address_ID)
        baseline_url = (
            API_ENDPOINT
            )

        full_url = baseline_url + self.address_ID + "/details"
        r = requests.get(full_url)
        _LOGGER.debug(full_url)
        _LOGGER.debug(r.json())
        disposals = r.json()["disposals"]
        for day in disposals:
            if day["fraction"] == "Restavfall":
                self._datarest.append(day)
            elif day["fraction"] == "Papir og plastemballasje":
                self._datapapir.append(day)


    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._state

    @property
    def device_class(self):
        return self._device_class


    @property
    def device_state_attributes(self):
        return {
        ATTR_LAST_UPDATE: self._last_update,
        ATTR_RESTAVFALL: self._restavfall,
        ATTR_PAPIR: self._papir,
        ATTR_NESTE_TOMMING: self._neste_tomming
        }

    def _update(self):
        self._last_update = (datetime.now() + timedelta(hours =2)).strftime("%d-%m-%Y %H:%M")
        if self.address_ID == '':
            self.getAddressID()
        baseline_url = (
            API_ENDPOINT
            )

        now= datetime.now()
        for k in self._datapapir[0], self._datarest[0]:
            if (datetime.now() - datetime.strptime(k['date'][0:10], "%Y-%m-%d") ).days > 0:
                _LOGGER.debug(self._datapapir)
                if k in self._datapapir[0]:
                    self._datapapir.clear()
                elif k in self._datarest[0]:
                    self._datarest.clear()
                return
                
            disposal_date = datetime.strptime(k['date'][0:10], "%Y-%m-%d")
            disposalDay = (disposal_date-now).days
            disposalItem = k["fraction"]
            if disposalItem == "Restavfall":
                self._restavfall = disposal_date
            else:
                self._papir = disposal_date

        if self._datapapir[0]['date'] < self._datarest[0]['date']:
            tid = datetime.strptime(self._datapapir[0]['date'][0:10], "%Y-%m-%d")
            disposaldays = (tid-now).days
            self._state = self._papir
            self._neste_tomming = 'Papir og plastemballasje'
        else:
            tid = datetime.strptime(self._datarest[0]['date'][0:10], "%Y-%m-%d")
            disposaldays = (tid-now).days
            self._state = self._restavfall
            self._neste_tomming = 'Restavfall'
