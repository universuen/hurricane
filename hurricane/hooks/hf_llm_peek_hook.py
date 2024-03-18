import torch
from transformers import PreTrainedTokenizer

from hurricane.hooks.hook_base import HookBase
from hurricane.trainers.trainer import Trainer
from hurricane.utils import is_deepspeed_zero3


class HFLLMPeekHook(HookBase):
    def __init__(
        self, 
        prompts: list[str], 
        tokenizer: PreTrainedTokenizer,
        interval: int = 1,
    ) -> None:
        super().__init__()
        self.prompts = prompts
        self.tokenizer = tokenizer
        self.interval = interval
    
    def iteration_end(self, trainer: Trainer) -> None:
        if trainer.accelerator.is_main_process \
        or is_deepspeed_zero3(trainer.accelerator):
            idx = trainer.ctx.batch_idx + 1
            num_batches = len(trainer.data_loader)
            if idx % self.interval == 0 or idx == num_batches:
                original_model = trainer.accelerator.unwrap_model(trainer.model)
                original_model.eval()
                answers = []
                with torch.no_grad():
                    for prompt in self.prompts:
                        inputs = self.tokenizer(prompt, return_tensors="pt").to(original_model.device)
                        outputs = original_model.generate(**inputs, max_new_tokens=100)
                        answer_ids = outputs[0][len(inputs.input_ids[0]):]
                        answer = self.tokenizer.decode(answer_ids, skip_special_tokens=True)
                        answers.append(answer)
                peek_results = zip(self.prompts, answers)
                if hasattr(trainer, 'logger') and trainer.accelerator.is_main_process:
                    for q, a in peek_results:
                        trainer.logger.info(f'Q:{q} A:{a}')
