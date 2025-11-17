#!/usr/bin/env python3
""" @brief  A basic framework to run social simulations.
"""



#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2025-11-16                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes/annotated.html     #
#============================================================================#


import sys
import os.path
import random
import itertools as it
import re
from time import sleep

sys.path.append('../../..')	# to include path to Evolife

from Evolife.Scenarii import Parameters
from Evolife.Tools import Tools
from Evolife.Ecology import Observer
from Evolife.Social import Alliances
from Evolife.Ecology import Learner
from Evolife.Graphics.Curves import Shade

DUMPSTATE = True

def Once():
	global ONCE
	try:	ONCE &= False
	except NameError:	ONCE = True
	return ONCE

class Global(Parameters.Parameters):
	"""	Global elements, mainly parameters
	"""
	def __init__(self, ConfigFile='_Params.evo'):
		# Parameter values
		Parameters.Parameters.__init__(self, ConfigFile)
		self.Parameters = self	# compatibility
		self.ScenarioName = self['ScenarioName']
		# Definition of interactions
		self.Interactions = None	# to be overloaded

	def Dump_(self, PopDump, ResultFileName, DumpFeatures, ExpeID, Verbose=False):
		""" Saves agents' features (possibly including agents' distance to best friend)
		"""
		
		# ====== storing feature values 
		if DumpFeatures is None or len(DumpFeatures) == 0:	return
		FeatureValues = dict()
		for Feature in DumpFeatures:
			FeatureValues[Feature] = PopDump(Feature)
		
		# ====== Sniffing data structure
		Test = FeatureValues[DumpFeatures[0]]
		# OldStyle: [Feature, AgentOfLowestCompetence' feature value, AgentOfNextCompetence' feature value, ...]
		# NewStyle: [(Competence1, FeatureValue1), (Competence2, FeatureValue2), ...]
		OldStyle = (len(Test) > 2 and type(Test[1]) == str and re.match(r'[0-9\.]+', Test[1]))
		if OldStyle:
			Qualities = list(range(len(FeatureValues[Feature])-1))
			for Feature in DumpFeatures:
				FeatureValues[Feature] = FeatureValues[Feature][1:]
		else:	# not used
			Qualities = sorted([x[0] for x in Test])
			for Feature in DumpFeatures:
				Values = dict(FeatureValues[Feature])
				FeatureValues[Feature] = [Values[q] for q in Qualities]	# robust to duplicates
		
		DumpFileName = ResultFileName + '_dmp.csv'
		if Verbose:	print("Saving data to", DumpFileName)
		SNResultFile = open(DumpFileName, 'w')
		SNResultFile.write('#%s\n' % ExpeID)
		if OldStyle:
			for Feature in DumpFeatures:
				SNResultFile.write(f"{Feature};")
				SNResultFile.write(";".join(FeatureValues[Feature]))
				SNResultFile.write("\n")	  
		else:	#NewStyle, 	not used
			Records = zip(map(str, Qualities), *[FeatureValues[f] for f in DumpFeatures])
			SNResultFile.write("Competence;" + ";".join(DumpFeatures) + "\n")
			for R in Records:
				SNResultFile.write(";".join(R) + "\n")
		SNResultFile.close()
		
	# def Param(self, ParameterName):	return self.Parameters.Parameter(ParameterName)

class Social_Observer(Observer.Experiment_Observer):
	"""	Stores some global observation and display variables
	"""

	def __init__(self, Parameters=None):
		"""	Experiment_Observer constructor 
			+ declaration of an average social distance curve
			+ initialization of social links
		"""
		Observer.Experiment_Observer.__init__(self, Parameters)
		#additional parameters	  
		self.Alliances = []		# social links, for display
		if self.Parameter('AvgFriendDistance', Default=False):
			self.curve('FriendDistance', Color='yellow', Legend='Avg distance to best friend')
		self.recordInfo('FieldTitle', 'Signals')
		
	def getData(self, Slot, Consumption=True):
		"""	Experiment_Observer's getData + slot 'Network' that contains social links
		"""
		if Slot == 'Network':	return self.Alliances			# returns stored links
		return Observer.Experiment_Observer.getData(self, Slot, Consumption=Consumption)

	def hot_phase(self):
		"""	The hot phase is a limited amount of time, controlled by the 'LearnHorizon' parameter,
			during which learning is faster.
		"""
		HotEnd = self.TimeLimit * self.Parameter('LearnHorizon', Default=100) / 100.0
		return HotEnd < 0 or self.StepId < HotEnd

