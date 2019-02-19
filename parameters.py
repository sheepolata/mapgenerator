#!/usr/bin/env python
#-*- coding: utf-8 -*-

import tile_info
import random

instance = None

def getInstance():
    global instance
    if instance == None:
        instance = Parameters()
    return instance

class Parameters(object):
    """docstring for Parameters"""
    def __init__(self):
        self.init()
        
    def init(self):
        self.MAP_TILES              = []
        self.CANVAS_SIZE            = 100
        self.CANVAS_WIDTH           = self.CANVAS_SIZE
        self.CANVAS_HEIGHT          = self.CANVAS_SIZE

        self.MAP_WIDTH              = 900
        self.MAP_HEIGHT             = 700

        self.MAP_WIDTH = int(round(self.MAP_WIDTH/self.CANVAS_WIDTH)) * self.CANVAS_WIDTH
        self.MAP_HEIGHT = int(round(self.MAP_HEIGHT/self.CANVAS_HEIGHT)) * self.CANVAS_HEIGHT

        self.INFO_WIDTH             = 320
        # INFO_HEIGHT            = 700
        self.INFO_HEIGHT            = self.MAP_HEIGHT

        self.WINDOW_WIDTH           = self.MAP_WIDTH + self.INFO_WIDTH
        self.WINDOW_HEIGHT          = self.MAP_HEIGHT

        self.MAIN_WINDOW_PROPORTION = 0.75

        self.CARAVAN_LIST        = []
        self.STARTING_NB_CARAVAN = 0
        self.MIN_POP_PER_CARAVAN = 50.0
        self.MAX_POP_PER_CARAVAN = 150.0

        self.MIGRANTS_VILLAGE_LIST = []

        self.EMISSARY_VILLAGE_LIST = []

        self.VILLAGE_LIST = []
        self.TOWN_LIST    = []
        self.CITY_LIST    = []

        self.NB_RIVERS = random.randint(35, 55)
        self.RIVERS = []

        self.MIN_TILE_SCORE = 0.0
        self.MAX_TILE_SCORE = 0.0

        self.REFRESH_FREQ = 20
        self.FORCED_FPS   = 30

        self.GEN_ONLY = False

        self.DEFAULT_DRAWING = False
        # BIOME = tile_info.LANDSCAPE_TEST
        self.BIOME = tile_info.LANDSCAPE_DEFAULT
        # BIOME = tile_info.LANDSCAPE_ISLANDS
        # BIOME = tile_info.LANDSCAPE_MOUNTAINS
        if not self.DEFAULT_DRAWING:
            self.COLOR_PALETTE = self.BIOME.keys()
            self.COLOR_PROBA   = self.BIOME.values()
        else:
            self.COLOR_PALETTE = tile_info.LANDSCAPE_COLOR_LIST 
        # COLOR_PROBA   = None
        self.MAX_TILE_COST = 0.0

        self.FAST_DISPLAY = ((self.CANVAS_WIDTH * self.CANVAS_HEIGHT) > 100*100)

        self.EIGHT_NEIGHBOURS = True

        self.HEATMAP_TYPE = 0
        self.HEATMAP_ALPHA = 255

    # def resize_window_from_canvas():
    #   MAP_WIDTH = int(round(MAP_WIDTH/CANVAS_WIDTH)) * CANVAS_WIDTH
    #   MAP_HEIGHT = int(round(MAP_HEIGHT/CANVAS_HEIGHT)) * CANVAS_HEIGHT