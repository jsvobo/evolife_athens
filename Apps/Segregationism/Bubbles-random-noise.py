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

sys.path.append('..')
sys.path.append('../../..')

import random
from collections import defaultdict, deque
from math import copysign, exp, sqrt

import Evolife.Ecology.Observer as EO
import Evolife.Graphics.Evolife_Window as EW
import Evolife.Graphics.Landscape as Landscape
import Evolife.Scenarii.Parameters as EPar

INDIV_ASPECT = ('red', -1)	# negative size makes it zoomable
FILM_ASPECT = ('green', -2)	# negative size makes it zoomable
ERASE_ASPECT = (1,1,-1,)	# negative colour erases from display

EvolifeColours = ['#808080', '#000000', '#FFFFFF', '#0000FF', '#FF0000', '#FFFF00', '#A06000', '#0080A0', '#FF80A0', '#94DCDC', 
			'#008000', '#009500', '#00AA00', '#00BF00', '#00D400', '#00E900', '#00FE00', '#64FF64', '#78FF78', '#8CFF8C', '#A0FFA0', '#B4FFB4',
			'#800000', '#950000', '#AA0000', '#BF0000', '#D40000', '#E90000', '#FE0000', '#FF6464', '#FF7878', '#FF8C8C', '#FFA0A0', '#FFB4B4',
			'#000080', '#101095', '	#2020AA', '#3030BF', '#3838D4', '#4747E9', '#5555FE', '#6464FF', '#7878FF', '#8C8CFF', '#A0A0FF', '#B4B4FF',
			'#FF8C00',
		   ]
EvolifeColourNames = ['grey', 'black', 'white', 'blue', 'red', 'yellow', 'brown', 'blue02', 'pink', 'lightblue', 
			'green', 'green1', 'green2', 'green3', 'green4', 'green5', 'green6', 'green7', 'green8', 'green9', 'green10', 'green11',  # 21
			'red0', 'red1', 'red2', 'red3', 'red4', 'red5', 'red6', 'red7', 'red8', 'red9', 'red10', 'red11', # 33
			'blue0', 'blue1', 'blue2', 'blue3', 'blue4', 'blue5', 'blue6', 'blue7', 'blue8', 'blue9', 'blue10', 'blue11',
			'orange',
			]

cluster_aspect = {
	1: ("green", -1),
	2: ("red", -1),
	3: ("blue", -1),
	4: ("orange", -1),
	5: ("green6", -1),
	6: ("red6", -1),
	7: ("blue6", -1),
	8: ("pink", -1),
	9: ("brown", -1),
	10: ("yellow", -1),
}

