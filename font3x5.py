# This 3x5 font wasn't present on the original code.
# Based on this font: https://robey.lag.net/2010/01/23/tiny-monospace-font.html
# Changed some chars as I thought it was better, you should do the same!
# Maybe, for code cleansing, I will move this into a file, and the user must loadFont3x5.
font3x5 = [									# KEY	| ASCII(dec)
[[0,0,0,0,0], [0,0,0,0,0], [0,0,0,0,0]],	# SPACE	32
[[0,0,0,0,0], [1,1,1,0,1], [0,0,0,0,0]],	# !			33
[[1,1,0,0,0], [0,0,0,0,0], [1,1,0,0,0]],	# "			34
[[1,1,1,1,1], [0,1,0,1,0], [1,1,1,1,1]],	# #			35
[[0,1,0,1,0], [1,1,1,1,1], [1,0,1,0,0]],	# $			36
[[1,0,0,1,0], [0,0,1,0,0], [0,1,0,0,1]],	# %			37
[[1,1,1,1,0], [1,1,1,0,1], [0,0,1,1,1]],	# &			38
[[1,1,0,0,0], [0,0,0,0,0], [0,0,0,0,0]],	# '			39
[[0,1,1,1,0], [1,0,0,0,1], [0,0,0,0,0]],	# (			40
[[0,0,0,0,0], [1,0,0,0,1], [0,1,1,1,0]],	# )			41
[[1,0,1,0,0], [0,1,0,0,0], [1,0,1,0,0]],	# *			42
[[0,0,1,0,0], [0,1,1,1,0], [0,0,1,0,0]],	# +			43
[[0,0,0,0,1], [0,0,0,1,0], [0,0,0,0,0]],	# ,			44
[[0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]],	# -			45
[[0,0,0,0,1], [0,0,0,0,0], [0,0,0,0,0]],	# .			46
[[0,0,0,1,1], [0,0,1,0,0], [1,1,0,0,0]],	# /			47
[[1,1,1,1,1], [1,0,0,0,1], [1,1,1,1,1]],	# 0			48
[[1,0,0,0,1], [1,1,1,1,1], [0,0,0,0,1]],	# 1			49
[[1,0,1,1,1], [1,0,1,0,1], [1,1,1,0,1]],	# 2			50
[[1,0,1,0,1], [1,0,1,0,1], [1,1,1,1,1]],	# 3			51
[[1,1,1,0,0], [0,0,1,0,0], [1,1,1,1,1]],	# 4			52
[[1,1,1,0,1], [1,0,1,0,1], [1,0,1,1,1]],	# 5			53
[[1,1,1,1,1], [1,0,1,0,1], [1,0,1,1,1]],	# 6			54
[[1,0,0,0,0], [1,0,0,1,1], [1,1,1,0,0]],	# 7			55
[[1,1,1,1,1], [1,0,1,0,1], [1,1,1,1,1]],	# 8			56
[[1,1,1,0,1], [1,0,1,0,1], [1,1,1,1,1]],	# 9			57
[[0,1,0,1,0], [0,0,0,0,0], [0,0,0,0,0]],	# :			58
[[0,0,0,0,1], [0,1,0,1,0], [0,0,0,0,0]],	# ;			59
[[0,0,1,0,0], [0,1,0,1,0], [1,0,0,0,1]],	# <			60
[[0,1,0,1,0], [0,1,0,1,0], [0,1,0,1,0]],	# =			61
[[1,0,0,0,1], [0,1,0,1,0], [1,1,1,1,1]],	# >			62
[[1,0,0,0,0], [1,0,1,0,1], [1,1,0,0,0]],	# ?			63
[[0,1,1,1,0], [1,0,1,0,1], [0,1,1,0,1]],	# @			64
[[1,1,1,1,1], [1,0,1,0,0], [1,1,1,1,1]],	# A			65
[[1,1,1,1,1], [1,0,1,0,1], [0,1,0,1,0]],	# B			66
[[0,1,1,1,0], [1,0,0,0,1], [1,0,0,0,1]],	# C			67
[[1,1,1,1,1], [1,0,0,0,1], [0,1,1,1,0]],	# D			68
[[1,1,1,1,1], [1,0,1,0,1], [1,0,1,0,1]],	# E			69
[[1,1,1,1,1], [1,0,1,0,0], [1,0,1,0,0]],	# F			70
[[0,1,1,1,0], [1,0,1,0,1], [1,0,1,1,1]],	# G			71
[[1,1,1,1,1], [0,0,1,0,0], [1,1,1,1,1]],	# H			72
[[1,0,0,0,1], [1,1,1,1,1], [1,0,0,0,1]],	# I			73
[[0,0,0,1,0], [0,0,0,0,1], [1,1,1,1,0]],	# J			74
[[1,1,1,1,1], [0,0,1,0,0], [1,1,0,1,1]],	# K			75
[[1,1,1,1,1], [0,0,0,0,1], [0,0,0,0,1]],	# L			76
[[1,1,1,1,1], [0,1,1,0,0], [1,1,1,1,1]],	# M			77
[[1,1,1,1,1], [0,1,1,1,0], [1,1,1,1,1]],	# N			78
[[0,1,1,1,0], [1,0,0,0,1], [0,1,1,1,0]],	# O			79
[[1,1,1,1,1], [1,0,1,0,0], [0,1,0,0,0]],	# P			80
[[0,1,1,1,0], [1,0,0,1,1], [0,1,1,1,1]],	# Q			81
[[1,1,1,1,1], [1,0,1,0,0], [0,1,0,1,1]],	# R			82
[[0,1,0,0,1], [1,0,1,0,1], [1,0,0,1,0]],	# S			83
[[1,0,0,0,0], [1,1,1,1,1], [1,0,0,0,0]],	# T			84
[[1,1,1,1,1], [0,0,0,0,1], [1,1,1,1,1]],	# U			85
[[1,1,1,1,0], [0,0,0,0,1], [1,1,1,1,0]],	# V			86
[[1,1,1,1,1], [0,0,1,1,0], [1,1,1,1,1]],	# W			87
[[1,1,0,1,1], [0,0,1,0,0], [1,1,0,1,1]],	# X			88
[[1,1,0,0,0], [0,0,1,1,1], [1,1,0,0,0]],	# Y			89
[[1,0,0,1,1], [1,0,1,0,1], [1,1,0,0,1]],	# Z			90
[[1,1,1,1,1], [1,0,0,0,1], [0,0,0,0,0]],	# [			91
[[1,1,0,0,0], [0,0,1,0,0], [0,0,0,1,1]],	# \			92
[[1,0,0,0,1], [1,1,1,1,1], [0,0,0,0,0]],	# ]			93
[[0,1,0,0,0], [1,0,0,0,0], [0,1,0,0,0]],	# ^			94
[[0,0,0,0,1], [0,0,0,0,1], [0,0,0,0,1]],	# _			95
[[1,1,0,0,0], [0,0,0,0,0], [0,0,0,0,0]],	# '			96
[[0,1,0,1,1], [0,1,1,0,1], [0,0,1,1,1]],	# a			97
[[1,1,1,1,1], [0,1,0,0,1], [0,0,1,1,0]],	# b			98
[[0,0,1,1,0], [0,1,0,0,1], [0,1,0,0,1]],	# c			99
[[0,0,1,1,0], [0,1,0,0,1], [1,1,1,1,1]],	# d			100
[[0,0,1,1,0], [0,1,0,1,1], [0,1,1,0,1]],	# e			101
[[0,0,1,0,0], [0,1,1,1,1], [1,0,1,0,0]],	# f			102
[[0,1,1,0,0], [1,0,1,0,1], [1,1,1,1,0]],	# g			103
[[1,1,1,1,1], [0,1,0,0,0], [0,0,1,1,1]],	# h			104
[[1,0,1,1,1], [0,0,0,0,0], [0,0,0,0,0]],	# i			105
[[0,0,0,1,0], [0,0,0,0,1], [1,0,1,1,1]],	# j			106
[[1,1,1,1,1], [0,0,1,1,0], [0,1,0,0,1]],	# k			107
[[1,0,0,0,1], [1,1,1,1,1], [0,0,0,0,1]],	# l			108
[[0,1,1,1,1], [0,1,1,1,0], [0,1,1,1,1]],	# m			109
[[0,1,1,1,1], [0,1,0,0,0], [0,1,1,1,1]],	# n			110
[[0,0,1,1,0], [0,1,0,0,1], [0,0,1,1,0]],	# o			111
[[0,1,1,1,1], [0,1,0,1,0], [0,0,1,0,0]],	# p			112
[[0,0,1,0,0], [0,1,0,1,0], [0,1,1,1,1]],	# q			113
[[0,0,1,1,1], [0,1,0,0,0], [0,1,1,0,0]],	# r			114
[[0,0,1,0,1], [0,1,1,1,1], [0,1,0,1,0]],	# s			115
[[0,1,0,0,0], [1,1,1,1,1], [0,1,0,0,1]],	# t			116
[[0,1,1,1,1], [0,0,0,0,1], [0,1,1,1,1]],	# u			117
[[0,1,1,1,0], [0,0,0,0,1], [0,1,1,1,0]],	# v			118
[[0,1,1,1,1], [0,0,1,1,1], [0,1,1,1,1]],	# w			119
[[0,1,0,0,1], [0,0,1,1,0], [0,1,0,0,1]],	# x			120
[[0,1,1,0,1], [0,0,0,1,1], [0,1,1,1,0]],	# y			121
[[0,1,0,1,1], [0,1,1,1,1], [0,1,1,0,1]],	# z			122
[[0,0,1,0,0], [1,1,0,1,1], [1,0,0,0,1]],	# {			123
[[1,1,1,1,1], [0,0,0,0,0], [0,0,0,0,0]],	# |			124
[[1,0,0,0,1], [1,1,0,1,1], [0,0,1,0,0]],	# ]			125
[[0,0,1,0,0], [0,1,1,0,0], [0,1,0,0,0]],	# ~			126
[[1,0,1,0,1], [0,1,0,1,0], [1,0,1,0,1]]]	# ERROR		"127" = If the ascii is out of range,
# will print this custom char instead. 


