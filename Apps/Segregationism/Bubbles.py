#!/usr/bin/env python3
""" @brief  Social Bubble formation due to recommender systems:
The point is to show that isolated communities emerge due to recommendation
based on resemblance
"""


#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2025-11-16                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes/annotated.html     #
#============================================================================#


##############################################################################
# Social Bubble formation due to recommender systems                         #
##############################################################################

import sys
import 
sys.path.append('..')
sys.path.append('../../..')

import random
from math import copysign
from sklearn.cluster import MiniBatchKMeans, KMeans
from collections import deque, defaultdict

import Evolife.Ecology.Observer as EO
import Evolife.Graphics.Evolife_Window as EW
import Evolife.Graphics.Landscape as Landscape
import Evolife.Scenarii.Parameters as EPar

INDIV_ASPECT = ('red', -1)	# negative size makes it zoomable
FILM_ASPECT = ('green', -2)	# negative size makes it zoomable
ERASE_ASPECT = (1,1,-1,)	# negative colour erases from display


class Scenario(EPar.Parameters):
	def __init__(self):
		# Parameter values
		EPar.Parameters.__init__(self, CfgFile='_Params.evo')	# loads parameters from configuration file
		#############################
		# Global variables		    #
		#############################

		
class Individual:
	""" Defines individual agents
	"""
	def __init__(self, ID, Type='individual', Aspect=INDIV_ASPECT):
		# print 'creating', self.ID
		self.ID = ID
		self.Aspect = Aspect
		self.Type = Type
		def randomLoc():	
			return (random.randint(0, Gbl['LandSize']-1),
						random.randint(0, Gbl['LandSize']-1))
		self.Location = None
		while True:
			if self.move(randomLoc()):	break
		self.cluster = None

		
	def display(self):
		Observer.record((self.ID, self.Location + self.Aspect)) # for ongoing display
	
	def erase(self, display=False):
		"""	erase individual from current location and possibly from display 
		"""
		if self.Location: 	Land.Modify(self.Location, None)	# delete old location
		self.Location = None
		if display:	 Observer.record((self.ID, ERASE_ASPECT))
		
	def move(self, Location):
		"""	moves agent to Location  
		"""
		if Location == self.Location:	return False
		if Land.Modify(Location, self, check=True):
			self.erase()
			self.Location = Location
			self.display()
			return True
		return False
		
	def closer(self, Location):
		"""	moves agent closer to Location 
		"""
		delta = [0,0]
		NewLoc = [0,0]
		for coord in (0,1):
			delta[coord] = (Location[coord] - self.Location[coord])
			# if abs(delta[coord]) > max(Gbl['InfluenceRadius'], Gbl['NeighbourhoodRadius']) + 1:
			# # # # if abs(delta[coord]) > Gbl['InfluenceRadius'] + Gbl['NeighbourhoodRadius'] + 1:
				# # # # # correcting for toric conversion
				# # # # delta[coord] += int(copysign(Land.Dimension[coord], -delta[coord]))
			delta[coord] =  round((delta[coord] * Gbl['Influence']) / 100.0)
			NewLoc[coord] = self.Location[coord] + delta[coord]
		# if tuple(NewLoc) == self.Location:
			# print(self, delta, Location)
		# ___OldLoc = self.Location[:]
		if self.move(Land.ToricConversion(tuple(NewLoc))):
			# print(Location, ___OldLoc, delta, self.Location)
			pass
		
	
	def inspect(self, Type, radius):
		"""	inspect neighbourhood to find items of type 'Type' (eg. films or other individuals) 
		"""
		Neighbourhood = list(Land.neighbours(self.Location, radius))
		return [Land.Content(loc) for loc in Neighbourhood 
			if Land.Content(loc) and Land.Content(loc).Type == Type]
		

	def __str__(self):	return '%s(%dx%d)' % ((self.ID,) +  self.Location)
	
class Film(Individual):
	def __init__(self, ID):
		super().__init__(ID, Type='film', Aspect=FILM_ASPECT)


