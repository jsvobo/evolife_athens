#!/usr/bin/env python3
""" @brief  This module implements a Gray code, using a function
	borrowed from https://stackoverflow.com/questions/72027920/python-graycode-saved-as-string-directly-to-decimal
	
	usage:
	G = GrayCode()
	G.Gray2Int(17) = 25
	If you want to visualize the table:
	G = GrayCode(5)
	print G
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
#  Implements a Gray code                                                    #
#  Note: according to Wikipedia, the French engineer Emile Baudot used 'Gray #
#  codes' in telegraphy long before they were 'invented', in 1878.           #
#  http://en.wikipedia.org/wiki/Gray_code                                    #
##############################################################################

import math

class GrayCode(object):

	def __init__(self, Length=8):	
		self.GrayTable = dict()
		self.Length = Length

	def InitGrayTable(self):
		# print "Initializing a %d-bit long Gray Table" % Length
		assert self.Length <= 16, "Gros-Gray code implementation limited to 16 bits"
		for ii in range(2 << (self.Length-1)):
			# self.GrayTable[ii] = self.Int2Gray(ii)
			self.GrayTable[self.Int2Gray(ii)] = ii
 
	def Int2Gray(self, i):
		"""
		This function returns the i'th Gray Code.
		It is recursive and operates in O(log n) time.
		This function is borrowed from https://stackoverflow.com/questions/72027920/python-graycode-saved-as-string-directly-to-decimal
		"""
		return i ^ (i >> 1)

	def Gray2Int(self, GrayIndex):
		"""	converts a coded integer into a decoded integer by using a Gray code
		"""
		try:
			return self.GrayTable[GrayIndex]
		except (NameError, KeyError):
			self.Length = max(self.Length, int(math.log2(1+GrayIndex))+1)
			self.InitGrayTable()
			return self.GrayTable[GrayIndex]
			
	def PaddedGray(self, i):
		" return a padded binary string for i "
		S = '0' * self.Length + bin(i)[2:]
		return S[-self.Length:]
   
	def __str__(self):
		return '\n'.join([self.PaddedGray(self.GrayTable[ii]) for ii in self.GrayTable])

if __name__ == "__main__":
		GrayTable = GrayCode(8)
		# for I in [17, 240, 1276]:
		print('********* Gray table **********')
		for I in list(range(44)) + list(range(250, 256)):
			GI = GrayTable.Int2Gray(I)
			print(f'{I}: {bin(GI)[2:]} --> {GrayTable.Gray2Int(GI)}')

		print()
		print()
		BI = '110100011'
		# for I in GrayTable.GrayTable:
			# if bin(GrayTable.GrayTable[I])[2:] == BI:
				# print(I)
				# break
		I = int(BI, 2)	# decimal interpretation
		GI = GrayTable.Gray2Int(I)	# Gray interpretation
		print(f'{BI}: {GI}\n{bin(GrayTable.Int2Gray(GI))[2:]}')
		# print(GrayTable.GrayTable)

__author__ = 'Dessalles'