class Feature:
	"""	global properties of features:
		- Name
		- Legend
		- Color for display
		- Thickness for display
		- Start (0 for all 0 start, 1 for all 1 start, or -1 for random start)
	"""
	def __init__(self, Name='aFeature', Legend=None, Color='blue', Thickness=2):
		self.Name = Name
		if Legend is None: 
			# ====== splitting Name
			Legend = ' '.join(re.findall('[A-Z][^A-Z]*', Name))
		self.Legend = Legend
		self.Color = Color
		self.Thickness = Thickness
		self.Start = Start
		
	def __str__(self):	return self.Legend

class Social_Individual(Alliances.Friendship, Learner.Learner):
	"""	A social individual has friends and can learn
	"""

	def __init__(self, IdNb, features=[], maxCompetence=100, parameters=None):
		"""	Initalizes social links and learning parameters
		""" 
		if parameters: 	self.Param = parameters.Param
		else:	self.Param = None	# but this will provoke an error
		self.ID = "A%d" % IdNb	# Identity number
		self.DotSize = 2	# size in display. Negative value --> in proportion of window size intead of pixels
		if self.Param('SocialSymmetry', default=False):
			Alliances.Friendship.__init__(self, self.Param('MaxFriends'), self.Param('MaxFriends'))
		else:
			Alliances.Friendship.__init__(self, self.Param('MaxFriends'), self.Param('MaxFollowers', default=self.Param('MaxFriends')))
		self.Competence = (100.0 * IdNb) / maxCompetence # quality may be displayed
		# Learnable features
		if features:
			Learner.Learner.__init__(self, features, MemorySpan=self.Param('MemorySpan'), AgeMax=self.Param('AgeMax'), 
							Infancy=self.Param('Infancy'), Imitation=self.Param('ImitationStrength'), 
							Speed=self.Param('LearningSpeed'), JumpProbability=self.Param('JumpProbability', 0),
							Conservatism=self.Param('LearningConservatism'), 
							LearningSimilarity=self.Param('LearningSimilarity'), 
							toric=self.Param('Toric'), Start=self.Param('LearningStart', default=-1))
		self.update()

	def Reset(self, Newborn=True):	
		"""	called by Learner at initialization and when born again
			Resets social links and learning experience
		"""
		Learner.Learner.Reset(self, Newborn=Newborn)	# sets Age to 0
		self.reinit(Newborn=Newborn)
		self.update()
		
	def reinit(self, Newborn=False):	
		"""	called at the beginning of each year 
			sets Points to zero and possibly erases social links (based on parameter 'EraseNetwork')
		"""
		# self.lessening_friendship()	# eroding past gurus performances
		if Newborn or self.Param('EraseNetwork', default=False):	self.forgetAll()
		self.Points = self.Param('InitialPoints', default=0)	# stores current performance

	def update(self, infancy=True):
		""" updates values for display
		"""
		# self.Colour = 'green%d' % int(1 + 10 * (1 - float(self.Age)/(1+self.Param('AgeMax'))))
		self.Colour = Shade(self.Age, BaseColour='green', Max=self.Param('AgeMax')+1, darkToLight=False)
		if infancy and not self.adult():	self.Colour = 'pink'
		y = self.feature()	# retrieves first feature's value
		self.Location = (self.Competence, y if y is not None else 17, self.Colour, self.DotSize)

	def interact(self, Partner):	
		"""	to be overloaded
		"""
		pass	
		return True

	def assessment(self):
		"""	Social benefit from having friends - called by Learning
			(to be overloaded)
		"""
		pass		
		
	def __str__(self):
		return f"{self.ID}[{self.Features}]"

	def __repr__(self):
		return self.ID
	
	# __repr__ = __str__
		
