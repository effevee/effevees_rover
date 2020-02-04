// dit wordt uitgevoerd bij de initialisatie van WebIOPi
webiopi().ready(function() {
            
    // Maak de macro knop vooruit
    // bij het klikken wordt de python code Vooruit aangeroepen
    var knop_vooruit = webiopi().createMacroButton("idBtnVooruit", "", "Vooruit");
                
    // Maak de macro knop stoppen
    // bij het klikken wordt de python code Stoppen aangeroepen
    var knop_stoppen = webiopi().createMacroButton("idBtnStoppen", "", "Stoppen");

    // Maak de macro knop achteruit
    // bij het klikken wordt de python code Achteruit aangeroepen
    var knop_achteruit = webiopi().createMacroButton("idBtnAchteruit", "", "Achteruit");

    // Maak de macro knop links
    // bij het klikken wordt de python code Links aangeroepen
    var knop_links = webiopi().createMacroButton("idBtnLinks", "", "Links");
   
    // Maak de macro knop rechts
    // bij het klikken wordt de python code Rechts aangeroepen
    var knop_rechts = webiopi().createMacroButton("idBtnRechts", "", "Rechts");

    // Maak de knop hand/auto
    // bij het klikken wordt de python code ToggleModus aangeroepen
    // de callback functie updateModus update de class van de knop
    var knop_modus = webiopi().createButton("idBtnModus", "", function() {
        webiopi().callMacro("ToggleModus", [], updateModus);
    });    
                        
    // Voeg de knoppen toe aan het HTML element met ID="controls" mbv jQuery
    $("#controls").append(knop_vooruit);
    $("#controls").append(knop_stoppen);
    $("#controls").append(knop_achteruit);
    $("#controls").append(knop_links);
    $("#controls").append(knop_rechts);
    $("#controls").append(knop_modus);
    
    // Start een timer om iedere seconde de UI te updaten
    setInterval(LeesWaarden,1000);        
	
});
      
// deze functie roept de python code WaardenUI aan om de waarden voor de UI op te halen
// de callback functie updateUI zorgt voor de eigenlijke update van de UI
function LeesWaarden(){
   webiopi().callMacro("WaardenUI", [], updateUI); 
}

// deze functie wordt opgeroepen als callback van LeesWaarden (timer)
// de returnwaarden worden gebruikt om de UI te updaten met de nieuwe waarden
var updateUI = function(macro, args, response) {
    // returnwaarden zijn als tekst doorgegeven gescheiden door ";"
    var waarden = response.split(";");
    $("#snelheid").val(waarden[0]+" %");
    $("#afstandvoor").val(waarden[1]+" cm");
    $("#afstandachter").val(waarden[2]+" cm");
    $("#automodus").val(waarden[3]);
};
     
// deze functie wordt opgeroepen bij de toggle van hand naar auto of omgekeerd
// de returnwaarde wordt gebruikt om de class van de besturingsknoppen aan te passen
// waardoor we via css de juiste knop kunnen afbeelden in de UI 
var updateModus = function(macro, args, response) {
    var waarden = response.split(";");
    // update class voor knoppen
    if (waarden[3] == "True") {
        document.getElementById("idBtnVooruit").className = "auto";
        document.getElementById("idBtnStoppen").className = "auto";
        document.getElementById("idBtnAchteruit").className = "auto";
        document.getElementById("idBtnLinks").className = "auto";
        document.getElementById("idBtnRechts").className = "auto";
        document.getElementById("idBtnModus").className = "auto";
    } else {
        document.getElementById("idBtnVooruit").className = "hand";
        document.getElementById("idBtnStoppen").className = "hand";
        document.getElementById("idBtnAchteruit").className = "hand";
        document.getElementById("idBtnLinks").className = "hand";
        document.getElementById("idBtnRechts").className = "hand";
        document.getElementById("idBtnModus").className = "hand";
    }
}


