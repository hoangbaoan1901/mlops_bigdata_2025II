import sklearn
import tensorflow as tf


class LSTMRegressor(sklearn.base.BaseEstimator, sklearn.base.RegressorMixin):
    def __init__(self, units=[64], dropouts=[0.2], kernel_regularizer=None, patience=0, batch_size=32, epochs=50, validation_split=0.1):
        """Note: Units and dropouts list should be of the same length"""
        super().__init__()
        self.units_ = units
        self.dropouts = dropouts
        self.kernel_regularizer = kernel_regularizer
        self.patience = patience
        self.batch_size = batch_size
        self.epochs = epochs
        self.model = tf.keras.models.Sequential()
        self.validation_split = validation_split
        self.is_fitted = False

    def fit(self, X, y):
        tf.keras.backend.clear_session()
        self.model.add(tf.keras.layers.Input(shape=(X.shape[1], X.shape[2])))
        for i in range(len(self.units_)):
            if i == len(self.units_) - 1:
                self.model.add(tf.keras.layers.LSTM(
                    self.units_[i], return_sequences=False, kernel_regularizer=self.kernel_regularizer, activation='relu'))
            else:
                self.model.add(tf.keras.layers.LSTM(
                    self.units_[i], return_sequences=True, kernel_regularizer=self.kernel_regularizer, activation='relu'))
            self.model.add(tf.keras.layers.Dropout(self.dropouts[i]))
        self.model.add(tf.keras.layers.Dense(1))
        self.model.compile(optimizer=tf.keras.optimizers.Adam(
            learning_rate=1e-3), loss='mse')
        if self.patience > 0:
            early_stopping = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=self.patience, restore_best_weights=True)
            self.model.fit(X, y, batch_size=self.batch_size, epochs=self.epochs, callbacks=[
                           early_stopping], validation_split=self.validation_split, verbose=0)
        else:
            self.model.fit(X, y, batch_size=self.batch_size,
                           epochs=self.epochs, verbose=0)
        self.is_fitted = True
        return self

    def predict(self, X):
        return self.model.predict(X)

    def get_params(self, deep=True):
        return {
            # Set units_ for trained model
            'units': self.units_,
            'dropouts': self.dropouts,
            'kernel_regularizer': self.kernel_regularizer,
            'patience': self.patience,
            'batch_size': self.batch_size,
            'epochs': self.epochs,
            'validation_split': self.validation_split
        }

    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self

    def get_layer(self):
        return self.model.layers


class GRURegressor(sklearn.base.BaseEstimator, sklearn.base.RegressorMixin):
    def __init__(self, units=[64], dropouts=[0.2], kernel_regularizer=None, patience=0, batch_size=32, epochs=50, validation_split=0.1):
        """Note: Units and dropouts list should be of the same length"""
        super().__init__()
        self.units_ = units
        self.dropouts = dropouts
        self.kernel_regularizer = kernel_regularizer
        self.patience = patience
        self.batch_size = batch_size
        self.epochs = epochs
        self.model = tf.keras.models.Sequential()
        self.validation_split = validation_split
        self.is_fitted = False

    def fit(self, X, y):
        tf.keras.backend.clear_session()
        self.model.add(tf.keras.layers.Input(shape=(X.shape[1], X.shape[2])))
        for i in range(len(self.units_)):
            if i == len(self.units_) - 1:
                self.model.add(tf.keras.layers.GRU(
                    self.units_[i], return_sequences=False, kernel_regularizer=self.kernel_regularizer, activation='relu'))
            else:
                self.model.add(tf.keras.layers.GRU(
                    self.units_[i], return_sequences=True, kernel_regularizer=self.kernel_regularizer, activation='relu'))
            self.model.add(tf.keras.layers.Dropout(self.dropouts[i]))
        self.model.add(tf.keras.layers.Dense(1))
        self.model.compile(optimizer=tf.keras.optimizers.Adam(
            learning_rate=1e-3), loss='mse')
        if self.patience > 0:
            early_stopping = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=self.patience, restore_best_weights=True)
            self.model.fit(X, y, batch_size=self.batch_size, epochs=self.epochs, callbacks=[
                           early_stopping], validation_split=self.validation_split, verbose=0)
        else:
            self.model.fit(X, y, batch_size=self.batch_size,
                           epochs=self.epochs, verbose=0)
        self.is_fitted = True
        return self

    def predict(self, X):
        return self.model.predict(X)

    def get_params(self, deep=True):
        return {
            'units': self.units_,
            'dropouts': self.dropouts,
            'kernel_regularizer': self.kernel_regularizer,
            'patience': self.patience,
            'batch_size': self.batch_size,
            'epochs': self.epochs,
            'validation_split': self.validation_split
        }

    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self

    def get_layer(self):
        return self.model.layers


class MLPRegressor(sklearn.base.BaseEstimator, sklearn.base.RegressorMixin):
    def __init__(self, units=[64], dropouts=[0.2], kernel_regularizer=None, patience=0, batch_size=32, epochs=50, validation_split=0.1):
        """Note: Units and dropouts list should be of the same length"""
        super().__init__()
        self.units_ = units
        self.dropouts = dropouts
        self.kernel_regularizer = kernel_regularizer
        self.patience = patience
        self.batch_size = batch_size
        self.epochs = epochs
        self.model = tf.keras.models.Sequential()
        self.validation_split = validation_split
        self.is_fitted = False

    def fit(self, X, y):
        tf.keras.backend.clear_session()
        self.model.add(tf.keras.layers.Input(shape=(X.shape[1], X.shape[2])))
        self.model.add(tf.keras.layers.Flatten())
        for i in range(len(self.units_)):
            if i == len(self.units_) - 1:
                self.model.add(tf.keras.layers.Dense(
                    self.units_[i], kernel_regularizer=self.kernel_regularizer, activation='relu'))
            else:
                self.model.add(tf.keras.layers.Dense(
                    self.units_[i], kernel_regularizer=self.kernel_regularizer, activation='relu'))
            self.model.add(tf.keras.layers.Dropout(self.dropouts[i]))
        self.model.add(tf.keras.layers.Dense(1))
        self.model.compile(optimizer=tf.keras.optimizers.Adam(
            learning_rate=1e-3), loss='mse')
        if self.patience > 0:
            early_stopping = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=self.patience, restore_best_weights=True)
            self.model.fit(X, y, batch_size=self.batch_size, epochs=self.epochs, callbacks=[
                           early_stopping], validation_split=self.validation_split, verbose=0)
        else:
            self.model.fit(X, y, batch_size=self.batch_size,
                           epochs=self.epochs, verbose=0)
        self.is_fitted = True
        return self

    def predict(self, X):
        return self.model.predict(X)

    def get_params(self, deep=True):
        return {
            'units': self.units_,
            'dropouts': self.dropouts,
            'kernel_regularizer': self.kernel_regularizer,
            'patience': self.patience,
            'batch_size': self.batch_size,
            'epochs': self.epochs,
            'validation_split': self.validation_split
        }

    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self

    def get_layer(self):
        return self.model.layers