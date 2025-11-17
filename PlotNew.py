#!/usr/bin/env python3
""" @brief  Draw curves offline.
	Takes a csv file as input and draws curves.
	Creates image file.
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
# Draw curves offline using matplotlib                                       #
##############################################################################

import sys
import os
import re
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')	# to use offline
import matplotlib.pyplot as plt



DPI = 300	# definition of saved images
LEGENDPOSITION = 'lower right'
LEGENDPOSITION = 'lower left'
LEGENDPOSITION = 'best'
LEGENDPOSITION = 'right'
LEGENDPOSITION = (0.3, 0.3)		# friends only 
LEGENDPOSITION = (0.1, 0.3) 	# no friends
LEGENDPOSITION = 'upper left'	# club friends
LEGENDPOSITION = 'upper right'

FONTSIZE = 20
FONTSIZEMin = FONTSIZE - 6
# COLOURS = ['#000000', '#00BF00', '#78FF78', '#BF0000', '#FF7878', '#0000BF', '#7878FF']
# COLOURS = ['#00BF00', '#78FF78', '#BF0000', '#FF7878', '#0000BF', '#7878FF']
COLOURS = ['#BF7000', '#0000BF', '#78FF78', '#FF7878', '#0000BF', '#7878FF', '#F54374', '#54F254', '#2383F3'] + ['black'] * 10
COLOURS = ['#FF7878', '#0000BF', '#7878FF', 'darkgreen', '#55FF55-', '#99FF99-', '#F54374', '#54F254', '#2383F3'] + ['black'] * 14
COLOURS = ['red', '#FFBBBB-', '#FFAAAA-', 'darkgreen', '#55FF55-', '#99FF99-', '#F54374', '#54F254', '#2383F3'] + ['black'] * 14
THICKNESS = [2,2,2,] + [0] * 14			# friends only 
THICKNESS = [0,0,0,2,2,2,] + [0] * 14
THICKNESS = [2,2,2,2,2,2,] + [0] * 14

'MemberAverageCapital'
'MemberMinCapital'
'MemberMaxCapital'
'NonMemberAverageCapital'
'NonMemberMinCapital'
'NonMemberMaxCapital'
'RelativeClubSize'
'AverageVisibility'
'NewMembers'
'QuittingMembers'
'MemberSatisfiedChallenges'
'MemberAveragePositiveChallenge'
'MemberAverageNegativeChallenge'
'NonMemberSatisfiedChallenges'
'NonMemberAveragePositiveChallenge'
'NonMemberAverageNegativeChallenge'


import logging	# for tracing
# modifying print priority of console handler
logging.basicConfig(level='WARNING')

SHOW = False
FIELDLINE = 2	# typically: 2 for feature1; 3 for feature2 -- Used to average field dot clouds

# Importing Evolife
EVOLIFE = False
CurDir = os.getcwd()
while len(CurDir) > 7:
	CurDir = os.path.dirname(CurDir)
	if 'Evolife' in os.listdir(CurDir):
		sys.path.append(CurDir)
		try:	
			import Evolife.Scenarii.Parameters as EP
			EVOLIFE = True
			print(f'Evolife found in {CurDir}')
		except ImportError:	continue


try:	import TableCsv as CSV
except ImportError:	import Evolife.Tools.TableCsv as CSV


def figsave(FileName):
	if os.path.exists(FileName):	os.remove(FileName)
	plt.savefig(FileName, dpi=DPI)
	print("%s created" % FileName)

def str2nb(x):	
	try: return int(x)
	except ValueError:	
		try:
			return float(x)
		except:
			return None
	
	
	
class Plot:
	def __init__(self, ExpeFile, ConstantConfigFileName=None, Parameter=None):	
		self.ExpeFile = os.path.splitext(ExpeFile)[0]
		self.ExpeName = self.ExpeFile
		if self.ExpeFile[-4:] in ['_res', '_avg', '_dmp']:
			self.ExpeName = self.ExpeFile[:-4]
		self.OutputFile = self.ExpeFile + '.png'
		self.PlotFile = self.ExpeFile + '.csv'
		self.Parameter = Parameter
		if EVOLIFE:
			ConfigFileName = self.ExpeName + '_res.csv'
			self.Cfg = self.RetrieveConfig(ConfigFileName)	# retrieve actual parameters from _res file
			self.RelevantParam = self.RelevantConfig(self.ExpeName, ConstantConfigFileName, Parameter=Parameter)	# display parameters 
		else:	self.RelevantParam = None
			
	def Process(self, FieldDraw='CurveField'):
		"""	draw curve and field
		"""
		if os.path.exists(self.OutputFile) \
				and (os.stat(self.PlotFile).st_mtime < os.stat(self.OutputFile).st_mtime) \
				and self.Parameter is None:
			print(f'{self.OutputFile} already exists')
			return
		# drawing curves
		plt.clf()
		plt.figure(1, figsize=(6 + 6 * (FieldDraw == 'CurveField'), 4))
		if FieldDraw == 'CurveField':	plt.subplot(1,2,1)
		if FieldDraw != 'Field':	
			ymax = self.Draw_Curve(plt)
			# self.title(plt)
		if FieldDraw != 'Curve':
			# drawing field
			if FieldDraw != 'Field':	plt.subplot(1,2,2)
			# self.Draw_Field(ymax=ymax)
			self.Draw_Field(plt, ymax=100)
			# if SHOW:	plt.show(, )
			self.title(plt, first=(FieldDraw == 'Field'))
		self.save(self.OutputFile)
		
	def Draw_Curve(self, plt):
		# Retrieving coordinates
		PlotOrders = CSV.load(self.PlotFile, sniff=True)	# loading csv file
		# Retrieving legend
		try:	Legend = next(PlotOrders)		# reading first line with curve names
		except StopIteration:	sys.exit(0)
		# Retrieving data
		Columns = list(zip(*PlotOrders))
		Columns = list(map(lambda L: [C for C in map(str2nb, L)], Columns))
		print(Legend)
		# Columns = list(map(lambda L: list(map(str2nb, L)), [*PlotOrders]))
		for Col in range(1,len(Columns)):
			if THICKNESS[Col-1] == 0:	continue
			Colour = COLOURS[Col-1]
			fmt = '--' if Colour.endswith('-') else '-'
			plt.plot(Columns[0], Columns[Col], fmt, linewidth=THICKNESS[Col-1], 
					color=Colour.strip('-'), label=Legend[Col].replace('_', ' '))	
		x1,x2,y1,y2 = plt.axis()
		plt.axis((x1, x2, 0, y2+0.05))
		plt.ylim(top=45000)
		# plt.ylim(top=1580)
		# plt.ylim(bottom=-5040)
		plt.ylim(bottom=-1580)
		plt.xlabel('year', fontsize=FONTSIZE)
		plt.xticks(fontsize=FONTSIZEMin) 
		plt.yticks(fontsize=FONTSIZEMin) 
		# plt.ylabel('wealth')
		# plt.ylabel('price or sales')
		# plt.legend(bbox_to_anchor=(0.1, 1))
		# plt.legend(loc=LEGENDPOSITION, fontsize=FONTSIZEMin)
		plt.tight_layout()
		return plt.ylim()[1]	# max coordinate

	def title(self, plt, first=True):
		if self.RelevantParam and first:	
			plt.title('   '.join(sorted(['%s = %s' % (P, self.RelevantParam[P]) for P in self.RelevantParam])), fontsize=6)
		else:	plt.title(self.ExpeFile, fontsize=8)
	
		
	@classmethod
	def RetrieveConfig(self, ConfigFile):
		" Retrieves parameters from _res file "
		if os.path.exists(ConfigFile):
			CfgLines = open(ConfigFile).readlines()
			# reading parameters
			Sep = max([';', '\t', ','], key=lambda x: CfgLines[0].count(x))
			if len(CfgLines) > 1:
				Parameters = dict(zip(*map(lambda x: x.strip().split(Sep), CfgLines[:2])))
				return EP.Parameters(ParamDict=Parameters)
		return None
		
	def RelevantConfig(self, ExpeName, ConstantParameterFile, Parameter=None):
		" Try to find relevant parameters "
		Irrelevant =  ['BatchMode', 'DisplayPeriod', 'TimeLimit', 'DumpStart', 'LearningStart']
		if self.Cfg is None or not ConstantParameterFile:	
			print('ConfigFile not found')
			return None
		RelevantParameters = {} if Parameter is None else {Parameter:self.Cfg[Parameter]}
		CP = EP.Parameters(ConstantParameterFile)
		# determining relevant parameters
		for p in CP:
			if p in Irrelevant:	continue
			if p in self.Cfg and CP[p] != self.Cfg[p]:
				# print(p, RelevantParameters[p], self.Cfg[p])
				RelevantParameters[p] = self.Cfg[p]
				# CP.addParameter(p, self.Cfg[p])
		RelevantParameters = EP.Parameters(ParamDict=RelevantParameters)
		print(f'Relevant Parameters: \n{RelevantParameters}')
		return RelevantParameters
		
	def Draw_Field(self, plt, ymax=None):
		if self.ExpeFile.endswith('_avg'):	
			AverageField = True
			FieldFile = self.ExpeFile + '.csv'
		else:	
			AverageField = False
			FieldFile = self.ExpeFile + '_dmp.csv'
		if not os.path.exists(FieldFile):	return None
		Lines = open(FieldFile).readlines()
		# reading recorded positions
		FieldPlot = None
		RelevantLine = FIELDLINE if AverageField else 1
		if len(Lines) > 1:
			FieldPlot = Lines[RelevantLine].strip().split(';')[1:]
			NbP = len(FieldPlot)
			plt.scatter(list(range(NbP)), list(map(float, FieldPlot)), s=11)
			# print(FieldPlot)
			if ymax is not None:
				plt.ylim(top=ymax)
			plt.xlabel('quality')
			# plt.ylabel('signal')
		return FieldPlot
		
	def save(self, OutputFile): figsave(OutputFile)

def Usage(cmd):
	print(f'''Usage:	{cmd} <curve file name> [<constant config file name>] [curve | field | curvefield]
Example: {cmd} ___Results\___Community_.csv Community.evo
	''')

def Parse(Args):
	Files = []
	ConstantConfigFileName = None
	if len(Args) < 2:
		# find last file
		CsvFiles = glob.glob('___Results/*.csv')
		for F in CsvFiles:
			if re.search('_(history|res|avg|dmp)', F):	
				# print(F, 'ignored')
				continue
			Files.append(F)
		if Files:
			Files.sort(key=lambda x: os.stat(x).st_mtime)
			Files = [Files[-1]]
		else:
			Usage(os.path.basename(Args[0]))
	elif len(Args) > 3:
		Usage(os.path.basename(Args[0]))
	else:
		Files = glob.glob(Args[1])
		ConstantConfigFileName = Args[2] if (len(Args) == 3) else None
	for Argfile in Files:
		yield (Argfile, ConstantConfigFileName)
	
if __name__ == "__main__":
	CurrentParameter = None
	Args = sys.argv
	Usage(Args[0])
	FieldDraw = 'CurveField'
	if re.match('curve|.*field', Args[-1], re.I):
		if Args[-1].lower().endswith('nofield'):
			# patch for ShowResult
			FieldDraw = 'Curve'
			if Args[-1].find('_') > 0:
				CurrentParameter = Args[-1].split('_')[0]
		elif Args[-1].lower() == 'field':	FieldDraw = 'Field'
		elif Args[-1].lower() == 'curve':	FieldDraw = 'Curve'
		Args.pop(-1)
	for (Argfile, ConstantConfigFileName) in Parse(Args):
		if Argfile:
			print(Argfile)
			plot = Plot(Argfile, Parameter=CurrentParameter, ConstantConfigFileName=ConstantConfigFileName)
			plot.Process(FieldDraw=FieldDraw)
			# print()
			

__author__ = 'Dessalles'
