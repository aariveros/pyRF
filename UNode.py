# from node import *
#import scipy.stats
import node
import numpy as np
import pandas as pd
from copy import deepcopy
import pyRF_prob


class UNode(node.Node):
	def __init__(self, data, level=1, max_depth=8, min_samples_split=10):

		node.Node.__init__(self, data, level, max_depth, min_samples_split)
		self.mass = int(self.data['weight'].sum())			

	def get_pivotes(self, feature, calidad = 'exact'):
		"""
		Retorna todos los valores segun los que se debe intentar cortar una feature
		"""
		name = feature.name.rstrip('.mean')
		bounds = self.data[name + '.l'].tolist() + self.data[name + '.r'].tolist()


		ret = list(set(bounds)) # Para eliminar valores repetidos
		ret.sort()	# Elimino los bordes, aunque talvez sea mejor poner un if mas adelante noma
		return ret[1:-1]

	# Busca el mejor corte posible para el nodo
	def split(self):

		# Inicializo la ganancia de info en el peor nivel posible
		max_gain = -float('inf')

		# Para cada feature (no considero la clase ni la completitud)
		filterfeatures = self.filterfeatures()

		print filterfeatures

		for f in filterfeatures:

			# Limpio el nombre de la feature
			feature_name = f.rstrip('.mean')
			print 'Evaluando feature: ' + f

			# Ordeno el frame segun la media de la variable
			data_por_media = self.data.sort(f, inplace=False)

			#Transformo la informacion relevante de esta feature a listas
			w_list = data_por_media['weight'].tolist()
			mean_list = data_por_media[feature_name + '.mean'].tolist()
			std_list = data_por_media[feature_name + '.std'].tolist()
			left_bound_list = data_por_media[feature_name + '.l'].tolist()
			right_bound_list = data_por_media[feature_name + '.r'].tolist()
			class_list = data_por_media['class'].tolist()

			menores_index = 0
			mayores_index = 0

			old_menores_index = 0
			old_mayores_index = 0

			# Obtengo las clases existentes
			clases = list(set(class_list))

			# Creo diccionarios para guardar la masa de los estrictos menores y estrictos mayores, y asi no calcularla continuamente.
			# Los menores parten vacios y los mayores parten con toda la masa
			menores_estrictos_mass = { c: 0 for c in clases}
			mayores_estrictos_mass = data_por_media.groupby('class')['weight'].sum().to_dict()

			# Me muevo a traves de los posibles pivotes. Podria hacerlo con self.data.index i at, asi podria saber
			# la fila en la que estoy trabajando
			# for i in xrange(1,self.n_rows):
			for i in data_por_media.index:

				pivote = data_por_media.at[i,f]

				# Actualizo los indices
				menores_index, mayores_index = self.update_indexes(menores_index, mayores_index, pivote, left_bound_list, right_bound_list)
				print menores_index, mayores_index

				# Actualizo la masa estrictamente menor y mayor
				for i in xrange(old_menores_index, menores_index):
					menores_estrictos_mass[class_list[i]] += w_list[i]

				for i in xrange(old_mayores_index, mayores_index):
					mayores_estrictos_mass[class_list[i]] -= w_list[i]

				old_menores_index, old_mayores_index = menores_index, mayores_index

				w_list_afectada = w_list[menores_index:mayores_index]
				mean_list_afectada = mean_list[menores_index:mayores_index]
				std_list_afectada = std_list[menores_index:mayores_index]
				left_bound_list_afectada = left_bound_list[menores_index:mayores_index]
				right_bound_list_afectada = right_bound_list[menores_index:mayores_index]
				class_list_afectada = class_list[menores_index:mayores_index]

				split_tuples_by_pivot = self.split_tuples_by_pivot
				pivote = [pivote for i in xrange(len(w_list_afectada))] ###### idea rara
				menores, mayores = split_tuples_by_pivot(w_list_afectada, mean_list_afectada, std_list_afectada, left_bound_list_afectada, right_bound_list_afectada, class_list_afectada, pivote, menores_estrictos_mass, mayores_estrictos_mass)

				# No se si es necesario
				if not any(menores) or not any(mayores):
					return

				# Calculo la ganancia de informacion para esta variable
				pivot_gain = self.gain(menores, mayores)
				
				if pivot_gain > max_gain:
					max_gain = pivot_gain
					self.feat_value = pivote
					self.feat_name = feature_name + '.mean'				

			break # Para testear cuanto se demora una sola feature

	# Toma los indices de los estrictamente menores y mayores, mas el nuevo pivote y los actualiza
	def update_indexes(self, menores_index, mayores_index, pivote, limites_l, limites_r):

		# Actualizo menores
		ultimo_r_menor = limites_r[menores_index]

		# Itero hasta encontrar una tupla que NO sea completamente menor que el pivote
		while( ultimo_r_menor <= pivote):
			menores_index += 1
			ultimo_r_menor = limites_r[menores_index]

		# Actualizo mayores
		ultimo_l_mayor = limites_l[mayores_index]

		# Itero hasta encontrar una tupla que SEA completamente mayor que el pivote
		while( ultimo_l_mayor <= pivote and mayores_index < len(limites_l) - 1):
			ultimo_l_mayor = limites_l[mayores_index]
			mayores_index += 1

		return menores_index, mayores_index

	def split_tuples_by_pivot(self, w_list, mean_list, std_list, left_bound_list, right_bound_list, class_list, pivote, menores, mayores):
		"""
		Toma un grupo de datos lo recorre entero y retorna dos diccionarios con las sumas de masa 
		separadas por clase. Un diccionario es para los datos menores que el pivote y el otro para los mayores
		"""

		for i in xrange(len(class_list)):
			cum_prob = pyRF_prob.cdf(pivote, mean_list[i], std_list[i], left_bound_list[i], right_bound_list[i])
			menores[class_list[i]] += w_list[i] * cum_prob
			mayores[class_list[i]] += w_list[i] * (1 - cum_prob)

		return menores, mayores	


	def gain(self, menores, mayores):
		"""
			Retorna la ganancia de dividir los datos en menores y mayores
			Menores y mayores son diccionarios donde la llave es el nombre de la clase y los valores son la suma de masa para ella.
		"""
		gain = self.entropia - ( sum(menores.values()) * self.entropy(menores) + sum(mayores.values()) * self.entropy(mayores) ) / self.mass

		return gain

	# Retorna la ganancia de dividir los datos en menores y mayores.
	# Deje la variable feature que no me sirve en la clase base, solo para ahorrarme repetir el metodo split. 
	# Eso debe poder arreglarse
	def gain_old(self, menores, mayores, feature):

		# total = self.data['weight'].sum()

		# gain = self.entropia - (menores['weight'].sum() * self.entropy(menores) + mayores['weight'].sum() * self.entropy(mayores)) / total
		gain = self.entropia - (menores['weight'].sum() * self.entropy(menores) + mayores['weight'].sum() * self.entropy(mayores)) / self.mass

		return gain

	def entropy(self, data):
		"""
		Retorna la entropia de un grupo de datos.
		data: diccionario donde las llaves son nombres de clases y los valores sumas (o conteos de valores)
		"""

		total = sum(data.values())
		entropia = 0
		
		for clase in data.keys():
			entropia -= (data[clase] / total) * np.log(data[clase] / total)

		return entropia

	# Retorna la entropia de un grupo de datos
	def entropy_old(self, data):

		# El total es la masa de probabilidad total del grupo de datos
		total = data['weight'].sum()
		log = np.log2
		entropia = 0

		pesos = data.groupby('class')['weight']
		for suma in pesos.sum():
			entropia -= (suma / total) * log(suma / total)

		return entropia

	def predict(self, tupla, prediction={}, w=1):
		# Si es que es el nodo raiz
		if len(prediction.keys()) == 0:
			prediction = {c: 0.0 for c in self.data['class'].unique() }

		if self.is_leaf:
			aux = deepcopy(prediction)
			aux[self.clase] += w
			return aux

		# Puede que falte chequear casos bordes, al igual que lo hago en get_menores y get_mayores
		else:
			feature_name = self.feat_name.rstrip('.mean')
			mean = tupla[feature_name + '.mean']
			std = tupla[feature_name + '.std']
			l = tupla[feature_name + '.l']
			r = tupla[feature_name + '.r']
			pivote = self.feat_value

			w_right = self.get_weight(w, mean, std, l, r, pivote, 'mayor')
			w_left = self.get_weight(w, mean, std, l, r, pivote, 'menor')
			
			a = self.right.predict(tupla, prediction, w_right)
			b = self.left.predict(tupla, prediction, w_left)

			# Tengo que retornar la suma elementwise de los diccionarios a y b
			return {key: a[key] + b[key] for key in a}