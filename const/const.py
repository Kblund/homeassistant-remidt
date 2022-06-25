import logging



SENSOR_PREFIX = "ReMidt "
CONF_ID = "id"
CONF_ADDRESS = "address"
CONF_KOMMUNE = "kommune"
CONF_UPDATE_FREQUENCY = "update_frequency"

ATTR_LAST_UPDATE = "last_update"
ATTR_PAPIR = "papir"
ATTR_RESTAVFALL = "restavfall"
ATTR_NESTE_TOMMING= "neste_tømming"
ATTR_TOMMING_ETTER ="etter_neste_tømming"

API_ENDPOINT = "https://kalender.renovasjonsportal.no/api/address/"

_LOGGER = logging.getLogger(__name__)
