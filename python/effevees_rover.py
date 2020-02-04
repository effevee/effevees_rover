#!/usr/bin/python

# Frank Vergote
# email effevee@gmail.com
# WebIOPi rover versie 5
# 06/05/2016

###############################################################################
# Bibliotheken
###############################################################################

import webiopi
import time
import threading
# import logging
import random

# gebruik de gpio lib van WebIOPi voor de interactie met de gpio pinnen
gpio = webiopi.GPIO

###############################################################################
# Constanten en variabelen
###############################################################################

# GPIO poorten voor sturen motoren via L298N motor module
# -------------------------------------------------------
# Motor            LINKS               RECHTS
# GPIO          IN1     IN2         IN3     IN4
# -------------------------------------------------------
# Vooruit       low     high        low     high
# Stoppen       low     low         low     low
# Achteruit     high    low         high    low
# -------------------------------------------------------
L298N_IN1 = 17          # richting motoren links
L298N_IN2 = 18          # richting motoren links
L298N_ENA = 24          # snelheid motoren links (PWM)

L298N_IN3 = 22          # richting motoren rechts
L298N_IN4 = 23          # richting motoren rechts
L298N_ENB = 25          # snelheid motoren rechts (PWM)

# commando's motoren
VOORUIT = 1
STOPPEN = 2
ACHTERUIT = 3
LINKS = 4
RECHTS = 5

# snelheden motoren
minSnelheid = 0         # alle snelheden in procenten
maxSnelheid = 100
stapSnelheid = 10
snelheid = minSnelheid
Commando = STOPPEN
laatsteCommando = STOPPEN

# modus besturing rover
autoModus = False       # auto navigatie boolean
autoSnelheid = 30       # snelheid in % bij auto navigatie
kwartDraai = 2          # tijd in sec voor een kwartdraai (90°)

# GPIO poorten afstandssensoren HC-SR04 voor en achter
ASV_TRIG = 27           # trigger afstandssensor voor
ASV_ECHO = 4            # echo afstandssensor voor

ASA_TRIG = 20           # trigger afstandssensor achter
ASA_ECHO = 21           # echo afstandssensor achter

ASV = 1                 # afstandssensor voor
ASA = 2                 # afstandssensor achter

# berekenen afstanden
PULSE = 0.00001         # trigger pulse 10 micro sec
SNELHEID_GELUID = 34000  # geluidsnelheid in cm/sec

# afstanden
minAfstand = 50         # minimum afstand tot obstakel in cm
maxAfstand = 200        # maximum afstand tot obstakel in cm

afstandVoor = 200       # variabele afstand voorste sensor
afstandAchter = 200     # variabele afstand achterste sensor


###############################################################################
# Setup wordt 1 maal uitgevoerd tijdens het starten van de WebIOPi service
# hier doen we de initialisatie van de GPIO pinnen
###############################################################################

def setup():

    # Zet debug aan
    # webiopi.setDebug()

    # setup GPIO poorten L298N
    gpio.setFunction(L298N_IN1, gpio.OUT)
    gpio.setFunction(L298N_IN2, gpio.OUT)
    gpio.setFunction(L298N_ENA, gpio.PWM)
    gpio.setFunction(L298N_IN3, gpio.OUT)
    gpio.setFunction(L298N_IN4, gpio.OUT)
    gpio.setFunction(L298N_ENB, gpio.PWM)

    # setup GPIO poorten HC-SR04
    gpio.setFunction(ASV_TRIG, gpio.OUT)
    gpio.setFunction(ASV_ECHO, gpio.IN)
    gpio.setFunction(ASA_TRIG, gpio.OUT)
    gpio.setFunction(ASA_ECHO, gpio.IN)

    # init GPIO poorten L298N
    gpio.digitalWrite(L298N_IN1, gpio.LOW)
    gpio.digitalWrite(L298N_IN2, gpio.LOW)
    gpio.pwmWrite(L298N_ENA, snelheid/100)
    gpio.digitalWrite(L298N_IN3, gpio.LOW)
    gpio.digitalWrite(L298N_IN4, gpio.LOW)
    gpio.pwmWrite(L298N_ENB, snelheid/100)

    # init GPIO poorten HC-SR04
    gpio.digitalWrite(ASV_TRIG, gpio.LOW)
    gpio.digitalWrite(ASA_TRIG, gpio.LOW)

    # thread opzetten voor afstandsmetingen en botsingsdetectie
    thread_metingen = threading.Thread(target=MeetAfstanden)
    thread_metingen.setDaemon(True)
    thread_metingen.start()

    # thread opzetten voor auto navigatie
    thread_navigatie = threading.Thread(target=Navigeer)
    thread_navigatie.setDaemon(True)
    thread_navigatie.start()


