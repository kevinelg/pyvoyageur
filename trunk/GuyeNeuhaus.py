#!/usr/bin/env python
# encoding: utf-8
"""
GuyeNeuhaus.py

Created by Raphael Guye and Jonathan Neuhaus on 2010-04-14.
Copyright (c) 2010 HE-Arc. All rights reserved.
"""

import pygame
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN, K_ESCAPE
import sys
import os
from string import strip
from optparse import OptionParser
from MyUtils import speedMeasure
import math
from random import randint

try:
	import psyco
	psyco.full()
except ImportError:
	pass

#================================================
#              VARIABLES GLOBALES
#================================================

text = None
screen = None
font = None
cities = []
screen_x = 500
screen_y = 500

city_color = [10,10,200] # blue
city_radius = 3
font_color = [255,255,255] # white


initialRoutesNumber = 30


#================================================
#              Classes
#================================================

class City(object):
    """Representation of a city"""
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        
    def __str__(self):
        return self.name + " : " + str(self.x) +","+ str(self.y)

class Route(object):
    """Route with all cities"""
    def __init__(self, cityList):
    	self.cityList = cityList
    def len(self):
        """Process the length of a route"""
        length = 0
        for i in range(len(self.cityList)-1):
    		length += dist2City(self.cityList[i], self.cityList[i+1])
        return length
    def isEgal(self, route):
        """Check if the 2 listRoutes are equal"""
        if (len(self.cityList) <> route.len()):
            return False
        for i in range(len(self.cityList)):
            if (self.cityList[i]<>route[i]):
                return False
        return True
    def isContained(self, listRoutes):
        """Check if the 2 listRoutes are equal"""
        for r in listRoutes:
            if r.isEgal(self):
                return True
        return False
    def __str__(self):
        tmp = ""
        for c in self.cityList:
            tmp += str(c)
            tmp += " / "
        return tmp
    		

#================================================
#              Main
#================================================

def main():
    global text
    usage = """usage: %prog [options] [filename]
This script is intend to solve the Travel Salesman problem (TSP) problem.

[filename] is a file that contains the coordinates of the cities.
The format of this file is: NAME1 XPos1 YPos1
It is an optional argument."""

    parser = OptionParser(usage)
    parser.add_option("-n","--nogui", action="store_false", dest="gui", default=True, help="Do not use a graphical representation")
    parser.add_option("-m","--maxtime", type="int", dest="maxtime", default=0, help="Force the algorithm to stop after the given time (in seconds)")
    (options, args) = parser.parse_args()
    
    # Retrieve the options
    filename = None
    if args<>[] and os.path.isfile(args[-1]):
                    filename = args[-1]

    initPygame()
    draw(cities)

    collecting = True
	
    while collecting:
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_RETURN:
                collecting = False
            elif event.type == MOUSEBUTTONDOWN:
                (x,y) = pygame.mouse.get_pos()
                cities.append(City(x,y,"v" + str(len(cities))))
                draw(cities)
    screen.fill(0)
    
    ga_solve(filename, options.gui, options.maxtime)
    
    while True:
        event = pygame.event.wait()
        if event.type == KEYDOWN: break

#================================================
#              Methodes
#================================================
def fac(n):
    """Return the orial of a number"""
    p=1
    for i in range(1,n+1):
        p*=i
    return p

def dist2City(city1, city2):
	"""return the distance between 2 cities"""
	return math.sqrt((city1.x-city2.x)**2 + (city1.y-city2.y)**2)
	
def generateRoutes(listRoutes, baseRoute, initialRoutesNumber):
    """generate the number of listRoutes required"""
    listRoutes.append(baseRoute)
    cpt=1
    cityList = []
    # The city list contains already the last city
    lenCityList = len(baseRoute.cityList) - 1
    indexList = []
    while cpt<=initialRoutesNumber and cpt<=maxPossibilities(lenCityList):
        tmp = shake(lenCityList)
        print "lenCityList", lenCityList
        while tmp in indexList:
            tmp = shake(lenCityList)
        indexList.append(tmp)
        print "il", indexList
        print cpt
        cpt += 1
        
        
        
        
        
    #     cityList[:] = []
    #     for i in indexList:
    #         cityList.append(baseRoute.cityList[i])
    #     #if (Route(cityList) not in listRoutes):
    #     
    #     newRoute = Route(cityList)
    #     if (not newRoute.isContained(listRoutes)):
    #         listRoutes.append(Route(cityList))
    #     cpt += 1
    #     print cpt
    # print "out"

def shake(initialList):
    """Return a list shaken"""
    indexList = []
    # The first element is allways the starting city
    indexList.append(0)
    
    for i in range(initialList-1):
        i = randint(1,initialList-1)
        while (i in indexList):
            i = randint(1,initialList-1)
        indexList.append(i)
    # Return to the starting city
    indexList.append(0)
    return indexList
    
def maxPossibilities(lenCityList):
    """return the maximum number of different listRoutes"""
    return fac(lenCityList-1)

def initPygame():
    global screen
    global font
    pygame.init() 
    window = pygame.display.set_mode((screen_x, screen_y)) 
    pygame.display.set_caption('Exemple') 
    screen = pygame.display.get_surface() 
    font = pygame.font.Font(None,30)

def draw(cities):
    screen.fill(0)
    for c in cities:
        pygame.draw.circle(screen,city_color,(c.x,c.y),city_radius)
    text = font.render("Nombre: %i" % len(cities), True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()

@speedMeasure
def ga_solve(file=None, gui=True, maxtime=0):
    """ Resolution of the city traveller problem """
    global cities
    
    print "gui = ", gui
    print "maxtime = ", maxtime
    print "filename = ", file
    
    if file != None:
        f = open(file,"r")
        cities = [City(int(l.split(" ")[1]),int(strip(l.split(" ")[2])),l.split(" ")[0]) for l in f]
    
    new = []
    for c in cities:
		new.insert(0,c)
		print "x,y=",c.x,",",c.y
    
    cities = new
    cities.append(cities[0])
    
    # Repeat the first element to the last position
    baseRoute = Route(cities)
    
    listRoutes=[]
    print fac(len(baseRoute.cityList))
    generateRoutes(listRoutes, baseRoute, initialRoutesNumber)
    for r in listRoutes:
        print r
    
    pos = []
    [pos.append((c.x,c.y)) for c in cities]
    if gui:
        pygame.draw.lines(screen,city_color,True,pos)
        text = font.render("Un chemin, pas le meilleur!", True, font_color)
        textRect = text.get_rect()
        screen.blit(text, textRect)
        pygame.display.flip()

if __name__ == '__main__':
    main()
