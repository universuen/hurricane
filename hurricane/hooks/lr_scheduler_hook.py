from torch.optim.lr_scheduler import LRScheduler

from hurricane.hooks.hook_base import HookBase
from hurricane.trainers.trainer import Trainer


class LRSchedulerHook(HookBase):
    def __init__(
        self,
        lr_scheduler: LRScheduler = None,
        mode: str = 'per_epoch',
    ) -> None:
        super().__init__()
        assert mode in ('per_epoch', 'per_step')
        self.lr_scheduler = lr_scheduler
        self.mode = mode
    
    
    def on_training_start(self, trainer: Trainer) -> None:
        if self.lr_scheduler is None:
            return
        
        trainer.accelerator.step_scheduler_with_optimizer = (self.mode == 'per_step')
        trainer.accelerator.register_for_checkpointing(self.lr_scheduler)
    
    
    def on_epoch_end(self, trainer: Trainer) -> None:
        if self.lr_scheduler is None or self.mode != 'per_epoch':
            return
        
        self.lr_scheduler.step()
        if hasattr(trainer, 'logger') and trainer.accelerator.is_main_process:
            trainer.logger.info(f'Current lr: {self.lr_scheduler.get_last_lr()}')
    
    
    def on_step_end(self, trainer: Trainer) -> None:
        if self.lr_scheduler is None or self.mode != 'per_step':
            return
        
        self.lr_scheduler.step()
        if hasattr(trainer, 'logger') and trainer.accelerator.is_main_process:
            trainer.logger.info(f'Current lr: {self.lr_scheduler.get_last_lr()}')