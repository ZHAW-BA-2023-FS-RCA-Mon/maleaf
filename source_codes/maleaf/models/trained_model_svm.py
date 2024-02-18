import logging
import pickle
import time
from os import path

import numpy as np
import pandas as pd
from sklearn.svm import SVC

logger = logging.getLogger(__name__)


class TrainedModelSVM:

    def __init__(self, config, clustering_instances, sort_indices, normalization_factors, training_data,
                 mean_ground_truth_values, dataset_tag=None):
        self.partial_structure_models = None
        self.independent_nodes = []
        self.normalization_factors = normalization_factors
        self.sort_indices = sort_indices
        self.clustering_instances = clustering_instances
        self.training_data = training_data
        self.mean_ground_truth_values = mean_ground_truth_values
        self.dataset_tag = dataset_tag
        self.all_service_statuses = self.get_all_service_statuses(config, training_data)
        self.all_metrics = list(training_data.drop(columns=self.all_service_statuses))
        logger.info("Starting to construct svm structure model...")
        if not dataset_tag:
            filename = time.strftime("%Y%m%d_%H%M%S") + "_svm"
        else:
            filename = dataset_tag + "_svm"
        if path.exists(f"structure_models/{filename}.pickle"):
            self.structure_model = TrainedModelSVM.read_from_file(f"structure_models/{filename}.pickle")
        else:
            self.structure_model = self.learn_from_data(config, training_data, self.all_service_statuses)
            TrainedModelSVM.save_data_to_file(self.structure_model, filename=f"structure_models/{filename}.pickle")
        logger.info("Structure model is constructed.")
        logger.info("Training complete.")

    @staticmethod
    def get_all_service_statuses(config, training_dataframe):
        service_statuses = []

        for service_name in config["services_for_fault_injection"]:
            service_name = service_name.replace('-', '_')
            service_statuses.extend([service_name, f"{service_name}_delay", f"{service_name}_cpu",
                                     f"{service_name}_memory", f"{service_name}_failure"])
        for service_status in service_statuses.copy():
            if service_status not in training_dataframe.columns:
                service_statuses.remove(service_status)
        return set(service_statuses)

    @staticmethod
    def learn_from_data(config, training_dataframe, all_service_statuses):
        Y = []
        X = pd.DataFrame(columns=training_dataframe.columns)

        for index, row in training_dataframe.iterrows():
            error_classes = []
            for service_status in all_service_statuses.copy():
                fault_status = row[service_status]
                if fault_status != 0:
                    error_classes = np.append(error_classes, service_status + '_' + str(fault_status))

            if len(error_classes) == 0:
                Y = np.append(Y, 'no_fault')
                X = X.append(row)

            for error_class in error_classes:
                Y = np.append(Y, error_class)
                X = X.append(row)

        X = X.drop(columns=all_service_statuses)

        classifier = SVC(kernel=config["svm_kernel"], random_state=config["random_state_svm"], probability=True)
        classifier.fit(X, Y)

        matched = 0
        for index, row in X.iterrows():
            actual = Y[index]
            predicted = classifier.predict([row.values])
            match = actual == predicted
            if match:
                matched += 1

        accuracy = matched / int(config["number_of_training_data"])
        logger.info('Accuracy of training set on trained model: ' + str(accuracy) + ' for rows: ' +
                    str(config["number_of_training_data"]))
        return classifier

    @staticmethod
    def save_data_to_file(data, filename="sm_svm.pickle"):
        logger.info(f"Saving model to {filename}")
        with open(filename, "wb+") as sm_file:
            pickle.dump(data, sm_file)

    @staticmethod
    def read_from_file(filename="sm_svm.pickle"):
        logger.info(f"Reading model from {filename}")
        with open(filename, "rb") as sm_file:
            return pickle.load(sm_file)