###############################################################################
# Loop wordt voortdurend herhaald zolang de WebIOPi service draait
# ik gebruik dit niet omdat loop enkel een single thread ondersteunt.
###############################################################################

# def loop():


###############################################################################
# Destroy wordt uitgevoerd bij het stoppen van de WebIOPi service
# dit wordt gebruikt voor de cleanup van de GPIO poorten.
###############################################################################

def destroy():

    # reset GPIO poorten
    gpio.digitalWrite(L298N_IN1, gpio.LOW)
    gpio.digitalWrite(L298N_IN2, gpio.LOW)
    gpio.digitalWrite(L298N_IN3, gpio.LOW)
    gpio.digitalWrite(L298N_IN4, gpio.LOW)
    gpio.digitalWrite(ASV_TRIG, gpio.LOW)
    gpio.digitalWrite(ASA_TRIG, gpio.LOW)

    # setup GPIO poorten
    gpio.setFunction(L298N_IN1, gpio.IN)
    gpio.setFunction(L298N_IN2, gpio.IN)
    gpio.disablePWM(L298N_ENA)
    gpio.setFunction(L298N_IN3, gpio.IN)
    gpio.setFunction(L298N_IN4, gpio.IN)
    gpio.disablePWM(L298N_ENB)
    gpio.setFunction(ASV_TRIG, gpio.IN)
    gpio.setFunction(ASV_ECHO, gpio.IN)
    gpio.setFunction(ASA_TRIG, gpio.IN)
    gpio.setFunction(ASA_ECHO, gpio.IN)


###############################################################################
# ZetSnelheid bepaalt de snelheid van de rover :
# manuele modus : verhoogt de huidige snelheid met stapSnelheid tot maxSnelheid
#                 bij veranderen van richting reset de snelheid
# auto modus : gebruikt steeds een vaste snelheid -> autoSnelheid
###############################################################################

def ZetSnelheid(Commando):
    global snelheid, laatsteCommando

    # snelheid op 0 zetten bij wijziging richting
    if Commando != laatsteCommando:
        snelheid = 0
        gpio.pwmWrite(L298N_ENA, snelheid/100)
        gpio.pwmWrite(L298N_ENB, snelheid/100)
        laatsteCommando = Commando

    # instellen snelheid
    if autoModus:
        # auto modus -> autoSnelheid
        snelheid = autoSnelheid
    else:
        # manuele modus -> snelheid verhogen met stapSnelheid
        snelheid += stapSnelheid

        # begrenzen tot maxSnelheid
        if snelheid > maxSnelheid:
            snelheid = maxSnelheid

    return snelheid


###############################################################################
# Afstand bepaalt de afstand (cm) tot een obstakel met de HC-SR04 sensoren
# de tijd dat de echo puls hoog is evenredig met 2x de afstand tot het obstakel
###############################################################################

def Afstand(sensor):

    # sensor variabelen
    if sensor == ASV:
        TRIG = ASV_TRIG
        ECHO = ASV_ECHO
    elif sensor == ASA:
        TRIG = ASA_TRIG
        ECHO = ASA_ECHO
    else:
        # ongeldige sensor
        print('Ongeldige sensor!')
        return maxAfstand

    # initialisatie
    afstand = 0

    # als echo nu reeds hoog is, dan ongeldige meting
    if gpio.digitalRead(ECHO):
        return maxAfstand

    # zet trigger laag en wacht 50 msec om sensor te stabiliseren
    gpio.digitalWrite(TRIG, gpio.LOW)
    time.sleep(0.05)

    # zet trigger hoog gedurende 10 micro sec
    gpio.digitalWrite(TRIG, gpio.HIGH)
    time.sleep(PULSE)
    gpio.digitalWrite(TRIG, gpio.LOW)

    # initialisatie tijden
    start, stop = time.time(), time.time()

    # wachten op echo hoog voor maximum 20 msec
    # indien langer, dan afbreken met ongeldige meting
    while not gpio.digitalRead(ECHO):
        start = time.time()
        if start - stop > 0.02:
            return maxAfstand

    # wachten op echo laag voor maximum 20 msec
    # indien langer, dan afbreken met ongeldige meting
    while gpio.digitalRead(ECHO):
        stop = time.time()
        if stop - start > 0.02:
            return maxAfstand

    # berekenen afstand
    delta = stop - start
    afstand = delta * SNELHEID_GELUID / 2.0

    return round(afstand, 0)


