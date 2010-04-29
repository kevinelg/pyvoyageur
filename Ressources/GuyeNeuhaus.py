#!/usr/bin/env python
# encoding: utf-8
''' 
GuyeNeuhaus.py

Created by Raphael Guye and Jonathan Neuhaus on 2010-04-14.
Copyright (c) 2010 HE-Arc. All rights reserved.
''' 

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
from threading import Thread
from threading import Event
from Queue import *
try:
	import psyco
	psyco.full()
except ImportError:
	pass

#================================================
#              VARIABLES GLOBALES
#================================================

# -------- GUI -------- #
text = None
screen = None
font = None
screen_x = 500
screen_y = 500
city_color = [255,0,0]      # blue graph between listCities
city_radius = 3             # circle radius when user click a city
font_color = [255,255,255]  # white font for text

# ------ ga tools ----- #
result = Queue(1)           # finish result - best routes
listCities = []             # each cities click bye user
stopRunning = False         # True when maxime is done

# ---- ga constants --- #
initialRoutesNumber = 100   # maximum number of initial routes
pe1 = 0                    # % of the population to eliminate and then add by crossover
pe2 = 100                    # % of the population to choose for mutation (dynamic)
epsilonDistCities = 5       # minimum distance between 2 listCities for natural selection


#================================================
#              Classes
#================================================

class City(object):
    ''' Representation of a city''' 
    __slots__ = ['x','y','name']
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name

    def __str__(self):
      # return self.name + " : " + str(self.x) +","+ str(self.y)
        return self.name

    def nearest(self, listCities, listCitiesCheck):
        ''' In  :   listCities as the list contains ALL of the cities
        listCitiesCheck as the list contains all the cities already treated
        Out :   The nearest city of self that it isn't contained in listCitiesCheck.'''
        cityNearest = listCities[0]
        i=1
        while cityNearest == self or cityNearest in listCitiesCheck:
            cityNearest = listCities[i]
            i+=1
        smallDistance = dist2City(self,cityNearest)

        for c in listCities:
            if dist2City(self, c) < smallDistance and c <> self and c not in listCitiesCheck:
                cityNearest = c
                smallDistance = dist2City(self,cityNearest)

        return cityNearest

class Route(object):
    ''' Route with each cities '''
    __slots__ = ['cityList']
    def __init__(self, cityList):
    	self.cityList = cityList[:]
        
    def len(self):
        ''' Process the length of a route''' 
        length = 0
        for i in range(len(self.cityList)-1):
    		length += dist2City(self.cityList[i], self.cityList[i+1])
                
    	# Add the distance between the first and last element of the cityList
    	length += dist2City(self.cityList[0], self.cityList[-1])
        return length
        
    def isEgal(self, route):
        ''' Check if the 2 listRoutes are equal''' 
        if (len(self.cityList) <> route.len()):
            return False
        
        for i in range(len(self.cityList)):
            if (self.cityList[i]<>route[i]):
                return False
        return True


    def isContained(self, listRoutes):
        ''' Check if the self route is contained in the listRoutes ''' 
        for r in listRoutes:
            if r.isEgal(self):
                return True
        return False
        
    def __str__(self):
        tmp = "len : "
        tmp += str(self.len()) + "\n"
        for c in self.cityList:
            tmp += str(c)
            tmp += " / "
        return tmp
        
