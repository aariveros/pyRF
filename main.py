import pandas as pd
from tree import Tree

if __name__ == '__main__':

	nombres = ['sepal length', 'sepal width', 'petal length', 'petal width', 'class']
	data = pd.read_csv('iris.data', header = None, names = nombres)

	clf = Tree('gain')
	clf.fit(data)


	