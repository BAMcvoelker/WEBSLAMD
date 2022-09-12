# Adapted from the original Sequential Learning App
# https://github.com/BAMresearch/SequentialLearningApp
import numpy as np
import pandas as pd
from lolopy.learners import RandomForestRegressor
from scipy.spatial import distance_matrix
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
from sklearn.preprocessing import OrdinalEncoder

from slamd.common.error_handling import ValueNotSupportedException, SequentialLearningException
from slamd.discovery.processing.algorithms.plot_generator import PlotGenerator


class DiscoveryExperiment:

    def __init__(self, dataframe, model, curiosity, features,
                 targets, target_weights, target_max_or_min,
                 fixed_targets, fixed_target_weights, fixed_target_max_or_min):
        self.dataframe = dataframe
        self.model = model
        self.curiosity = curiosity
        self.targets = targets
        self.target_weights = target_weights
        self.target_max_or_min = target_max_or_min
        self.fixed_targets = fixed_targets
        self.fixed_target_weights = fixed_target_weights
        self.fixed_target_max_or_min = fixed_target_max_or_min
        self.features = features

        # Partition the dataframe in three parts: features, targets and fixed targets
        self.features_df = dataframe[features]
        self.target_df = dataframe[targets]
        self.fixed_target_df = dataframe[fixed_targets]

        if len(targets) == 0:
            raise SequentialLearningException('No targets were specified!')

        # Select the rows that have a label for the first target
        # These have a null value in the corresponding column
        self.prediction_index = pd.isnull(self.dataframe[[self.targets[0]]]).to_numpy().nonzero()[0]
        # The rows with labels (the training set) are the rest of the rows
        self.sample_index = self.dataframe.index.difference(self.prediction_index)

    def run(self):
        self._preprocess_features()
        self.decide_max_or_min(self.targets, self.target_max_or_min)
        self.decide_max_or_min(self.fixed_targets, self.fixed_target_max_or_min)
        self.fit_model()

        # The strategy is always 'MLI (explore & exploit)' for this implementation
        # See the original app for other possibilities
        utility_function = self.update_index_MLI()

        novelty_factor = self.compute_novelty_factor()

        # Original dataframe
        df = self.dataframe
        # Add the columns with utility and novelty values
        df = df.iloc[self.prediction_index].assign(Utility=pd.Series(utility_function).values)
        df = df.loc[self.prediction_index].assign(Novelty=pd.Series(novelty_factor).values)

        # Fill in prediction and uncertainty values
        if self.uncertainty.ndim > 1:
            for i in range(len(self.targets)):
                df[self.targets[i]] = self.prediction[:, i]
                uncertainty_name_column = 'Uncertainty (' + self.targets[i] + ' )'
                df[uncertainty_name_column] = self.uncertainty[:, i].tolist()
                df[uncertainty_name_column] = df[uncertainty_name_column].apply(lambda row: round(row, 5))
        else:
            df[self.targets] = self.prediction.reshape(len(self.prediction), 1)
            uncertainty_name_column = 'Uncertainty (' + str(self.targets[0]) + ' )'
            df[uncertainty_name_column] = self.uncertainty.reshape(len(self.uncertainty), 1)
            df[uncertainty_name_column] = df[uncertainty_name_column].apply(lambda row: round(row, 5))

        df[self.targets] = df[self.targets].apply(lambda row: round(row, 6))
        df['Utility'] = df['Utility'].apply(lambda row: round(row, 6))
        df['Novelty'] = df['Novelty'].apply(lambda row: round(row, 6))

        sorted = df.sort_values(by='Utility', ascending=False)

        target_list = sorted[self.targets]
        if len(self.fixed_targets) > 0:
            target_list = pd.concat((target_list, sorted[self.fixed_targets]), axis=1)
        target_list = pd.concat((target_list, sorted['Utility']), axis=1)

        plot = PlotGenerator.create_target_scatter_plot(target_list)

        return sorted, plot

    def _preprocess_features(self):
        non_numeric_features = [col for col, datatype in self.features_df.dtypes.items() if
                                not np.issubdtype(datatype, np.number)]
        if len(non_numeric_features) > 0:
            encoder = OrdinalEncoder()
            for feature in non_numeric_features:
                self.features_df.loc[:, feature] = encoder.fit_transform(self.features_df[[feature]])
        self.features_df = self.features_df.dropna(axis=1)

    def normalize_data(self):
        # Subtract the mean and divide by the standard deviation of each column
        std = self.features_df.std().apply(lambda x: x if x != 0 else 1)
        self.features_df = (self.features_df - self.features_df.mean()) / std

        std = self.target_df.std().apply(lambda x: x if x != 0 else 1)
        self.target_df = (self.target_df - self.target_df.mean()) / std

        std = self.fixed_target_df.std().apply(lambda x: x if x != 0 else 1)
        self.fixed_target_df = (self.fixed_target_df - self.fixed_target_df.mean()) / std

    def decide_max_or_min(self, columns, max_or_min):
        # Multiply the column by -1 if it needs to be minimized
        for (column, value) in zip(columns, max_or_min):
            if value == 'minimize':
                self.fixed_target_df[column] *= (-1)

    def fit_model(self):
        if self.model == 'AI Model (lolo Random Forest)':
            self.fit_random_forest_with_jack_knife_variance_estimators()
        elif self.model == 'Statistics-based model (Gaussian Process Regression)':
            self.fit_gaussian_process_regression()
        else:
            raise ValueNotSupportedException(f'Model {self.model} value not supported')

    def fit_gaussian_process_regression(self):
        for i in range(len(self.targets)):
            # Initialize the model with given hyperparameters
            kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
            gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=9)

            # Train the GPR model for every target with the corresponding rows and labels
            training_rows = self.features_df.iloc[self.sample_index].to_numpy()
            training_labels = self.target_df[self.targets[i]].iloc[self.sample_index].to_numpy()

            self._check_target_label_validity(training_labels)

            nan_counts = list(self.target_df.isna().sum())

            previous_count = nan_counts[0]
            for j in range(1, len(nan_counts)):
                if nan_counts[1] != previous_count:
                    raise SequentialLearningException('Targets used are labelled for differing rows.')
                previous_count = nan_counts[j]

            gpr.fit(training_rows, training_labels)

            # Predict the label for the remaining rows
            rows_to_predict = self.features_df.iloc[self.prediction_index]
            prediction, uncertainty = gpr.predict(rows_to_predict, return_std=True)

            if i == 0:
                uncertainty_stacked = uncertainty
                pred_stacked = prediction
            else:
                uncertainty_stacked = np.vstack((uncertainty_stacked, uncertainty))
                pred_stacked = np.vstack((pred_stacked, prediction))

        self.uncertainty = uncertainty_stacked.T
        self.prediction = pred_stacked.T

    def fit_random_forest_with_jack_knife_variance_estimators(self):
        for i in range(len(self.targets)):
            # Initialize the model
            rfr = RandomForestRegressor()

            # Train the model
            training_rows = self.features_df.iloc[self.sample_index].to_numpy()
            training_labels = self.target_df.iloc[self.sample_index]

            self._check_target_label_validity(training_labels)

            self.x = training_rows
            # Sum the training labels for all targets
            self.y = training_labels.sum(axis=1).to_frame().to_numpy()
            if self.y.shape[0] < 8:
                self.x = np.tile(self.x, (4, 1))
                self.y = np.tile(self.y, (4, 1))
            rfr.fit(self.x, self.y)

            # Predict the label for the remaining rows
            rows_to_predict = self.features_df.iloc[self.prediction_index]
            prediction, uncertainty = rfr.predict(rows_to_predict, return_std=True)

            if i == 0:
                uncertainty_stacked = uncertainty
                pred_stacked = prediction
            else:
                uncertainty_stacked = np.vstack((uncertainty_stacked, uncertainty))
                pred_stacked = np.vstack((pred_stacked, prediction))

        self.uncertainty = uncertainty_stacked.T
        self.prediction = pred_stacked.T

    def compute_novelty_factor(self):
        features_of_predicted_rows = self.features_df.iloc[self.prediction_index]
        features_of_known_rows = self.features_df.iloc[self.sample_index]

        distance = distance_matrix(features_of_predicted_rows, features_of_known_rows)
        min_distances = distance.min(axis=1)
        max_of_min_distances = min_distances.max()
        return min_distances * (max_of_min_distances ** (-1))

    def update_index_MLI(self):
        predicted_rows = self.target_df.iloc[self.sample_index]
        # Normalize the uncertainty of the predicted labels
        uncertainty_norm = self.uncertainty / np.array(predicted_rows.std())
        # Normalize the predicted labels
        prediction_norm = (self.prediction - np.array(predicted_rows.mean())) / np.array(predicted_rows.std())

        if self.prediction.ndim >= 2:
            # Scale the prediction and the uncertainty by the given weight for that target
            for w in range(len(self.target_weights)):
                prediction_norm[:, w] *= self.target_weights[w]
                uncertainty_norm[:, w] *= self.target_weights[w]
        else:
            # There is only one target property and weights do not matter
            # Nevertheless multiply by the single weight available
            prediction_norm *= self.target_weights[0]
            uncertainty_norm *= self.target_weights[0]

        self.normalize_data()

        if len(self.fixed_targets) > 0:
            fixed_targets_for_predicted_rows = self.apply_weights_to_fixed_targets()
        else:
            fixed_targets_for_predicted_rows = np.zeros(len(self.prediction_index))

        # Compute the value of the utility function
        # See slide 43 of the PowerPoint presentation
        if len(self.targets) > 1:
            utility_function = fixed_targets_for_predicted_rows.squeeze(
            ) + prediction_norm.sum(axis=1) + self.curiosity * uncertainty_norm.sum(axis=1)
        else:
            utility_function = fixed_targets_for_predicted_rows.squeeze(
            ) + prediction_norm.squeeze() + self.curiosity * uncertainty_norm.squeeze()

        return utility_function

    def apply_weights_to_fixed_targets(self):
        fixed_targets_for_predicted_rows = self.fixed_target_df.iloc[self.prediction_index].to_numpy()

        for w in range(len(self.fixed_target_weights)):
            fixed_targets_for_predicted_rows[w] *= self.fixed_target_weights[w]
        # Sum the fixed targets values row-wise for the case that there are several of them
        # We need to simply add their contributions in that case
        return fixed_targets_for_predicted_rows.sum(axis=1)

    def _check_target_label_validity(self, training_labels):
        number_of_labelled_targets = training_labels.shape[0]
        if number_of_labelled_targets == 0:
            raise SequentialLearningException('No labels exist.')
        all_data_is_labelled = self.dataframe.shape[0] == number_of_labelled_targets
        if all_data_is_labelled:
            raise SequentialLearningException('All data is already labelled.')