###############################################################################
# MeetAfstanden draait in een aparte thread. De afstanden van beide sensoren
# worden iedere 250 msec gemeten en bewaard in globale variabelen.
# In manuele stuurmodus wordt de rover gestopt bij risico op botsing.
###############################################################################
def MeetAfstanden():
    global afstandVoor, afstandAchter

    while True:

        # initialiseer de lijsten voor de afstandsmetingen
        av, aa = [], []

        # meet 5 afstanden voor iedere sensor en voeg ze toe in de lijsten
        for i in range(5):
            av.append(Afstand(ASV))
            aa.append(Afstand(ASA))

        # verwijder de minimum en maximum meetwaarden uit de lijsten
        av.remove(min(av))
        av.remove(max(av))
        aa.remove(min(aa))
        aa.remove(max(aa))

        # bereken het gemiddelde van de restende meetwaarden uit de lijsten
        afstandVoor = round(sum(av)/len(av), 0)
        afstandAchter = round(sum(aa)/len(aa), 0)

        # debug
        # logging.debug("Richting: %s",laatsteCommando)
        # logging.debug("Afstand voor: %d cm", afstandVoor)
        # logging.debug("Afstand achter: %d cm", afstandAchter)

        # stoppen bij risico op botsing in manuele stuurmodus
        if not autoModus:
            if (laatsteCommando == VOORUIT) and (afstandVoor < minAfstand):
                Stoppen()
            if (laatsteCommando == ACHTERUIT) and (afstandAchter < minAfstand):
                Stoppen()

        # wacht even
        time.sleep(0.25)


###############################################################################
# WaardenUI wordt periodiek aangeroepen vanuit javascript (setInterval).
# De waarden dienen om de UI up te daten.
###############################################################################

@webiopi.macro
def WaardenUI():

    return "%d;%d;%d;%s" % (snelheid, afstandVoor, afstandAchter, autoModus)


###############################################################################
# ToggleModus verandert de status van de besturingsmodus.
# wordt aangeroepen bij het klikken op de modus knop van de UI
###############################################################################

@webiopi.macro
def ToggleModus():
    global autoModus

    # rover stoppen
    Stoppen()

    # modus besturing veranderen
    autoModus = not autoModus

    return WaardenUI()


###############################################################################
# Navigeer zorgt ervoor dat de rover automatisch zijn weg zoekt.
# Dit gebeurt in een aparte thread. We moeten namelijk terug kunnen
# overschakelen naar manuele modus via de UI
###############################################################################

def Navigeer():
    global snelheid

    while True:

        # enkel uitvoeren bij automatische navigatie
        while autoModus:

            # rover vooruit
            Vooruit()

            # botsing gevaar
            while afstandVoor < minAfstand:

                # rover stoppen
                Stoppen()

                # rover 2 sec achteruit
                if (afstandAchter > minAfstand):
                    Achteruit()
                    time.sleep(2)
                    Stoppen()

                # willekeurige kwartdraai
                if random.randint(1, 10) <= 5:
                    Links()
                else:
                    Rechts()

            # even pauzeren
            time.sleep(0.5)


###############################################################################
# Rover vooruit
# wordt aangeroepen bij het klikken op de vooruit knop van de UI
###############################################################################