class StepingKmeans:
	def __init__(self, n_clusters=6, max_iter=100):
		self.n_clusters = n_clusters
		self.max_iter = max_iter
		self.cluster_centers_ = None
		self.labels_ = None
		self.inertia_ = None

	def fit(self, X):
		# X: list of tuples (positions)
		X = [tuple(x) for x in X]
		if len(X) < self.n_clusters:
			raise ValueError("Not enough points to form clusters")
		# Randomly initialize centers
		centers = random.sample(X, self.n_clusters)
		for _ in range(self.max_iter):
			# Assign points to nearest center
			labels = []
			for x in X:
				dists = [((x[0]-c[0])**2 + (x[1]-c[1])**2) for c in centers]
				labels.append(dists.index(min(dists)))
			# Update centers
			new_centers = []
			for k in range(self.n_clusters):
				members = [x for x, l in zip(X, labels) if l == k]
				if members:
					cx = sum(p[0] for p in members) / len(members)
					cy = sum(p[1] for p in members) / len(members)
					new_centers.append((cx, cy))
				else:
					# Reinitialize empty cluster
					new_centers.append(random.choice(X))
			if all(abs(a-b) < 1e-4 for c1, c2 in zip(centers, new_centers) for a, b in zip(c1, c2)):
				break
			centers = new_centers
		self.cluster_centers_ = centers
		self.labels_ = labels
		# Compute inertia (WCSS)
		inertia = 0.0
		for x, l in zip(X, labels):
			c = centers[l]
			inertia += (x[0]-c[0])**2 + (x[1]-c[1])**2
		self.inertia_ = inertia
		return self

	def predict(self, X):
		# Assign each point to nearest center
		return [
			min(range(self.n_clusters), key=lambda k: (x[0]-self.cluster_centers_[k][0])**2 + (x[1]-self.cluster_centers_[k][1])**2)
			for x in X
		]
	
	def partial_fit(self, X):
		# X: list of tuples (positions)
		X = [tuple(x) for x in X]
		if len(X) < self.n_clusters:
			raise ValueError("Not enough points to form clusters")
		# Use previous centers if available, else random
		if self.cluster_centers_ is not None:
			centers = list(self.cluster_centers_)
		else:
			centers = random.sample(X, self.n_clusters)
		for _ in range(int(self.max_iter/10)):  # fewer iterations for partial fit

			labels = []
			for x in X:
				dists = [((x[0]-c[0])**2 + (x[1]-c[1])**2) for c in centers]
				labels.append(dists.index(min(dists)))
			new_centers = []
			for k in range(self.n_clusters):
				members = [x for x, l in zip(X, labels) if l == k]
				if members:
					cx = sum(p[0] for p in members) / len(members)
					cy = sum(p[1] for p in members) / len(members)
					new_centers.append((cx, cy))
				else:
					new_centers.append(random.choice(X))
			if all(abs(a-b) < 1e-4 for c1, c2 in zip(centers, new_centers) for a, b in zip(c1, c2)):
				break
			centers = new_centers
		self.cluster_centers_ = centers
		self.labels_ = labels
		inertia = 0.0
		for x, l in zip(X, labels):
			c = centers[l]
			inertia += (x[0]-c[0])**2 + (x[1]-c[1])**2
		self.inertia_ = inertia
		
		return self

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
		self.cluster = 1
		self.Aspect = cluster_aspect.get(self.cluster, INDIV_ASPECT)

		
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
		K = 6
		# Collect positions of all individuals
		positions = [indiv.Location for indiv in self.members]
		
		# Use our prepared StepingKmeans class for clustering
		self.clustering = StepingKmeans(n_clusters=K)
		self.clustering.fit(positions)
		self.ClusterCenters = self.clustering.cluster_centers_
		self.MiniBatchLabels = self.clustering.labels_
		self.WCSS = self.clustering.inertia_

		for indiv, cid in zip(self.members, self.MiniBatchLabels):
			indiv.cluster = cid
			indiv.Aspect = cluster_aspect.get(cid+1, INDIV_ASPECT)
		
			
	def selectIndividual(self):	
		return random.choice(self.members)
	
	def One_Decision(self):
		Observer.season()
		if self.currentFilm is None:
			self.currentFilm = Film('F%d' % Observer.StepId)
			for film in self.films[:-Gbl['DisplayTrail']]:
				film.erase(display=True)
			return True

		# film -> individuals
		direct = self.currentFilm.inspect(Type='individual', radius=Gbl['InfluenceRadius'])
		k_direct = len(direct) * Gbl['InfluenceRatio'] // 100
		DirectlyConcerned = random.sample(direct, k_direct) if direct else []

		# influence propagation
		# TODO: here try different modes of influence propagation! 
		# 			different smapling?
		# 			taking larger neighborgood?
		# 			not tking the closest?
		Concerned = DirectlyConcerned[:]
		for indiv in DirectlyConcerned:
			neigh = indiv.inspect(Type='individual', radius=Gbl['NeighbourhoodRadius'])
			k_ind = len(neigh) * Gbl['InfluenceRatio'] // 100
			if neigh:
				Concerned += random.sample(neigh, k_ind)

			"""# propagate influence probabilistically using a Gaussian (normal) decay with distance
			# sigma: characteristic distance (use InfluenceRadius or fallback)
			sigma = max(1.0, float(Gbl.get('InfluenceRadius', max(1, Gbl.get('LandSize', 10)))))

			for nb in neigh:
				if nb in Concerned:
					continue
				if nb.Location is None:
					continue
				# Euclidean distance to the current film
				dx = nb.Location[0] - self.currentFilm.Location[0]
				dy = nb.Location[1] - self.currentFilm.Location[1]
				dist = sqrt(dx * dx + dy * dy)

				# Gaussian probability density (unnormalized) -> higher prob for closer neighbours
				p = exp(-0.5 * (dist / sigma) ** 2)

				# scale by InfluenceRatio
				p *= (Gbl.get('InfluenceRatio', 100) / 100.0)

				# sample
				if random.random() < p:
					Concerned.append(nb)"""

		for indiv in Concerned:
			indiv.closer(self.currentFilm.Location)

		# small random jitter for exploration
		prob = Gbl.get('RandomMoveProb', 0.1)  # probability of a small random move per individual
		for indiv in self.members:
			if indiv.Location is None:
				continue
			if random.random() < prob:
				dx = random.choice((-1, 0, 1))
				dy = random.choice((-1, 0, 1))
				if dx == 0 and dy == 0:
					continue
				new_loc = Land.ToricConversion((indiv.Location[0] + dx, indiv.Location[1] + dy))
				indiv.move(new_loc)

		self.films.append(self.currentFilm)
		self.currentFilm = None

		# clustering on all individuals using partial_fit
		all_positions = [indiv.Location for indiv in self.members]
		if getattr(self, 'clustering', None) is not None and all_positions:
			self.clustering.partial_fit(all_positions)
			self.ClusterCenters = self.clustering.cluster_centers_
			self.MiniBatchLabels = self.clustering.labels_
			self.WCSS = self.clustering.inertia_

		# predict cluster for everyone
		all_positions = [indiv.Location for indiv in self.members]
		if getattr(self, 'clustering', None) is not None and all_positions:
			for indiv, cid in zip(self.members, self.clustering.predict(all_positions)):
				indiv.cluster = cid
				indiv.Aspect = cluster_aspect.get(cid+1, INDIV_ASPECT)

		# 4-connected toroidal neighbors
		def neighbors(loc):
			x, y = loc
			L = Gbl['LandSize']
			return [((x - 1) % L, y), ((x + 1) % L, y), (x, (y - 1) % L), (x, (y + 1) % L)]

		# group by cluster & compute connected components (patches)
		cluster_to_inds = defaultdict(list)
		for indiv in self.members:
			if hasattr(indiv, 'cluster'):
				cluster_to_inds[indiv.cluster].append(indiv)

		self.LargestPatchSizes = {}
		self.IndividualPatchSizes = {}
		self.PatchSizes = {}
		self.MeanPatchSizes = {}

		# Instead of separating by clusters, compute patches over all individuals
		loc_to_ind = {ind.Location: ind for ind in self.members}
		unvisited = set(loc_to_ind.keys())
		all_patch_sizes = []
		indiv_patch = {}

		while unvisited:
			start = unvisited.pop()
			queue = deque([start])
			patch = {start}
			while queue:
				loc = queue.popleft()
				for n in neighbors(loc):
					if n in unvisited and n in loc_to_ind:
						unvisited.remove(n)
						queue.append(n)
						patch.add(n)
			size = len(patch)
			for loc in patch:
				indiv_patch[loc_to_ind[loc].ID] = size
			all_patch_sizes.append(size)

		self.LargestPatchSizes = {'all': max(all_patch_sizes) if all_patch_sizes else 0}
		self.PatchSizes = {'all': all_patch_sizes}
		self.MeanPatchSizes = {'all': (sum(all_patch_sizes) / len(all_patch_sizes)) if all_patch_sizes else 0}
		self.IndividualPatchSizes = indiv_patch

		# normalized composite objective (WCSS_per_point + lambda * PatchPenalty)
		lmbda = 0.5
		N = max(1, len(self.members))
		WCSS_per_point = (getattr(self, 'WCSS', 0.0)**0.5) / N
		
		# Compute patch_penalty as mean of patch sizes squared divided by N (over all individuals)
		patch_penalty = 0.0
		all_patch_sizes = list(set(all_patch_sizes))
		if all_patch_sizes:
			patch_penalty = sum(size for size in all_patch_sizes) / N

		self.Objective = WCSS_per_point + lmbda * patch_penalty
		self.WCSS_per_point = WCSS_per_point
		self.PatchPenalty = patch_penalty

		# draw the line with criterion!
		print("Step %d: Objective=%.4f (WCSS/point=%.4f, PatchPenalty=%.4f)" % (
			Observer.StepId,
			self.Objective,
			self.WCSS_per_point,
			self.PatchPenalty
		))

		Observer.curve("Objective", 100*self.Objective)
		Observer.curve("PatchPenalty", 100 * self.PatchPenalty)
		#Observer.curve("SqrtWCSS", 100 * ((getattr(self, 'WCSS', 0.0) ** 0.5)/N) )

		# Display all individuals after updating clusters
		for indiv in self.members:
			indiv.display()

		# housekeeping
		self.CallsSinceLastMove += 1
		if self.CallsSinceLastMove > 100 * self.popSize:
			return False
		return True


class Modified_Observer(EO.Experiment_Observer):
	def __init__(self, Params):
		super().__init__(Params)
		self.curve("Objective", Color="blue", Legend="Objective")
		self.curve("PatchPenalty", Color="red", Legend="Patch Penalty")
		#self.curve("SqrtWCSS", Color="Green", Legend="Sqrt WCSS")


if __name__ == "__main__":
	print(__doc__)
	
	#############################
	# Global objects			#
	#############################
	Gbl = Scenario()
	# optional determinism:
	if Gbl.Parameter('RandomSeed', Default=0) > 0:	random.seed(Gbl['RandomSeed'])
	Observer = Modified_Observer(Gbl)	  # Observer contains statistics
	Land = Landscape.Landscape(Gbl['LandSize'])	  # logical settlement grid
	Pop = Population(Gbl['PopulationSize'])
	
	# Observer.recordInfo('Background', 'white')
	Observer.recordInfo('FieldWallpaper', 'white')
	Observer.recordInfo('DefaultViews',	[('Field', 800, 720)])	# Evolife should start with these windows open - these sizes are in pixels
	
	
	EW.Start(Pop.One_Decision, Observer, Capabilities='RPC')
	print("Bye.......")
	
	__author__ = 'Dessalles'
