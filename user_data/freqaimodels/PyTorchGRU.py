from typing import Any

import torch

from freqtrade.freqai.base_models.BasePyTorchRegressor import BasePyTorchRegressor
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen
from freqtrade.freqai.torch.PyTorchDataConvertor import (
    DefaultPyTorchDataConvertor,
    PyTorchDataConvertor,
)

# We will reuse the existing MLP model structure for now to ensure it loads
from freqtrade.freqai.torch.PyTorchMLPModel import PyTorchMLPModel
from freqtrade.freqai.torch.PyTorchModelTrainer import PyTorchModelTrainer


class PyTorchGRU(BasePyTorchRegressor):
    """
    Custom GRU model - for now, uses MLP architecture as a placeholder to ensure loading works.
    """

    @property
    def data_convertor(self) -> PyTorchDataConvertor:
        return DefaultPyTorchDataConvertor(target_tensor_type=torch.float)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        config = self.freqai_info.get("model_training_parameters", {})
        self.learning_rate: float = config.get("learning_rate", 3e-4)
        self.model_kwargs: dict[str, Any] = config.get("model_kwargs", {})
        self.trainer_kwargs: dict[str, Any] = config.get("trainer_kwargs", {})

    def fit(self, data_dictionary: dict, dk: FreqaiDataKitchen, **kwargs) -> Any:
        n_features = data_dictionary["train_features"].shape[-1]

        # Using the existing MLP model as a placeholder
        model = PyTorchMLPModel(input_dim=n_features, output_dim=1, **self.model_kwargs)
        model.to(self.device)

        optimizer = torch.optim.AdamW(model.parameters(), lr=self.learning_rate)
        criterion = torch.nn.MSELoss()

        trainer = self.get_init_model(dk.pair)
        if trainer is None:
            trainer = PyTorchModelTrainer(
                model=model,
                optimizer=optimizer,
                criterion=criterion,
                device=self.device,
                data_convertor=self.data_convertor,
                tb_logger=self.tb_logger,
                **self.trainer_kwargs,
            )
        trainer.fit(data_dictionary, self.splits)
        return trainer
