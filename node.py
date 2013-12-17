from __future__ import division
import numpy as np
from scipy import stats
# data es un dataframe que tiene que contener una columna class. La cual el arbol intenta predecir.
# podria pensar en relajar esto y simplemente indicar cual es la variable a predecir.

class Node:

	def __init__(self, data):

		self.data = data
		self.entropia = self.entropy(data)
		self.is_leaf = False
		self.clase = ''
		self.feat_name = ""
		self.feat_value = None
		self.left = None
		self.right = None

		# Si es necesario particionar el nodo, llamo a split para hacerlo
		if self.check_data():
			self.split()
			menores = self.data[self.data[self.feat_name] < self.feat_value]
			mayores = self.data[self.data[self.feat_name] >= self.feat_value]

			menores = menores.drop(self.feat_name,1)
			mayores = mayores.drop(self.feat_name,1)

			self.add_left(menores)
			self.add_right(mayores)

		# De lo contrario llamo a set_leaf para transformarlo en hoja
		else:
			self.set_leaf()

	# Busca el mejor corte posible para el nodo
	def split(self):
		# Inicializo la ganancia de info en el peor nivel posible
		max_gain = -float('inf')

		# Para cada feature (no considero la clase)
		for f in self.data.columns[0:-1]:

			# separo el dominio en todas las posibles divisiones para obtener la optima division
			pivotes = self.get_pivotes(self.data[f])

			for pivote in pivotes:

				# Separo las tuplas segun si su valor de esa variable es menor o mayor que el pivote
				menores = self.data[self.data[f] < pivote]
				mayores = self.data[self.data[f] >= pivote]

				# Calculo la ganancia de informacion para esta variable
				total = len(self.data.index)
				gain = self.entropia - (len(menores) * self.entropy(menores) + len(mayores) * self.entropy(mayores)) / total

				# Comparo con la ganancia anterior, si es mejor guardo el gain, la feature correspondiente y el pivote
				if(gain > max_gain):
					max_gain = gain
					self.feat_name = f
					self.feat_value = pivote


	# Retorna la entropia de un grupo de datos
	def entropy(self, data):
		total = len(data.index)
		clases = data['class'].unique()

		entropia = 0

		for c in clases:
			p_c = len(data[data['class'] == c].index) / total
			entropia = entropia - p_c * np.log2(p_c)

		return entropia

	# determina se es necesario hacer un split de los datos
	def check_data(self):
		if self.data['class'].nunique() == 1:
			return False
		else: 
			return True

	# retorna una lista con los todos los threshold a evaluar para buscar la mejor separacion
	def get_pivotes(self, feature):

		#maximo = feature.max()
		#minimo = feature.min()
		#paso = (maximo - minimo) / 100

		#for i in range(100):
		#	pivotes.append( minimo + i*paso)

		return feature[1:].unique()

	# Convierte el nodo en hoja. Colocando la clase mas probable como resultado
	def set_leaf(self):
		self.is_leaf = True
		self.clase = stats.mode( self.data['class'])[0].item()

	def add_left(self, left_data):
		self.left = Node(left_data)

	def add_right(self, right_data):
		self.right = Node(right_data)

	def predict(self, tupla):
		if(self.is_leaf):
			return self.clase
		else:
			if(tupla['self.feat_name'] < self.feat_value):
				return self.left.predict(tupla)
			else:
				return self.right.predict(tupla)