class Population:
	"""	defines the set of individuals 
	"""
	def __init__(self, popSize):
		"""	creates a population of agents 
		"""
		self.popSize = popSize
		print("population size: %d" % self.popSize)
		self.members = [Individual('I%s' % str(ID).rjust(4,'0')) for ID in range(popSize)]
		self.CallsSinceLastMove = 0  # counts the number of times agents were proposed to move since last actual move
		self.films = []		# recent films
		self.currentFilm = None
	
		# Cluster all individuals into K clusters using KMeans
		K = 10
		# Collect positions of all individuals
		positions = [indiv.Location for indiv in self.members]
		# Fit KMeans
		if len(positions) >= K:
			kmeans = KMeans(n_clusters=K, n_init=10)
			labels = kmeans.fit_predict(positions)
			# Optionally, store or use the cluster labels
			for indiv, label in zip(self.members, labels):
				indiv.ClusterLabel = label
		else:
			for indiv in self.members:
				indiv.ClusterLabel = 0  # fallback: assign all to one cluster
		
		# Store cluster centers and WCSS (within-cluster sum of squares)
		if len(positions) >= K:
			self.ClusterCenters = kmeans.cluster_centers_
			self.WCSS = kmeans.inertia_
		else:
			self.ClusterCenters = None
			self.WCSS = None

		# Initialize MiniBatchKMeans with KMeans centers if available
		if self.ClusterCenters is not None:
			mbkmeans = MiniBatchKMeans(n_clusters=K, init=self.ClusterCenters, n_init=1, batch_size=20)
			mbkmeans.cluster_centers_ = self.ClusterCenters
			self.clustering = mbkmeans
			self.MiniBatchLabels = mbkmeans.labels_
			self.ClusterCenters = mbkmeans.cluster_centers_
			self.WCSS = mbkmeans.inertia_

			
	def selectIndividual(self):	return random.choice(self.members)
	
	def One_Decision(self):
		""" This function is repeatedly called by the simulation thread.
			One agent is randomly chosen and decides what it does
		"""

		# sets StepId
		Observer.season()  
		if self.currentFilm is None:# Creating film
			self.currentFilm = Film('F%d' % Observer.StepId)
			for film in self.films[:-Gbl['DisplayTrail']]:
				film.erase(display=True)
			return True
			
		# Influence of films on individuals
		DirectlyConcerned = self.currentFilm.inspect(Type='individual', 
			radius=Gbl['InfluenceRadius'])
		DirectlyConcerned = random.sample(DirectlyConcerned, 
			len(DirectlyConcerned) * Gbl['InfluenceRatio'] // 100)

		# making ground copy	
		Concerned = DirectlyConcerned[:]	

		for indiv in DirectlyConcerned:	# Influence of individuals on individuals
			IndirectlyConcerned = indiv.inspect(Type='individual', radius=Gbl['NeighbourhoodRadius'])
			IndirectlyConcerned = random.sample(IndirectlyConcerned, 
				len(IndirectlyConcerned) * Gbl['InfluenceRatio'] // 100)
			Concerned += IndirectlyConcerned
		for indiv in Concerned:	indiv.closer(self.currentFilm.Location)

		self.films.append(self.currentFilm)
		self.currentFilm = None
		
		# Perform MiniBatchKMeans clustering on the locations of all Concerned individuals
		if Concerned:
			concerned_positions = [indiv.Location for indiv in Concerned]
			self.clustering.partial_fit(concerned_positions)
			self.MiniBatchLabels = self.clustering.labels_
			self.ClusterCenters = self.clustering.cluster_centers_
			self.WCSS = self.clustering.inertia_
		
		# Predict cluster for all individuals and save to individual.cluster
		positions = [indiv.Location for indiv in self.members]
		if hasattr(self, 'clustering') and self.clustering is not None and positions:
			predicted_clusters = self.clustering.predict(positions)
			for indiv, cluster in zip(self.members, predicted_clusters):
				indiv.cluster = cluster
		
		# For each cluster, compute the largest continuous patch (connected component) size
		def get_neighbors(loc):
			# 4-connected neighbors (up, down, left, right)
			x, y = loc
			neighbors = [
				((x - 1) % Gbl['LandSize'], y),
				((x + 1) % Gbl['LandSize'], y),
				(x, (y - 1) % Gbl['LandSize']),
				(x, (y + 1) % Gbl['LandSize']),
			]
			return neighbors

		# Group individuals by cluster
		cluster_to_inds = defaultdict(list)
		for indiv in self.members:
			if hasattr(indiv, 'cluster'):
				cluster_to_inds[indiv.cluster].append(indiv)

		self.LargestPatchSizes = {}  # cluster_id -> largest patch size
		self.IndividualPatchSizes = {}  # indiv.ID -> patch size
		self.PatchSizes = {}  # cluster_id -> list of patch sizes
		self.MeanPatchSizes = {}  # cluster_id -> mean patch size

		for cluster_id, inds in cluster_to_inds.items():
			# Build set of locations for this cluster
			loc_to_indiv = {indiv.Location: indiv for indiv in inds}
			unvisited = set(loc_to_indiv.keys())
			largest_patch = 0
			indiv_patch_size = {}
			patch_sizes = []

			while unvisited:
				start = unvisited.pop()
				queue = deque([start])
				patch = {start}
				while queue:
					loc = queue.popleft()
					for n in get_neighbors(loc):
						if n in unvisited and n in loc_to_indiv:
							unvisited.remove(n)
							queue.append(n)
							patch.add(n)
				# Mark patch size for all individuals in this patch
				for loc in patch:
					indiv_patch_size[loc_to_indiv[loc].ID] = len(patch)
				patch_sizes.append(len(patch))
				if len(patch) > largest_patch:
					largest_patch = len(patch)

			self.LargestPatchSizes[cluster_id] = largest_patch
			self.PatchSizes[cluster_id] = patch_sizes
			self.MeanPatchSizes[cluster_id] = sum(patch_sizes) / len(patch_sizes) if patch_sizes else 0
			self.IndividualPatchSizes.update(indiv_patch_size)

		# indiv = self.selectIndividual()	# indiv who will play the game	
		self.CallsSinceLastMove += 1
		if self.CallsSinceLastMove > 100 * self.popSize:
			return False	# situation is probably stable
		return True	# simulation goes on
			   


if __name__ == "__main__":
	print(__doc__)

	
	#############################
	# Global objects			#
	#############################
	Gbl = Scenario()
	# optional determinism:
	if Gbl.Parameter('RandomSeed', Default=0) > 0:	random.seed(Gbl['RandomSeed'])
	Observer = EO.Observer(Gbl)	  # Observer contains statistics
	Land = Landscape.Landscape(Gbl['LandSize'])	  # logical settlement grid
	Pop = Population(Gbl['PopulationSize'])
	
	# Observer.recordInfo('Background', 'white')
	Observer.recordInfo('FieldWallpaper', 'white')
	Observer.recordInfo('DefaultViews',	[('Field', 800, 720)])	# Evolife should start with these windows open - these sizes are in pixels
	
	
	EW.Start(Pop.One_Decision, Observer, Capabilities='RP')

	print("Bye.......")
	
__author__ = 'Dessalles'
__author__ = 'Dessalles'
