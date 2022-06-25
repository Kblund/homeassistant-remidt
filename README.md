#Homeassistant-ReMidt Søppeltømming

##ReMidt Søppeltømming

Laget av Bolme123

Benytter API levert av ReMidt og Python requests for å hente tømmedager for søpla.
###Konfigurasjon

For å bruke må du taste inn 2 felt i 'configuration.yaml'-fila på ditt Home Assistant-system.

    CONF_ADDRESS
    CONF_KOMMUNE

Om dette ikke er opplagt så skal du da taste inn addresse og kommune til plassen du ønsker å hente tømmekalender fra.

Ellers er den lite konfigurerbar. frivillige felt du kan ta med er:

    CONF_UPDATE_FREQUENCY - Styrer hvor ofte den skal sende HTTP-forespørsel
    CONF_ID - Gir entiteten et unikt navn på Home Assistant

Enjoy
###Bugs

Det var noen men kommer ikke på nå som jeg skriver
###Kilder

ReMidt API endpoint - https://kalender.renovasjonsportal.no/main
