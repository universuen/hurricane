import path_setup

import os

from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from transformers import AutoTokenizer, AutoModelForCausalLM
from accelerate import Accelerator
from peft import get_peft_model

from hurricane.trainers.hf_llm_trainer import HFLLMTrainer
from hurricane.collators.hf_llm_instruction_tuning_collator import HFLLMITCollator
from hurricane.logger import Logger
from hurricane.utils import launch, log_all_configs

from zhihu_qa_dataset import ZhihuQADataset
from configs import *


def main():
    accelerator_config = AcceleratorConfig()
    accelerator = Accelerator(**accelerator_config)

    logger_config = LoggerConfig()
    logger = Logger('sft_gemma_2b_peft', **logger_config)

    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    if accelerator.is_main_process:
        log_all_configs(logger)
        logger.info('Set TOKENIZERS_PARALLELISM=false to prevent dead lock.')
    
    with accelerator.main_process_first():
        tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
        model = AutoModelForCausalLM.from_pretrained("google/gemma-2b")
        dataset = ZhihuQADataset()

    tokenizer.add_special_tokens({'pad_token': '<pad>'})
    model.resize_token_embeddings(len(tokenizer))

    peft_config = PEFTConfig()
    get_peft_model(model, **peft_config)

    data_loader_config = DataLoaderConfig()
    collator_config = CollatorConfig()
    data_loader = DataLoader(
        dataset=dataset,
        collate_fn=HFLLMITCollator(
            tokenizer=tokenizer, 
            **collator_config,
        ).collate_fn,
        **data_loader_config,
    )

    optimizer_config = OptimizerConfig()
    optimizer = AdamW(
        params=model.parameters(),
        **optimizer_config,
    )

    scheduler = CosineAnnealingWarmRestarts(
        optimizer=optimizer,
        T_0=len(data_loader) // accelerator_config.gradient_accumulation_steps,
    )

    trainer_config = TrainerConfig()
    trainer = HFLLMTrainer(
        model=model, 
        data_loader=data_loader, 
        optimizer=optimizer, 
        logger=logger, 
        accelerator=accelerator,
        tokenizer=tokenizer,
        lr_scheduler=scheduler,
        lr_scheduler_mode='per_step',
        **trainer_config,
    )
    trainer.run()

launch(main, num_processes=4, use_port='8000')
