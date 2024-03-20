import path_setup

from os import cpu_count
import logging
from pathlib import Path

from accelerate import DeepSpeedPlugin

from hurricane.config_base import ConfigBase
from hurricane.utils import get_current_date_time


gradient_accumulate_interval = 32


class PathConfig(ConfigBase):
    project = Path(__file__).parent
    data = project / 'data'
    logs = data / 'logs'
    checkpoints = data / 'checkpoints'

    def __post_init__(self) -> None:
        for path in vars(self).values():
            path.mkdir(parents=True, exist_ok=True)


class TrainerConfig(ConfigBase):
    epochs = 100
    ckpt_folder_path=PathConfig().checkpoints
    log_interval = 1
    peek_prompts=[
        '如何看待明天下雨？',
        '为什么太阳比地球大？',
        '你如何看待近期的股市？',
    ],
    peek_interval=gradient_accumulate_interval * 10
    log_interval=gradient_accumulate_interval
    ckpt_folder_path=PathConfig().checkpoints


class OptimizerConfig(ConfigBase):
    lr = 5e-5


class DataLoaderConfig(ConfigBase):
    batch_size = 1
    shuffle = True
    num_workers = cpu_count()


class CollatorConfig(ConfigBase):
    max_len = 512


class LoggerConfig(ConfigBase):
    name = get_current_date_time()
    level = logging.INFO
    logs_dir = PathConfig().logs


class AcceleratorConfig(ConfigBase):
    gradient_accumulation_steps = gradient_accumulate_interval
    deepspeed_plugin=DeepSpeedPlugin(
        gradient_accumulation_steps = gradient_accumulation_steps, 
        zero_stage = 2,
        offload_optimizer_device = 'cpu',
        zero3_init_flag = False,
    )
