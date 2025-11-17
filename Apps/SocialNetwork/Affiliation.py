#!/usr/bin/env python3
""" @brief  Study of the role of signalling in the emergence of social networks:
Individuals signal their competence to attract followers
"""


#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2025-11-16                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes/annotated.html     #
#============================================================================#



from time import sleep
from random import sample, choice

import sys
sys.path.append('../../..')

from Evolife.Social import SocialSimulation
from Evolife.Social import Alliances
from Evolife.Ecology import Learner

		
class Observer(SocialSimulation.Social_Observer):
	def Field_grid(self):
		"""	initial draw: here a green square 
		"""
		return [(0, 0, 'red', 1, 100, 100, 'red', 1), (100, 100, 1, 0)]
	
class Individual(Alliances.Follower, Learner.Learner):
	"""	A social individual has friends and can learn 
	"""
	def __init__(self, IdNb, maxCompetence=100, features={}, parameters=None):
		if parameters is None:	parameters = Gbl
		self.Param = parameters.Param
		self.SignalLevel = 0
		self.BestSignal = 0	# best signal value in memory
		self.ID = "A%d" % IdNb	# Identity number
		Alliances.Follower.__init__(self, self.Param('MaxFriends'), self.Param('MaxFollowers'))
		self.Competence = (100.0 * IdNb) / maxCompetence # competence may be displayed
		# Learnable features
		Learner.Learner.__init__(self, features, MemorySpan=self.Param('MemorySpan'), AgeMax=self.Param('AgeMax'), 
							Infancy=self.Param('Infancy'), Imitation=self.Param('ImitationStrength'), 
							Speed=self.Param('LearningSpeed'), Conservatism=self.Param('LearningConservatism'), toric=self.Param('Toric'))
		self.Points = 0	# stores current performance
		self.update()

	def Reset(self, Newborn=True):
		self.detach()	# erase friendships
		Learner.Learner.Reset(self, Newborn=Newborn)
		self.Points = 0
		# self.update()
		
	def update(self, infancy=True):
		"""	updates values for display 
		"""
		Colour = 'brown'
		if infancy and not self.adult():	Colour = 'pink'
		self.SignalLevel = self.signal()
		BR = self.bestRecord()
		if BR:	self.BestSignal = BR[0]['SignalInvestment'] * self.Competence / 100.0
		else:	self.BestSignal = 0
		# self.Location = (self.Competence, self.Features['SignalInvestment'], Colour, 8)
		self.Location = (self.Competence, self.BestSignal+1, Colour, -1)	# -1 == negative size --> logical size instead of pixel
		if Gbl.Param('Links') and self.best():
			self.Location += (self.best().Competence, self.best().BestSignal+1, 21, 1)

	def signal(self, Transparent=False):
		"""	returns the actual competence of an individual or its displayed version 
		"""
		if Transparent:	return self.Competence
		BC = Gbl.Param('BottomCompetence')
		Comp = (100.0-BC) * self.Competence/100.0 + BC
		# Comp = BC + self.Competence
		VisibleCompetence = Comp * self.Features['SignalInvestment'] / 100.0
		return self.Limitate(VisibleCompetence, 0, 100)

	def interact(self, Signallers):
		if Signallers == []:	return
		# The agent chooses the best available Signaller from a sample.
		OldFriend = self.best()
		Signallers.sort(key=lambda S: S.SignalLevel, reverse=True)
		for Signaller in Signallers:
			if Signaller == self:	continue
			if OldFriend and OldFriend.SignalLevel >= Signaller.SignalLevel:
				break	# no available interesting signaller
			if Signaller.followers.accepts(0) >= 0:
				# cool! Self accepted as fan by Signaller.
				if OldFriend is not None and OldFriend != Signaller:
					self.G_quit_(OldFriend)
				self.F_follow(0, Signaller, Signaller.SignalLevel)
				break

	def assessment(self):
		"""	Social benefit from having friends 
		"""
		self.Points -= Gbl.Param('SignallingCost') * self.Features['SignalInvestment'] / 100.0
		if self.best() is not None:
			self.best().Points += Gbl.Param('JoiningBonus')

	def __str__(self):
		return f"{self.ID}[{self.SignalLevel:0.1f}]"
		
class Population(SocialSimulation.Social_Population):
	"""	defines the population of agents 
	"""
	def __init__(self, parameters, NbAgents, Observer):
		"""	creates a population of agents 
		"""
		Features = [SocialSimulation.Feature('SignalInvestment', Color='blue', Thickness=3)]   # propensity to be moral oneself
		SocialSimulation.Social_Population.__init__(self, parameters, NbAgents, Observer, 
			IndividualClass=Individual, features=Features)
		

	def season_initialization(self):
		for agent in self.Pop:
			if self.Param('EraseNetwork'):	agent.detach()
			agent.Points = 0
		
	def interactions(self, group=None):
		if group is None: group = self.Pop
		for Run in range(int(Gbl.Param('NbInteractions'))):
			Fan = choice(self.Pop)
			# Fan chooses from a sample
			Fan.interact(sample(self.Pop, Gbl.Param('SampleSize')))

			
	def Dump(self, Slot):
		""" Saving investment in signalling for each adult agent
			and then distance to best friend for each adult agent having a best friend
		"""
		if Slot == 'SignalInvestment':
			#D = [(agent.Competence, "%2.03f" % agent.Features['SignalInvestment']) for agent in self.Pop if agent.adult()]
			#D += [(agent.Competence, " ") for agent in self.Pop if not agent.adult()]
			D = [(agent.Competence, "%2.03f" % agent.Features['SignalInvestment']) for agent in self.Pop]
		if Slot == 'DistanceToBestFriend':
			D = [(agent.Competence, "%d" % abs(agent.best().Competence - agent.Competence)) for agent in self.Pop if agent.adult() and agent.best() is not None]
			D += [(agent.Competence, " ") for agent in self.Pop if agent.best() == None or not agent.adult()]
		return [Slot] + [d[1] for d in sorted(D, key=lambda x: x[0])]
		

		
if __name__ == "__main__":
	Gbl = SocialSimulation.Global()
	SocialSimulation.Start(Params=Gbl, PopClass=Population, ObsClass=Observer)



__author__ = 'Dessalles'