class GeneticAlgorithm(object):
    ''' Contains all the genetics methodes to solve the problem '''
    def __init__(self,listRoutes,pe1,pe2, initialRoutesNumber):
        self.listRoutes = listRoutes
        self.pe1 = pe1
        self.pe2 = pe2
        print "pe1 :", pe1
        print "pe2 :", pe2
        self.initialRoutesNumber = initialRoutesNumber
        
    # -------------------------------- #
    # -- Central algorithm methodes -- #
    # -------------------------------- #
        
    #@speedMeasure
    def selection(self):
        R = int(self.initialRoutesNumber * (self.pe1/100.0))
        # We sort the individual in lenght-value order
        self.listRoutes.sort(key=lambda r:r.len())
            
        # Eliminate all similar individuals if the difference < epsilonDistCities
        # TODO: optimize this part (create a temp array to hold the route to remove)
        i=0
        while i<len(self.listRoutes)-1 and R > 0:
            if (self.listRoutes[i].len() - self.listRoutes[i+1].len() < epsilonDistCities):
                j = i+1
                while (j <len(self.listRoutes) and self.listRoutes[i].len() - self.listRoutes[j].len() < epsilonDistCities and R > 0):
                    self.listRoutes.remove(self.listRoutes[j])
                    j += 1
                    R -= 1
            i += 1
            
        # Eliminate the other individuals in the order of lowest lenght-value order
        while R > 0:
            self.listRoutes.pop(len(self.listRoutes)-1)
            R -= 1
    
    #@speedMeasure
    def crossover(self):
        R = int(self.initialRoutesNumber * (self.pe1/100.0))
            
        pairList = []    
        # Select R number of pair city
        while R > 0:
            route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            route2 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            while route1 == route2 or (route1,route2) in pairList or (route2,route1) in pairList:
                route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
                route2 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
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
            listCities = p[0].cityList[:]
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
                        listCities.remove(p[0].cityList[iRoute1])
                        genRoute.insert(0, p[0].cityList[iRoute1])
                    else:
                        canMove1 = False
                if canMove2:
                    if p[1].cityList[iRoute2] not in genRoute:
                        # Add the new city at the end of the generate list
                        listCities.remove(p[1].cityList[iRoute2])
                        genRoute.append(p[1].cityList[iRoute2])
                    else:
                        canMove2 = False
    
            # Add randomly the remaining listCities
            genRoute = genRandomCities(genRoute, lenRoute, listCities)
    
            # if the genRoute already exist, we generate a random route. So: no redundancy
            # while (genRoute in self.listRoutes):
            #     genRoute = []
            #     genRoute = genRandomCities(genRoute, lenRoute, listCities)
                        
            self.listRoutes.append(Route(genRoute))
    
    #@speedMeasure
    def mutation(self):
        # Retrieve pe% of individuals (- the elite individual)
        R = int(self.initialRoutesNumber * (self.pe2/100.0))-1
        mutationPop = []
        # Allways add the elite individual
        mutationPop.append(self.listRoutes[0])
        self.listRoutes.remove(self.listRoutes[0])
        while R > 0:
            route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            while route1 in mutationPop:
                route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            mutationPop.append(route1)
            self.listRoutes.remove(route1)
            R -= 1
    
        for route in mutationPop:
            for i in range(len(route.cityList)):
                for j in range(i+1,len(route.cityList)):
                    if stopRunning:
                        break
                    # Check if a cities inversion is better (Method give not good results)
                    #if gainSwapCities(route,i,j) > 0:
                    #    route = swapCities(route,i,(j)%len(route.cityList))
                    # Check if a route inversion is better
                    if self.gainSwapRoute(route,i,j) > 0:
                        route = self.swapRoute(route,i,(j+1)%len(route.cityList))
                if stopRunning:
                    break
            if stopRunning:
                break
            self.listRoutes.append(route)
    
    # ------------------------------ #
    # -- Tools algorithm methodes -- #
    # ------------------------------ #
    
    def sortListRoutesByLength(self):
        self.listRoutes.sort(key=lambda r:r.len())
    
    def genRandomCities(self,genRoute, lenRoute, listCities):
        while (len(genRoute)-1 < lenRoute):
                iCity = randint(0, len(listCities)-1)
                while listCities[iCity] in genRoute:
                    iCity = randint(0, len(listCities)-1)
                genRoute.append(listCities[iCity])
        return genRoute
    
    def swapRoute(self,route,i,j):
        # Method 1
        tmp = route.cityList[i:j]
        tmpRoute = Route(route.cityList)
        tmpRoute.cityList[i:j] = tmp[::-1]
            
        # Method 2: OTHER SOLUTION (a bit slower)        
        # tmpRoute = Route(route.cityList)
        # tmpRoute.cityList[i:j] = route.cityList[i:j][::-1]
        return tmpRoute
    
    def swapCities(self,route,i,j):
        # Method 1
        tmp = route.cityList[i]
        tmpRoute = Route(route.cityList)
        tmpRoute.cityList[i] = tmpRoute.cityList[j]
        tmpRoute.cityList[j] = tmp
            
        # Method 2: OTHER SOLUTION (a bit slower)        
        # tmpRoute = Route(route.cityList)
        # tmpRoute.cityList[i:j] = route.cityList[i:j][::-1]
        return tmpRoute
    
    def gainSwapRoute(self,route, i, j):
        lenRoute = len(route.cityList)
        return dist2City(route.cityList[(i-1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[j]) - (dist2City(route.cityList[(i-1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[i]))
    
    def gainSwapCities(self,route, i, j):
        lenRoute = len(route.cityList)
        tmp1 = dist2City(route.cityList[(i-1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(i+1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(j-1)%lenRoute], route.cityList[j])
        tmp2 = dist2City(route.cityList[(i-1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(i+1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(j-1)%lenRoute], route.cityList[i])
        return tmp1 - tmp2
        
class Resolution(Thread):
    ''' Class called to solve the problem in a thread '''
    def __init__(self, listRoutes, gui):
        Thread.__init__(self)
        self._stopevent = Event( )
        self.listRoutes = listRoutes
        self.gui = gui
        print "T pe2 = ",pe2
        
    def stop(self):
        ''' thread asked to be stopped '''
        global stopRunning
        self._stopevent.set()
        stopRunning = True
        
    def run(self):
        ''' the main fonction to solve the problem '''
        lastResults= [0,0]
        sd = sys.maxint
        bestRoute= self.listRoutes[0]
        genAlgo = GeneticAlgorithm(self.listRoutes,pe1,pe2, initialRoutesNumber)
        while(sd > 1 and not self._stopevent.isSet()):
            genAlgo.selection()
            genAlgo.crossover()
            genAlgo.mutation()

            genAlgo.sortListRoutesByLength()

            # Process the standard deviation
            bestRoute = genAlgo.listRoutes[0]
            lastResults.pop()
            lastResults[1:] = lastResults[0:]
            lastResults[0] = bestRoute.len()
            
            sd = standartDeviation(lastResults)

            if self.gui:
                drawRoute(bestRoute)
        result.put(bestRoute)

#================================================
#              Main
#================================================

def main():
    global text
    usage =''' usage: %prog [options] [filename]
This script is intend to solve the Travel Salesman problem (TSP) problem.

[filename] is a file that contains the coordinates of the cities.
The format of this file is: NAME1 XPos1 YPos1
It is an optional argument.''' 

    parser = OptionParser(usage)
    parser.add_option("-n","--nogui", action="store_false", dest="gui", default=True, help="Do not use a graphical representation")
    parser.add_option("-m","--maxtime", type="int", dest="maxtime", default=0, help="Force the algorithm to stop after the given time (in seconds)")
    (options, args) = parser.parse_args()

    # Retrieve the options
    filename = None
    collecting = True
    if args<>[] and os.path.isfile(args[-1]):
        filename = args[-1]
        collecting = False
    initPygame()
    drawCities(listCities)

    while collecting:
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_RETURN:
                collecting = False
            elif event.type == MOUSEBUTTONDOWN:
                (x,y) = pygame.mouse.get_pos()
                listCities.append(City(x,y,"v" + str(len(listCities))))
                drawCities(listCities)
    screen.fill(0)
    ga_solve(filename, options.gui, options.maxtime)
        
    while True:
        event = pygame.event.wait()
        if event.type == KEYDOWN: break

#================================================
#              Methodes
#================================================

def fac(n):
    ''' Return the factorial of a number''' 
    p=1
    for i in range(1,n+1):
        p*=i
    return p

def dist2City(city1, city2):
    ''' return the distance between 2 listCities''' 
    return math.sqrt((city1.x-city2.x)**2 + (city1.y-city2.y)**2)

#@speedMeasure
def generateRoutes(listRoutes, baseRoute):
    ''' generate the number of listRoutes required''' 
    cpt=1
    lenCityList = len(baseRoute.cityList)    
    # Generate a random indexList
    indexList = []
    indexList.append(range(lenCityList))
    while cpt <= (initialRoutesNumber - 1) and cpt <= (maxPossibilities(lenCityList) - 1):
        tmp = shake(lenCityList)
        while tmp in indexList:
            tmp = shake(lenCityList)
        indexList.append(tmp)
        cpt += 1
        
    # generate the baseRoute list with the generated indexList
    for j in indexList:
        cityList = []
        [cityList.append(baseRoute.cityList[i]) for i in j]
        listRoutes.append(Route(cityList))
        
    return len(listRoutes)

def shake(initialList):
    ''' Return a list of index shaken ''' 
    indexList = []
    # The first element is allways the starting city
    indexList.append(0)
        
    for cpt in range(initialList-1):
        i = randint(1,initialList-1)
        while (i in indexList):
            i = randint(1,initialList-1)
        indexList.append(i)
    return indexList
        
def maxPossibilities(lenCityList):
    ''' return the maximum number of different listRoutes'''
    return fac(lenCityList-1)

def standartDeviation(tab):
    ''' calcul and return the standart deviation''' 
    moyenne = 0
    for t in tab:
        moyenne += t
    moyenne /= len(tab)
    et = 0
    for t in tab:
        et += (t-moyenne)**2
    return math.sqrt(et)
    
# ------------------ #
# -- gui methodes -- #
# ------------------ #

def initPygame():
    global screen
    global font
    pygame.init() 
    window = pygame.display.set_mode((screen_x, screen_y)) 
    pygame.display.set_caption('Exemple') 
    screen = pygame.display.get_surface() 
    font = pygame.font.Font(None,30)

def drawCities(listCities):
    screen.fill(0)
    [pygame.draw.circle(screen,city_color,(c.x,c.y),city_radius) for c in listCities]
    text = font.render("Nombre: %i" % len(listCities), True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()

def drawRoute(route):
    screen.fill(0)
    pos = []
    [pos.append((c.x,c.y)) for c in route.cityList]
    [pygame.draw.lines(screen,city_color,True,pos) for c in pos]
    text = font.render("Length = "+str(route.len()) , True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()

def notTooBadSorting(listCities):
    ''' Just for begin with a first route "not too bad". Generate a route looking "each nearest" city WITHOUT complexe check ! ''' 
    newCities = []
    newCities.append(listCities[0])
    for i in range(len(listCities)):
        if i != 0:
            city = newCities[i-1].nearest(listCities,newCities)
            newCities.append(city)
    return newCities

@speedMeasure
def ga_solve(file=None, gui=True, maxtime=0):
    ''' Resolution of the city traveller problem''' 
    global listCities, pe2, initialRoutesNumber 
        
    if file != None:
        f = open(file,"r")
        listCities = [City(int(l.split(" ")[1]),int(strip(l.split(" ")[2])),l.split(" ")[0]) for l in f]
        
    new = []
    [new.insert(0,c) for c in listCities]
    new.reverse()
    listCities = new
    
    # First base route (random => so very bad route...)
    badRoute = Route(listCities)

    # Optimize the base route
    listCities = notTooBadSorting(listCities)
    baseRoute = Route(listCities)
        
    if gui:
        drawRoute(baseRoute)        
    
    # dynamic adaptation of the factors
    if len(baseRoute.cityList)<50:
        pe2 = 100
        initialRoutesNumber = 100
    else:
        pe2 = 114 -7.0/25*len(baseRoute.cityList)
        initialRoutesNumber = 67 + 2.0/3*len(baseRoute.cityList)
    if pe2<10:
        pe2 = 10

    listRoutes=[]
    initialRoutesNumber = generateRoutes(listRoutes, baseRoute)
    
    resolution = Resolution(listRoutes, gui)
    resolution.start()
    if (maxtime > 0):
        time.sleep(maxtime)
        resolution.stop()
    bestRoute = result.get()
    tmp =(bestRoute.len(), [c.name for c in bestRoute.cityList[:]])
    return tmp

if __name__ == '__main__':
    main()