class Social_Population:
	"""	defines a population of interacting agents 
	"""
	def __init__(self, parameters, NbAgents, Observer, IndividualClass=None, features=[]):
		"""	creates a population of social individuals
		"""
		if IndividualClass is None:	IndividualClass = Social_Individual
		self.Features = features
		FeatureNames = [F.Name for F in self.Features]
		self.PopSize = NbAgents
		self.Obs = Observer
		self.Pop = [IndividualClass(IdNb, maxCompetence=NbAgents, features=FeatureNames, 
					parameters=parameters) for IdNb in range(NbAgents)]
		self.Param = parameters.Param
		self.NbGroup = parameters.Parameter('NumberOfGroups', Default=1)	# number of groups
				 
	def positions(self):	
		"""	returns the list of agents' locations
		"""
		return [(A.ID, A.Location) for A in self]

	def neighbours(self, Agent):
		"""	Returns agents of neighbouring qualitied 
		"""
		AgentCompetenceRank = self.Pop.index(Agent)
		return [self.Pop[NBhood] for NBhood in [AgentCompetenceRank - 1, AgentCompetenceRank + 1]
				if NBhood >= 0 and NBhood < self.PopSize]
		  
	def FeatureAvg(self, Feature):
		"""	average value of Feature's value
		"""
		Avg = sum([I.feature(Feature.Name) for I in self])
		return Avg / len(self) if self.Pop else Avg
	
	def FriendDistance(self):	
		"""	average distance between friends
		"""
		FD = []
		for I in self:	
			BF = I.best_friend()
			if BF:	FD.append(abs(I.Competence - BF.Competence))
		if FD:	return sum(FD) / len(FD)
		return 0
		
	def display(self):
		"""	Updates agents positions and social links for display.
			Updates average feature values for curves
		"""
		if self.Obs.Visible():	# Statistics for display
			for agent in self:
				agent.update(infancy=self.Obs.hot_phase())	# update Location for display
				# self.Obs.Positions[agent.ID] = agent.Location	# Observer stores agent location 
			# ------ Observer stores social links
			self.Obs.Alliances = [(agent.ID, [T.ID for T in agent.social_signature()]) for agent in self]
			self.Obs.record(self.positions(), Window='Field')
			self.display_curves()
			
	def display_curves(self):
		if self.Param('AvgFriendDistance', default=False):	self.Obs.curve('FriendDistance', self.FriendDistance())
		# Colours = ['brown', 'blue', 'red', 'green', 'white']
		# for F in sorted(list(self.Features.keys())):
		for F in self.Features:
			self.display_feature(F)
	
	def display_feature(self, F):
		self.Obs.curve(F.Name, self.FeatureAvg(F), 
				Color=F.Color, 
				Thickness = F.Thickness,
				Legend=f'Avg of {F.Legend}')

	def season_initialization(self):
		"""	tells agents to reinitialize each year
		"""
		for agent in self:	agent.reinit()
	
	'''
	def systematic_encounters(self, group=None, shuffle=True, NbInteractions=1):
		"""	organizing systematic encounters - 
			Kept for compatibility
		"""
		return self.encounters(group, NbInteractions=NbInteractions, systematic=True, shuffle=shuffle)
	'''
	
	def encounters(self, group=None, NbInteractions=None, shuffle=True):
		"""	NbInteractions is the number of encounters per individual (on average if non systematic)
		"""
		if group is None: group = self.Pop

		if NbInteractions is None:
			NbInteractions = self.Param('NbInteractions', default=1)
		systematic = (type(NbInteractions) == int)
		if not systematic:
			assert type(NbInteractions) == float
			NbInteractions = int(NbInteractions * len(group))
		
		if systematic:
			# Pairs = list(it.product(group, repeat=2))	# cartesian product group x group
			ShuffledGroup = random.sample(group, len(group)) if shuffle else group
			for Player in group:
				for Partner in ShuffledGroup:
					if Player != Partner:	yield Player, Partner
			# ====== warning: Python does not like to mix iter() with yield, so do not return iter(Pairs)
			# if shuffle:	random.shuffle(Pairs)
			# for _ in range(NbInteractions):
				# for Player, Partner in Pairs:
					# if Player != Partner:	yield Player, Partner
		else:
			assert shuffle, "Random encounters implements shuffling"
			# ====== randomly picking interacting pairs
			for _ in range(NbInteractions):
				yield random.sample(group, 2)
		
	def interactions(self, group=None, shuffle=True):
		"""	interactions occur within a group 
		"""
		for Player, Partner in self.encounters(group, shuffle=shuffle):
			Player.interact(Partner)
			# global I
			# try:	I += 1
			# except NameError:	I = 0
			# print(I)
		# print(f'/{self.Obs.StepId}')
	
	def learning(self):
		"""	called at each 'run', several times per year 
		"""
		for agent in self:
			agent.assessment()	# storing current scores (with possible cross-benefits)
		for agent in self:	# now cross-benefits are completed
			agent.wins(agent.Points)	# Stores points for learning
		# ------ some agents learn
		Learners = random.sample(self.Pop, Tools.chances(self.Param('LearningProbability')/100.0, len(self.Pop)))	
		for agent in Learners:
			agent.Learns(self.neighbours(agent), hot=self.Obs.hot_phase())
			# agent.update()	# update location for display
				
	def One_Run(self):
		"""	This procedure is repeatedly called by the simulation thread.
			It increments the year through season().
			Then for each run (there are NbRunPerYear runs each year),
			interactions take place within groups
		"""
		# ====================
		# Display
		# ====================
		self.Obs.season()	# increments year
		# ====================
		# Interactions
		# ====================
		for Run in range(self.Param('NbRunPerYear')):	
			# if self.Obs.Visible(): print('-------------', self.Obs.StepId)
			self.season_initialization()	# calls reinit
				
			# ------ interactions within groups
			GroupLength = max(1, len(self.Pop) // self.NbGroup)
			if self.NbGroup > 1:
				Pop = self.Pop[:] 
				random.shuffle(Pop)
			else:	Pop = self.Pop
			for groupID in range(self.NbGroup):	# interaction only within groups
				group = Pop[groupID * GroupLength: (groupID + 1) * GroupLength]
				self.interactions(group)

			# ------ learning
			if self.Features:	self.learning()

		self.display()
		return True	# This value is forwarded to "ReturnFromThread"

	def Dump(self, Slot):
		pass
		
	def close(self, Verbose=True):
		pass
		
	def __len__(self):	return len(self.Pop)
		
	def __iter__(self):	return iter(self.Pop)
	
	def __str__(self):
		return '\n'.join([str(A) for n, A in enumerate(self) if n < 20]) + '\n' * 2
		

		
def Start(Params=None, PopClass=Social_Population, ObsClass=Social_Observer, DumpFeatures=None, Windows='FNC'):
	"""	Launches the simulation
	"""
	if Params is None:	Params = Global()
	if Params.get('RandomSeed', 0) > 0:	random.seed(Params['RandomSeed'])
	Observer_ = ObsClass(Params)   # Observer contains statistics
	Observer_.setOutputDir('___Results')
	Views = Observer_.getInfo('DefaultViews', default=[])
	if Views == [] and 'Views' in Params: 
		# retrieving views from configuration
		Views = Params['Views']
		if type(Views) == str:
			Views = Views.split('+')
	ViewsNames = list(map(lambda W: W[0].strip('*') if type(W) is tuple else W.strip('*'), Views))
	Windows = set(Windows)
	for V in ViewsNames:	Windows.add(V[0])
	Windows = ''.join(Windows)
	if 'Field' not in ViewsNames and 'F' in Windows:	Views.append(('Field', 770, 70, 520, 370))
	if 'Network' not in ViewsNames and 'N' in Windows:	Views.append(('Network', 530, 200))
	if 'Trajectories' not in ViewsNames and 'T' in Windows:	Views.append(('Trajectories', 500, 350))
	Observer_.recordInfo('DefaultViews', Views)	# Evolife should start with that window open
	# Observer.record((100, 100, 0, 0), Window='Field')	# to resize the field
	Pop = PopClass(Params, Params['NbAgents'], Observer_)   # population of agents
	# if DumpFeatures is None:	DumpFeatures = list(Pop.Features.keys()) + ['DistanceToBestFriend']
	Observer_.recordInfo('DumpFeatures', DumpFeatures)
	BatchMode = Params['BatchMode']
	
	if BatchMode:
		from Evolife.Graphics import Evolife_Batch
		##########	##########
		# Batch mode
		####################
		# # # # for Step in range(Gbl['TimeLimit']):
			# # # # #print '.',
			# # # # Pop.One_Run()
			# # # # if os.path.exists('stop'):	break
		Evolife_Batch.Start(Pop.One_Run, Observer_)
	else:
		from Evolife.Graphics import Evolife_Window
		####################
		# Interactive mode
		####################
		"""	launching window 
		"""
		try:
			Evolife_Window.Start(Pop.One_Run, Observer_, Capabilities=Windows+'P', 
					 Options={'Background':Params.get('Background', 'lightblue'), 'Run':Params.get('Run', False)})
		except Exception as Msg:
			from sys import excepthook, exc_info
			excepthook(exc_info()[0],exc_info()[1],exc_info()[2])
			input('[Entree]')
		
	if DUMPSTATE:
		# saving population state
		Params.Dump_(Pop.Dump, Observer_.getInfo('ResultFile'), Observer_.getInfo('DumpFeatures'), 
						Observer_.getInfo('ExperienceID'), Verbose = not BatchMode)
	
	Pop.close(Verbose= not BatchMode)	# possible final actions

	if not BatchMode:	
		print("Bye.......")
		# input(['Enter'])	# no effect, but make people believe it has
		sleep(0.5)
	return
	


if __name__ == "__main__":
	Gbl = Global()
	if Gbl['RandomSeed'] > 0:	random.seed(Gbl['RandomSeed'])
	Start(Gbl)



__author__ = 'Dessalles'
