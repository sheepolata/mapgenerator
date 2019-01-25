BLACK        = (0,0,0)
WHITE        = (255,255,255)
RED          = (255,0,0)
RED_2        = (255, 50, 50)
RED_3        = (150, 50, 50)
LIME         = (0,255,0)
BLUE         = (0,0,255)
BLUE_2       = (50,50,255)
BLUE_3       = (50,50,150)
YELLOW       = (255,255,0)
YELLOW_2     = (200,200,0)
YELLOW_3     = (150,150,0)
CYAN         = (0,255,255)
MAGENTA      = (255,0,255)
SILVER       = (192,192,192)
GRAY         = (128,128,128)
GRAY_EFFECT  = (98,98,98)
MAROON       = (128,0,0)
BROWN        = (139,69,19)
BROWN_EFFECT = (119,49,0)
OLIVE        = (128,128,0)
OLIVE_EFFECT = (108,108,0)
OLIVE_2      = (100,100,0)
OLIVE_3      = (64,64,0)
GREEN        = (0, 255, 0)
GREEN_EFFECT = (0, 185, 0)
GREEN_2      = (0,128,0)
GREEN_3      = (0,64,0)
PURPLE       = (128,0,128)
TEAL         = (0,128,128)
NAVY         = (0,0,128)

ALL_COLOR_LIST = [BLACK, WHITE, RED, RED_2, RED_3, LIME, BLUE, BLUE_2, BLUE_3, 
                YELLOW, YELLOW_2, YELLOW_3, CYAN, MAGENTA, SILVER, GRAY, MAROON,
                OLIVE, OLIVE_2, OLIVE_3, GREEN, PURPLE, TEAL, NAVY, BROWN]

LANDSCAPE_COLOR_LIST = [BLUE, NAVY, GREEN, GREEN_2, YELLOW, BROWN, OLIVE]
LANDSCAPE_TEST       = {
                        BLUE:0,
                        NAVY:0,
                        GREEN:1,
                        GREEN_2:0,
                        YELLOW:0,
                        BROWN:0,
                        OLIVE:0
                    }
LANDSCAPE_DEFAULT    = {
                        BLUE:0.15,
                        NAVY:0.14,
                        GREEN:0.15,
                        GREEN_2:0.14,
                        YELLOW:0.14,
                        BROWN:0.14,
                        OLIVE:0.14
                    }
LANDSCAPE_ISLANDS    = {
                        BLUE:0.44,
                        NAVY:0.12,
                        GREEN:0.2,
                        GREEN_2:0.08,
                        YELLOW:0.10,
                        BROWN:0.05,
                        OLIVE:0.01
                    }
LANDSCAPE_MOUNTAINS  = {
                        BLUE:0.05,
                        NAVY:0.02,
                        GREEN:0.1,
                        GREEN_2:0.21,
                        YELLOW:0.07,
                        BROWN:0.35,
                        OLIVE:0.2
                    }

COLOR_TO_TYPE = {
    BLACK     : "city",
    WHITE     : "unknow",
    RED       : "unknow",
    RED_2     : "unknow",
    RED_3     : "unknow",
    LIME      : "unknow",
    BLUE      : "shallow_water",
    BLUE_2    : "unknow",
    BLUE_3    : "unknow",
    YELLOW    : "desert",
    YELLOW_2  : "unknow",
    YELLOW_3  : "unknow",
    CYAN      : "unknow",
    MAGENTA   : "unknow",
    SILVER    : "unknow",
    GRAY      : "city",
    MAROON    : "unknow",
    BROWN     : "mountain",
    OLIVE     : "hill",
    OLIVE_2   : "unknow",
    OLIVE_3   : "unknow",
    GREEN     : "plain",
    GREEN_2   : "forest",
    PURPLE    : "unknow",
    TEAL      : "unknow",
    NAVY      : "deep_water"
}

USED_TYPES = ["shallow_water", "deep_water", "plain", "forest", "desert", "hill", "mountain", "city"]
LAND_TYPES = ["plain", "forest", "desert", "hill", "mountain", "city"]
WATER_TYPES = ["shallow_water", "deep_water"]

TYPE_TO_COST = {
    "unknow"        : 1.0,
    "shallow_water" : 22.0,
    "deep_water"    : 28.0,
    "plain"         : 1.0,
    "forest"        : 4.0,
    "desert"        : 8.0,
    "hill"          : 4.0,
    "mountain"      : 14.0,
    "city"          : 2.0
}

SCORE_RIVER = 0.3
SCORE_NEIGH_RIVER = 0.3

TYPE_TO_SCORE = {
    "unknow"        : 0.0,
    "shallow_water" : -3.0,
    "deep_water"    : -3.0,
    "plain"         : -0.1,
    "forest"        : 0.4,
    "desert"        : -0.4,
    "hill"          : 0.4,
    "mountain"      : 0.2,
    "city"          : -3.0
}

TYPE_TO_WEIGTH_SCORE = {
    "unknow"        : 0.0,
    "shallow_water" : 0.4,
    "deep_water"    : 0.3,
    "plain"         : 0.6,
    "forest"        : 0.4,
    "desert"        : -0.6,
    "hill"          : 0.1,
    "mountain"      : -0.2,
    "city"          : -3.0
}

TYPE_TO_MULTIPLIER = {
    "unknow"        : 1.0 / TYPE_TO_COST["unknow"],
    "shallow_water" : 1.0 / TYPE_TO_COST["shallow_water"],
    "deep_water"    : 1.0 / TYPE_TO_COST["deep_water"],
    "plain"         : 1.0 / TYPE_TO_COST["plain"],
    "forest"        : 1.0 / TYPE_TO_COST["forest"],
    "desert"        : 1.0 / TYPE_TO_COST["desert"],
    "hill"          : 1.0 / TYPE_TO_COST["hill"],
    "mountain"      : 1.0 / TYPE_TO_COST["mountain"],
    "city"          : 1.0 / TYPE_TO_COST["city"],

}

EMPTY = (0, 0, 0, 0)

ALPHA_BLACK     = (0,0,0, 128)
ALPHA_BLACK_2   = (0,0,0, 64)
ALPHA_WHITE     = (255,255,255, 128)
ALPHA_WHITE_2   = (255,255,255, 64)
ALPHA_RED       = (255,0,0, 128)
ALPHA_RED_2     = (255,0,0, 64)
ALPHA_LIME      = (0,255,0, 128)
ALPHA_LIME_2    = (0,255,0, 64)
ALPHA_BLUE      = (0,0,255, 128)
ALPHA_YELLOW    = (255,255,0, 128)
ALPHA_CYAN      = (0,255,255, 128)
ALPHA_MAGENTA   = (255,0,255, 128)
ALPHA_SILVER    = (192,192,192, 128)
ALPHA_GRAY      = (128,128,128, 128)
ALPHA_MAROON    = (128,0,0, 128)
ALPHA_OLIVE     = (128,128,0, 128)
ALPHA_GREEN     = (0,128,0, 128)
ALPHA_PURPLE    = (128,0,128, 128)
ALPHA_TEAL      = (0,128,128, 128)
ALPHA_NAVY      = (0,0,128, 128)