@webiopi.macro
def Vooruit():

    # snelheid instellen
    ZetSnelheid(VOORUIT)

    # linkermotoren vooruit
    gpio.digitalWrite(L298N_IN1, gpio.LOW)
    gpio.digitalWrite(L298N_IN2, gpio.HIGH)

    # rechtermotoren vooruit
    gpio.digitalWrite(L298N_IN3, gpio.LOW)
    gpio.digitalWrite(L298N_IN4, gpio.HIGH)

    # snelheid linker- en rechtermotoren
    gpio.pwmWrite(L298N_ENA, snelheid/100)
    gpio.pwmWrite(L298N_ENB, snelheid/100)


###############################################################################
# Rover stoppen
# wordt aangeroepen bij het klikken op de stoppen knop van de UI
###############################################################################

@webiopi.macro
def Stoppen():
    global snelheid

    # snelheid op 0 zetten
    snelheid = 0

    # linkermotoren stoppen
    gpio.digitalWrite(L298N_IN1, gpio.LOW)
    gpio.digitalWrite(L298N_IN2, gpio.LOW)

    # rechtermotoren stoppen
    gpio.digitalWrite(L298N_IN3, gpio.LOW)
    gpio.digitalWrite(L298N_IN4, gpio.LOW)

    # snelheid linker- en rechtermotoren
    gpio.pwmWrite(L298N_ENA, snelheid)
    gpio.pwmWrite(L298N_ENB, snelheid)


###############################################################################
# Rover achteruit
# wordt aangeroepen bij het klikken op de achteruit knop van de UI
###############################################################################

@webiopi.macro
def Achteruit():

    # snelheid instellen
    ZetSnelheid(ACHTERUIT)

    # linkermotoren achteruit
    gpio.digitalWrite(L298N_IN1, gpio.HIGH)
    gpio.digitalWrite(L298N_IN2, gpio.LOW)

    # rechtermotoren achteruit
    gpio.digitalWrite(L298N_IN3, gpio.HIGH)
    gpio.digitalWrite(L298N_IN4, gpio.LOW)

    # snelheid linker- en rechtermotoren
    gpio.pwmWrite(L298N_ENA, snelheid/100)
    gpio.pwmWrite(L298N_ENB, snelheid/100)


###############################################################################
# Rover links
# wordt aangeroepen bij het klikken op de links knop van de UI
# voert een kwartdraai (90°) uit; resultaat is afhankelijk van ondergrond
###############################################################################

@webiopi.macro
def Links():
    global snelheid

    # snelheid instellen
    ZetSnelheid(LINKS)

    # kwartdraai uitvoeren aan snelheid 40%
    snelheid = 40

    # linkermotoren achteruit
    gpio.digitalWrite(L298N_IN1, gpio.HIGH)
    gpio.digitalWrite(L298N_IN2, gpio.LOW)

    # rechtermotoren vooruit
    gpio.digitalWrite(L298N_IN3, gpio.LOW)
    gpio.digitalWrite(L298N_IN4, gpio.HIGH)

    # snelheid linker- en rechtermotoren
    gpio.pwmWrite(L298N_ENA, snelheid/100)
    gpio.pwmWrite(L298N_ENB, snelheid/100)

    # tijd voor kwartdraai en daarna stoppen
    time.sleep(kwartDraai)
    Stoppen()


###############################################################################
# Rover rechts
# wordt aangeroepen bij het klikken op de rechts knop van de UI
# voert een kwartdraai (90°) uit; resultaat is afhankelijk van ondergrond
###############################################################################

@webiopi.macro
def Rechts():
    global snelheid

    # snelheid instellen
    ZetSnelheid(RECHTS)

    # kwartdraai uitvoeren aan snelheid 40%
    snelheid = 40

    # linkermotoren vooruit
    gpio.digitalWrite(L298N_IN1, gpio.LOW)
    gpio.digitalWrite(L298N_IN2, gpio.HIGH)

    # rechtermotoren achteruit
    gpio.digitalWrite(L298N_IN3, gpio.HIGH)
    gpio.digitalWrite(L298N_IN4, gpio.LOW)

    # snelheid linker- en rechtermotoren
    gpio.pwmWrite(L298N_ENA, snelheid/100)
    gpio.pwmWrite(L298N_ENB, snelheid/100)

    # tijd voor kwartdraai en daarna stoppen
    time.sleep(kwartDraai)
    Stoppen()
