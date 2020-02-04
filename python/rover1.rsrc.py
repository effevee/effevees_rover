{'application':{'type':'Application',
          'name':'Template',
    'backgrounds': [
    {'type':'Background',
          'name':'bgTemplate',
          'title':u'Rover1',
          'size':(292, 224),
          'style':['resizeable'],

        'menubar': {'type':'MenuBar',
         'menus': [
             {'type':'Menu',
             'name':'menuFile',
             'label':'&File',
             'items': [
                  {'type':'MenuItem',
                   'name':'menuFileExit',
                   'label':'E&xit',
                   'command':'exit',
                  },
              ]
             },
         ]
     },
         'components': [

{'type':'StaticText', 
    'name':'STAchter', 
    'position':(20, 145), 
    'backgroundColor':(237, 236, 235, 255), 
    'text':u'Achter', 
    },

{'type':'StaticText', 
    'name':'STVoor', 
    'position':(20, 65), 
    'backgroundColor':(237, 236, 235, 255), 
    'text':u'Voor ', 
    },

{'type':'Gauge', 
    'name':'GaugeSnelheid', 
    'position':(95, 20), 
    'size':(100, 28), 
    'backgroundColor':(191, 191, 191, 255), 
    'foregroundColor':(30, 144, 255, 255), 
    'layout':u'horizontal', 
    'max':100, 
    'value':0, 
    },

{'type':'Button', 
    'name':'BtnRechts', 
    'position':(190, 100), 
    'label':u'Rechts', 
    },

{'type':'Button', 
    'name':'BtnLinks', 
    'position':(10, 100), 
    'label':u'Links', 
    },

{'type':'Button', 
    'name':'BtnAchteruit', 
    'position':(100, 140), 
    'label':u'Achteruit', 
    },

{'type':'Button', 
    'name':'BtnStoppen', 
    'position':(100, 100), 
    'label':u'Stoppen', 
    },

{'type':'Button', 
    'name':'BtnVooruit', 
    'position':(100, 60), 
    'label':u'Vooruit', 
    },

] # end components
} # end background
] # end backgrounds
} }
