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
    ATTR_TOMMING_ETTER,
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
        self._dataplast = []
        self._datapapir = []
        self.dates = None
        self.update = Throttle(update_frequency)(self._update)
        self._name = SENSOR_PREFIX + (id_name + " " if len(id_name) > 0  else "")
        self._icon = "mdi:delete"
        self._device_class = 'timestamp'
        self._state = None
        self._last_update = None
        self._papir = None
        self._restavfall = None
        self._etter_neste_tomming = None
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
       


    def getDays(self):
        _LOGGER.debug(self.address_ID)
        baseline_url = (
            API_ENDPOINT
            )

        full_url = baseline_url + self.address_ID + "/details"
        r = requests.get(full_url)
        _LOGGER.debug(full_url)
        _LOGGER.debug(r.json())
        disposalDays = []
        disposals = r.json()["disposals"]
        for day in disposals:
            disposalDays.append(day)
            if len(disposalDays) > 1:
                if disposalDays[-1]["date"] == disposalDays[-2]["date"]:
                    bin = [disposalDays[-1]["fraction"],disposalDays[-2]["fraction"]]
                    disposalDays.pop()
                    newDisposalObject = " & ".join(bin)
                    disposalDays[-1]["fraction"] = newDisposalObject
        return disposalDays

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
    def extra_state_attributes(self):
        return {
        ATTR_LAST_UPDATE: self._last_update,
        ATTR_NESTE_TOMMING: self._neste_tomming,
        ATTR_TOMMING_ETTER: self._etter_neste_tomming
        }
        

    
    def Prerequisites(self):
        self._last_update = (datetime.now()).strftime("%d-%m-%Y %H:%M")
        if self.address_ID == '':
            self.getAddressID()
        return self.getDays()
        
    
    def _update(self):
        disposalDays = self.Prerequisites()
        now= datetime.now()
        first = datetime.strptime(disposalDays[0]["date"][0:10]+":10","%Y-%m-%d:%H")
        if first <= now:
            disposalDays.pop(0)
        next = disposalDays[0]
        after_next = disposalDays[1]
        disposal_date = datetime.strptime(next['date'][0:10],"%Y-%m-%d")
        disposalDay = (disposal_date-now).days
        disposalItem = next["fraction"]
        self._state = next["date"][0:10]+"T10:00:00"
        self._neste_tomming = disposalItem
        self._etter_neste_tomming = f'{after_next["date"][0:10]}\n{after_next["fraction"]}'