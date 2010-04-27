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
import time

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

# Maximum number of initial routes
initialRoutesNumber = 30
# % of the population to eliminate and then add by crossover
pe1 = 30
# % of the population to choose for mutation
pe2 = 20
# minimum distance between 2 cities for natural selection
epsilon = 2


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
    	self.cityList = cityList[:]
    def len(self):
        """Process the length of a route"""
        length = 0
        for i in range(len(self.cityList)-1):
    		length += dist2City(self.cityList[i], self.cityList[i+1])
    	# Add the distance between the first and last element of the cityList
    	length += dist2City(self.cityList[0], self.cityList[-1])
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
	
def generateRoutes(listRoutes, baseRoute):
    """generate the number of listRoutes required"""
    cpt=1
    cityList = []
    # The city list contains already the last city
    lenCityList = len(baseRoute.cityList)
    indexList = []
    indexList.append(range(lenCityList))
    while cpt<=initialRoutesNumber-1 and cpt<=(maxPossibilities(lenCityList)-1):
        tmp = shake(lenCityList)
        while tmp in indexList:
            tmp = shake(lenCityList)
        indexList.append(tmp)
        cpt += 1
        
    for j in indexList:
        cityList = []
        for i in j:
            cityList.append(baseRoute.cityList[i])
        tmpRoute = Route(cityList)
        listRoutes.append(tmpRoute)
        
    return len(listRoutes)

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
    return indexList
    
def maxPossibilities(lenCityList):
    """return the maximum number of different listRoutes"""
    return fac(lenCityList-1)

def selection(listRoutes, pe, initialRoutesNumber):
    R = int(initialRoutesNumber * (pe/100.0))
    # We sort the individual in lenght-value order
    listRoutes.sort(key=lambda r:r.len())
    
    # Eliminate all similar individuals if the difference < epsilon
    i=0
    while i<len(listRoutes)-1 and R > 0:
        if (listRoutes[i].len() - listRoutes[i+1].len() < epsilon):
            j = i+1
            while (j <len(listRoutes) and listRoutes[i].len() - listRoutes[j].len() < epsilon and R > 0):
                listRoutes.remove(listRoutes[j])
                j += 1
                R -= 1
        i += 1
    
    # Eliminate the other individuals in the order of lowest lenght-value order
    while R > 0:
        listRoutes.pop(len(listRoutes)-1)
        R -= 1
        
def crossover(listRoutes, pe, initialRoutesNumber):
    R = int(initialRoutesNumber * (pe/100.0))
    
    pairList = []    
    # Select R number of pair city
    while R > 0:
        route1 = listRoutes[randint(0,len(listRoutes)-1)]
        route2 = listRoutes[randint(0,len(listRoutes)-1)]
        while route1 == route2 or (route1,route2) in pairList or (route2,route1) in pairList:
            route1 = listRoutes[randint(0,len(listRoutes)-1)]
            route2 = listRoutes[randint(0,len(listRoutes)-1)]
        pairList.append((route1,route2))
        R -= 1
        
    # Make the crossover
    for p in pairList:
        # Route length - first city -last city
        lenRoute = len(p[0].cityList)-1
        # Choose a random city (except the starting city: first and last in list)
        city = p[0].cityList[randint(1,lenRoute)]
        
        iRoute1 = p[0].cityList.index(city)
        iRoute2 = p[1].cityList.index(city)
        cities = p[0].cityList[:]
        genRoute = []
        genRoute.append(city)
        
        canMove1 = True
        canMove2 = True
        while canMove1 or canMove2:
            # Must vary from 1 to lenRoute-1
            iRoute1 = (iRoute1-1) % lenRoute
            iRoute2 = (iRoute2+1) % lenRoute
            if canMove1:
                if p[0].cityList[iRoute1] not in genRoute:
                    # Add the new city at the beginning of the generate list
                    cities.remove(p[0].cityList[iRoute1])
                    genRoute.insert(0, p[0].cityList[iRoute1])
                else:
                    canMove1 = False
            if canMove2:
                if p[1].cityList[iRoute2] not in genRoute:
                    # Add the new city at the end of the generate list
                    cities.remove(p[1].cityList[iRoute2])
                    genRoute.append(p[1].cityList[iRoute2])
                else:
                    canMove2 = False
                    
        # Add randomly the remaining cities                
        while (len(genRoute) < lenRoute):
            iCity = randint(0, len(cities)-1)
            while cities[iCity] in genRoute:
                iCity = randint(0, len(cities)-1)
            genRoute.append(cities[iCity])
                    
        # Add the crossover Route to the list Routes    
#        if genRoute not in listRoutes:
        listRoutes.append(Route(genRoute))
            
def swapRoute(route,i,j):
    tmp = route.cityList[i:j]
    tmp.reverse()
    tmpRoute = Route(route.cityList)
    tmpRoute.cityList[:] = route.cityList[:i]+tmp[:] + route.cityList[j:]    
    return tmpRoute

def mutation(listRoutes, pe, initialRoutesNumber):
    # Retrieve pe% of individuals (- the elite individual)
    R = int(initialRoutesNumber * (pe/100.0)) -1
    mutationPop = []
    # Allways add the elite individual
    mutationPop.append(listRoutes[0])
    while R > 0:
        route1 = listRoutes[randint(0,len(listRoutes)-1)]
        while route1 in  mutationPop:
            route1 = listRoutes[randint(0,len(listRoutes)-1)]
        mutationPop.append(route1)
        R -= 1
    
    for route in mutationPop:
        for i in range(len(route.cityList)):
            for j in range(i+1,len(route.cityList)):
                tmpRoute = swapRoute(route,i,j)
                if (tmpRoute.len() < route.len()):
                    route = tmpRoute
        
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
    
    new.reverse()
    cities = new
    
    baseRoute = Route(cities)
    
    listRoutes=[]
    
    print "\n*** GENERATE ROUTES ***"
    initialRoutesNumber = generateRoutes(listRoutes, baseRoute)
    print "after generateRoutes :"
    for r in listRoutes:
        print r
    
    while(True):
        print "\n*** SELECTION ***"
        selection(listRoutes, pe1, initialRoutesNumber)
        print "after selection :"
        for r in listRoutes:
            print r
        
        print "\n*** CROSSOVER ***"        
        crossover(listRoutes, pe1, initialRoutesNumber)
        print "after crossover :"
        for r in listRoutes:
            print r
    
        print "\n*** MUTATION ***"                
        mutation(listRoutes, pe2, initialRoutesNumber)
        print "after mutation :"
        for r in listRoutes:
            print r
    
        bestRoute = listRoutes[0]
        for r in listRoutes:
            if r.len() < bestRoute.len():
                bestRoutes = r
        
        pos = []
        [pos.append((c.x,c.y)) for c in cities]
        if gui:
            pygame.draw.lines(screen,city_color,True,pos)
            text = font.render("Un chemin, pas le meilleur!", True, font_color)
            textRect = text.get_rect()
            screen.blit(text, textRect)
            pygame.display.flip()

        time.sleep(2)

if __name__ == '__main__':
    main()
