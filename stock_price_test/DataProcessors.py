import pandas as pd
import numpy as np
from sklearn import preprocessing


class DataProcessor:
	def __init__(self, train_dataset: pd.DataFrame, test_dataset: pd.DataFrame, time_steps: int = 1, target_column: str = 'BTC_Close'):
		self.train_dataset = train_dataset
		self.test_dataset = test_dataset
		self.time_steps = time_steps
		self.X_scaler = preprocessing.MinMaxScaler()
		self.y_scaler = preprocessing.MinMaxScaler()
		self.target_column = target_column

	def create_sequences(self, data, target):
		X, y = [], []
		for i in range(len(data) - self.time_steps):
			X.append(data[i:(i + self.time_steps)])
			y.append(target[i + self.time_steps])
		return np.array(X), np.array(y)

	def prepare_data(self):
		X_train = self.train_dataset
		Y_train = self.train_dataset[self.target_column]
		X_test = self.test_dataset
		Y_test = self.test_dataset[self.target_column]
		X_train, Y_train = self.create_sequences(X_train.values, Y_train.values)
		X_test, Y_test = self.create_sequences(X_test.values, Y_test.values)
		X_train_scaled = self.X_scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
		X_test_scaled = self.X_scaler.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)
		# Y_train_scaled = self.y_scaler.fit_transform(Y_train.reshape(-1, 1)).reshape(Y_train.shape)
		# Y_test_scaled = self.y_scaler.transform(Y_test.reshape(-1, 1)).reshape(Y_test.shape)
		return X_train_scaled, Y_train, X_test_scaled, Y_test