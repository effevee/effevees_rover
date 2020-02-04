#!/usr/bin/python


# PythonCard versie


from PythonCard import model, timer

import wiringpi as wpi
import time


class Minimal(model.Background):
    global INPUT, OUTPUT, PWM
    global LOW, HIGH
    global L298N_IN1, L298N_IN2, L298N_IN3, L298N_IN4, L298N_ENA, L298N_ENB
    global ASV_TRIG, ASV_ECHO, ASA_TRIG, ASA_ECHO
    global VOORUIT, ACHTERUIT, STOPPEN, LINKS, RECHTS
    global minSnelheid, maxSnelheid, stapSnelheid, Snelheid, laatsteCommando
    global Versnellen
    global cmVoor, cmAchter, minAfstand, Afstand
    global ASV, ASA, PULSE, SNELHEID_GELUID

    # constanten
    INPUT = 0
    OUTPUT = 1
    PWM = 2
    LOW = 0
    HIGH = 1

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
    minSnelheid = 0
    maxSnelheid = 100
    stapSnelheid = 10
    Snelheid = minSnelheid
    laatsteCommando = 0

    # GPIO poorten afstandssensoren HC-SR04 voor en achter
    ASV_TRIG = 27           # trigger afstandssensor voor
    ASV_ECHO = 4            # echo afstandssensor voor

    ASA_TRIG = 20           # trigger afstandssensor achter
    ASA_ECHO = 21           # echo afstandssensor achter

    PULSE = 0.00001         # trigger pulse 10 micro sec
    SNELHEID_GELUID = 34000  # geluidsnelheid in cm/s

    ASV = 1                 # afstandssensor voor
    ASA = 2                 # afstandssensor achter

    minAfstand = 30         # minimum afstand tot obstakel in cm

    def on_menuFileAbout_select(self, event):
        pass

    def on_initialize(self, event):

        # GPIO wiring conventie
        wpi.wiringPiSetupGpio()

        # setup GPIO poorten L298N en HC-SR04
        wpi.pinMode(L298N_IN1, OUTPUT)
        wpi.pinMode(L298N_IN2, OUTPUT)
        wpi.pinMode(L298N_IN3, OUTPUT)
        wpi.pinMode(L298N_IN4, OUTPUT)
        wpi.pinMode(L298N_ENA, PWM)
        wpi.pinMode(L298N_ENB, PWM)
        wpi.softPwmCreate(L298N_ENA, minSnelheid, maxSnelheid)
        wpi.softPwmCreate(L298N_ENB, minSnelheid, maxSnelheid)
        wpi.pinMode(ASV_TRIG, OUTPUT)
        wpi.pinMode(ASV_ECHO, INPUT)
        wpi.pinMode(ASA_TRIG, OUTPUT)
        wpi.pinMode(ASA_ECHO, INPUT)

        # init GPIO poorten L298N en HC-SR04
        wpi.digitalWrite(L298N_IN1, LOW)
        wpi.digitalWrite(L298N_IN2, LOW)
        wpi.digitalWrite(L298N_IN3, LOW)
        wpi.digitalWrite(L298N_IN4, LOW)
        wpi.softPwmWrite(L298N_ENA, Snelheid)
        wpi.softPwmWrite(L298N_ENB, Snelheid)
        wpi.digitalWrite(ASV_TRIG, LOW)
        wpi.digitalWrite(ASA_TRIG, LOW)

        # setup timer voor afstandsmetingen
        self.mijnTimer = timer.Timer(self.components.STVoor, -1)
        self.mijnTimer.Start(500)

    def Versnellen(Commando):
        global Snelheid, maxSnelheid, stapSnelheid, laatsteCommando

        # Snelheid op 0 zetten bij wijziging commando
        if Commando != laatsteCommando:
            Snelheid = 0
            wpi.softPwmWrite(L298N_ENA, Snelheid)
            wpi.softPwmWrite(L298N_ENB, Snelheid)
            laatsteCommando = Commando

        # snelheid verhogen met stapSnelheid
        Snelheid += stapSnelheid

        # begrenzen tot maxSnelheid
        if Snelheid > maxSnelheid:
            Snelheid = maxSnelheid

        return Snelheid

    def on_BtnVooruit_mouseClick(self, event):
        global Snelheid

        # Snelheid verhogen met stapSnelheid
        Versnellen(VOORUIT)

        # Snelheid tonen in GaugeSnelheid
        self.components.GaugeSnelheid.value = Snelheid

        # linkermotoren vooruit
        wpi.digitalWrite(L298N_IN1, LOW)
        wpi.digitalWrite(L298N_IN2, HIGH)

        # rechtermotoren vooruit
        wpi.digitalWrite(L298N_IN3, LOW)
        wpi.digitalWrite(L298N_IN4, HIGH)

        # snelheid linker- en rechtermotoren
        wpi.softPwmWrite(L298N_ENA, Snelheid)
        wpi.softPwmWrite(L298N_ENB, Snelheid)

    def on_BtnStoppen_mouseClick(self, event):
        global Snelheid

        # Snelheid op 0 zetten
        Snelheid = 0

        # Snelheid tonen in GaugeSnelheid
        self.components.GaugeSnelheid.value = Snelheid

        # linkermotoren stoppen
        wpi.digitalWrite(L298N_IN1, LOW)
        wpi.digitalWrite(L298N_IN2, LOW)

        # rechtermotoren stoppen
        wpi.digitalWrite(L298N_IN3, LOW)
        wpi.digitalWrite(L298N_IN4, LOW)

        # snelheid linker- en rechtermotoren
        wpi.softPwmWrite(L298N_ENA, Snelheid)
        wpi.softPwmWrite(L298N_ENB, Snelheid)

    def on_BtnAchteruit_mouseClick(self, event):
        global Snelheid

        # Snelheid verhogen met stapSnelheid
        Versnellen(ACHTERUIT)

        # Snelheid tonen in GaugeSnelheid
        self.components.GaugeSnelheid.value = Snelheid

        # linkermotoren achteruit
        wpi.digitalWrite(L298N_IN1, HIGH)
        wpi.digitalWrite(L298N_IN2, LOW)

        # rechtermotoren achteruit
        wpi.digitalWrite(L298N_IN3, HIGH)
        wpi.digitalWrite(L298N_IN4, LOW)

        # snelheid linker- en rechtermotoren
        wpi.softPwmWrite(L298N_ENA, Snelheid)
        wpi.softPwmWrite(L298N_ENB, Snelheid)

    def on_BtnLinks_mouseClick(self, event):
        global Snelheid

        # Snelheid verhogen met stapSnelheid
        Versnellen(LINKS)

        # Snelheid tonen in GaugeSnelheid
        self.components.GaugeSnelheid.value = Snelheid

        # linkermotoren achteruit
        wpi.digitalWrite(L298N_IN1, HIGH)
        wpi.digitalWrite(L298N_IN2, LOW)

        # rechtermotoren vooruit
        wpi.digitalWrite(L298N_IN3, LOW)
        wpi.digitalWrite(L298N_IN4, HIGH)

        # snelheid linker- en rechtermotoren
        wpi.softPwmWrite(L298N_ENA, Snelheid)
        wpi.softPwmWrite(L298N_ENB, Snelheid)

    def on_BtnRechts_mouseClick(self, event):
        global Snelheid

        # Snelheid verhogen met stapSnelheid
        Versnellen(RECHTS)

        # Snelheid tonen in GaugeSnelheid
        self.components.GaugeSnelheid.value = Snelheid

        # linkermotoren vooruit
        wpi.digitalWrite(L298N_IN1, LOW)
        wpi.digitalWrite(L298N_IN2, HIGH)

        # rechtermotoren achteruit
        wpi.digitalWrite(L298N_IN3, HIGH)
        wpi.digitalWrite(L298N_IN4, LOW)

        # snelheid linker- en rechtermotoren
        wpi.softPwmWrite(L298N_ENA, Snelheid)
        wpi.softPwmWrite(L298N_ENB, Snelheid)

    def Afstand(sensor):

        # sensor variabelen
        if sensor == ASV:
            TRIG = ASV_TRIG
            ECHO = ASV_ECHO
        elif sensor == ASA:
            TRIG = ASA_TRIG
            ECHO = ASA_ECHO
        else:
            print('Ongeldige sensor!')
            afstand = minAfstand
            return afstand

        # trigger hoog zetten gedurende 10 micro sec
        wpi.digitalWrite(TRIG, HIGH)
        time.sleep(PULSE)
        wpi.digitalWrite(TRIG, LOW)

        # wachten op echo hoog
        while wpi.digitalRead(ECHO) == LOW:
            start = time.time()

        # wachten op echo laag
        while wpi.digitalRead(ECHO) == HIGH:
            stop = time.time()

        # berekenen afstand
        delta = stop - start
        afstand = delta * SNELHEID_GELUID / 2.0

        return round(afstand, 1)

    def on_STVoor_timer(self, event):
        global Snelheid, cmVoor, cmAchter, minAfstand

        # meet afstand voor en achter
        cmVoor = Afstand(ASV)
        cmAchter = Afstand(ASA)

        # toon afstanden
        self.components.STVoor.text = str(cmVoor) + ' cm'
        self.components.STAchter.text = str(cmAchter) + ' cm'

        # kontrole afstanden
        if (cmVoor <= minAfstand) or (cmAchter <= minAfstand):
            Snelheid = 0
            wpi.softPwmWrite(L298N_ENA, Snelheid)
            wpi.softPwmWrite(L298N_ENB, Snelheid)

    def on_close(self, event):

        # setup GPIO poorten
        wpi.pinMode(L298N_IN1, INPUT)
        wpi.pinMode(L298N_IN2, INPUT)
        wpi.pinMode(L298N_IN3, INPUT)
        wpi.pinMode(L298N_IN4, INPUT)
        wpi.pinMode(L298N_ENA, INPUT)
        wpi.pinMode(L298N_ENB, INPUT)
        wpi.pinMode(ASV_TRIG, INPUT)
        wpi.pinMode(ASV_ECHO, INPUT)
        wpi.pinMode(ASA_TRIG, INPUT)
        wpi.pinMode(ASA_ECHO, INPUT)

        # reset GPIO poorten
        wpi.digitalWrite(L298N_IN1, LOW)
        wpi.digitalWrite(L298N_IN2, LOW)
        wpi.digitalWrite(L298N_IN3, LOW)
        wpi.digitalWrite(L298N_IN4, LOW)
        wpi.digitalWrite(L298N_ENA, LOW)
        wpi.digitalWrite(L298N_ENB, LOW)
        wpi.digitalWrite(ASV_TRIG, LOW)
        wpi.digitalWrite(ASV_ECHO, LOW)
        wpi.digitalWrite(ASA_TRIG, LOW)
        wpi.digitalWrite(ASA_ECHO, LOW)
        self.Destroy()


if __name__ == '__main__':
    app = model.Application(Minimal)
    app.MainLoop()
