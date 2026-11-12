"""
2026.6.7+rhaiv.1
2026.6.9+rhaiv.2
5.13.0
1.7.1
__UNSLOTH_VERSIONING__
"""

# Unsloth auto generated code
# Copyright 2023-present Daniel Han-Chen, Michael Han-Chen & the Unsloth team. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from torch import Tensor
import torch
import torch.nn as nn
from torch.nn import functional as F
from unsloth_zoo.temporary_patches.common import torch_compile
from typing import Any, List, Optional, Tuple, Union, Dict, Set, Callable
from trl.experimental.kto.kto_trainer import (Any, AutoProcessor, Callable, DataCollator, DataCollatorForUnpairedPreference, DataCollatorForVisionUnpairedPreference, DataLoader, Dataset, EvalLoopOutput, F, Hasher, IterableDataset, IterableDatasetDict, KTOConfig, KTOTrainer, LigerFusedLinearKTOLoss, LoraConfig, PartialState, Path, PeftConfig, PeftModel, PreTrainedModel, PreTrainedTokenizerBase, ProcessorMixin, Sampler, SequentialSampler, SyncRefModelCallback, TrainerCallback, Version, _BaseTrainer, _get_kl_completion_ids, apply_chat_template, concatenate_datasets, contextlib, create_model_from_path, dataclass, defaultdict, disable_dropout_in_model, disable_gradient_checkpointing, extract_prompt, flush_left, get_act_offloading_ctx_manager, get_config_model_id, get_dataset_column_names, get_peft_model, has_length, hash_module, is_conversational, is_liger_kernel_available, is_peft_available, is_peft_model, logger, os, pad, peft, prepare_deepspeed, prepare_fsdp, prepare_multimodal_messages, selective_log_softmax, textwrap, torch, tqdm, transformers, unpair_preference_dataset, use_adapter, AutoProcessor, Callable, DataCollator, DataCollatorForUnpairedPreference, DataCollatorForVisionUnpairedPreference, Dataset, EvalLoopOutput, F, IterableDataset, IterableDatasetDict, KTOConfig, KTOTrainer, LigerFusedLinearKTOLoss, LoraConfig, PeftConfig, PeftModel, PreTrainedModel, PreTrainedTokenizerBase, ProcessorMixin, SyncRefModelCallback, TrainerCallback, Version, contextlib, create_model_from_path, defaultdict, disable_dropout_in_model, get_act_offloading_ctx_manager, get_config_model_id, get_peft_model, is_liger_kernel_available, is_peft_available, is_peft_model, logger, os, pad, peft, prepare_deepspeed, prepare_fsdp, torch, transformers, unpair_preference_dataset, F, PeftModel, PreTrainedModel, is_peft_available, logger, os, peft, torch)


import os
import math
import logging
from typing import *
from dataclasses import dataclass, field
from packaging.version import Version
import torch
import numpy as np
from contextlib import nullcontext
from torch.nn import functional as F
import inspect
from transformers import DataCollatorForSeq2Seq, DataCollatorForLanguageModeling as TransformersDataCollatorForLanguageModeling
from transformers.training_args import ParallelMode
from unsloth_zoo.device_type import DEVICE_TYPE, device_synchronize

# Wrap trainer with padding to right and enable training mode
import functools
from types import MethodType
try:
    from unsloth_zoo.gradient_checkpointing import reset_unsloth_gradient_checkpointing_buffers
except:
    def reset_unsloth_gradient_checkpointing_buffers(): pass
# Canonical reset lives in unsloth.models._utils so the SFT auto-packing wrapper and the plain
# Trainer loop can import the same helper; fall back to a no-op only if it can't be imported.
try:
    from unsloth.models._utils import _unsloth_reset_stray_compile_cache
except Exception:
    def _unsloth_reset_stray_compile_cache(self): pass
def prepare_for_training_mode(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        # Drop any torch.compile graph cache poisoned by a stray pre-train forward.
        try:
            _unsloth_reset_stray_compile_cache(self)
        except Exception:
            pass
        # Finish the previous W&B run if this is a subsequent train() call.
        # We do this at the START of train() (not the end) so that
        # evaluate() / log() still work after train() completes.
        # HF's WandbCallback.setup() will call wandb.init() for the new run.
        # See: https://github.com/unslothai/unsloth/issues/3954
        if getattr(self, '_unsloth_training_completed', False):
            try:
                import wandb
                if wandb.run is not None:
                    wandb.finish()
                    # Reset HF's WandbCallback so it calls wandb.init() for the new run
                    for cb in self.callback_handler.callbacks:
                        if type(cb).__name__ == 'WandbCallback':
                            cb._initialized = False
                            break
            except:
                pass
        # Enable training mode
        _was_training = None
        # Get gradient checkpointing setting from training arguments
        use_gc = getattr(self.args, 'gradient_checkpointing', True)
        if hasattr(self, 'model') and hasattr(self.model, "training"):
            _was_training = self.model.training
        if hasattr(self, 'model') and hasattr(self.model, "for_training"):
            self.model.for_training(use_gradient_checkpointing=use_gc)
        output = f(self, *args, **kwargs)
        # Restore previous mode when possible
        if hasattr(self, 'model') and hasattr(self.model, "for_inference"):
            if _was_training is False:
                self.model.for_inference()
            elif _was_training is True and hasattr(self.model, "for_training"):
                self.model.for_training(use_gradient_checkpointing=use_gc)
        # Reset gradient checkpointing buffers to free memory while staying ready for next run
        try:
            reset_unsloth_gradient_checkpointing_buffers()
        except:
            pass
        # Mark that training completed so the next train() call can
        # finish this W&B run before starting a new one
        self._unsloth_training_completed = True
        return output
    return wrapper
pass

torch_compile_options = {
    "epilogue_fusion"   : True,
    "max_autotune"      : False,
    "shape_padding"     : True,
    "trace.enabled"     : False,
    "triton.cudagraphs" : False,
}

@torch.compile(dynamic = True, fullgraph = True, options = torch_compile_options,)
def chunked_hidden_states_selective_log_softmax(
    hidden_states: torch.Tensor,
    lm_head: torch.Tensor,
    index: torch.Tensor,
    chunks: int = 4,
    logit_scale_multiply: float = 0.0,
    logit_scale_divide: float = 0.0,
    logit_softcapping: float = 0.0,
    temperature: float = 1.0,
) -> torch.Tensor:
    # All Unsloth Zoo code licensed under AGPL3
    flat_hidden_states = hidden_states.reshape(-1, hidden_states.shape[-1])
    flat_index = index.reshape(-1)

    chunked_hidden_states = torch.chunk(flat_hidden_states, chunks=chunks, dim=0)
    chunked_index = torch.chunk(flat_index, chunks=chunks, dim=0)

    all_per_token_logps = []

    for chunk_hidden_states, chunk_index in zip(chunked_hidden_states, chunked_index):
        chunk_logits = chunk_hidden_states.to(lm_head.dtype) @ lm_head.t()

        if logit_scale_multiply != 0.0:
            chunk_logits = chunk_logits * logit_scale_multiply
        if logit_scale_divide != 0.0:
            chunk_logits = chunk_logits / logit_scale_divide
        if logit_softcapping != 0.0:
            chunk_logits = logit_softcapping * torch.tanh(chunk_logits / logit_softcapping)

        chunk_logits = chunk_logits.to(torch.float32)

        if temperature != 1.0:
            chunk_logits = chunk_logits / temperature

        selected_logits = torch.gather(chunk_logits, dim=-1, index=chunk_index.unsqueeze(-1)).squeeze(-1)
        logsumexp_values = torch.logsumexp(chunk_logits, dim=-1)
        per_token_logps = selected_logits - logsumexp_values
        all_per_token_logps.append(per_token_logps)

    all_per_token_logps = torch.concat(all_per_token_logps)

    all_per_token_logps = all_per_token_logps.reshape((hidden_states.shape[0], hidden_states.shape[1]))
    return all_per_token_logps

@torch.compile(dynamic = True, fullgraph = True, options = torch_compile_options,)
def chunked_selective_log_softmax(
    logits,
    index,
    temperature: float = 1.0,
    chunks: int = 4,
):
    chunked_logits = torch.chunk(logits.reshape(-1, logits.shape[-1]), chunks = chunks, dim = 0)
    chunked_index  = torch.chunk(index.reshape(-1), chunks = chunks, dim = 0)
    all_per_token_logps = []
    # Per-chunk selective_log_softmax.
    for chunk_logits, chunk_index in zip(chunked_logits, chunked_index):
        chunk_logits = chunk_logits.to(torch.float32)
        if temperature != 1.0:
            chunk_logits = chunk_logits / temperature
        selected_logits = torch.gather(chunk_logits, dim = -1, index = chunk_index.unsqueeze(-1)).squeeze(-1)
        logsumexp_values = torch.logsumexp(chunk_logits, dim = -1)
        per_token_logps = selected_logits - logsumexp_values
        all_per_token_logps.append(per_token_logps)
    pass
    all_per_token_logps = torch.concat(all_per_token_logps)
    all_per_token_logps = all_per_token_logps.reshape((logits.shape[0], logits.shape[1]))
    return all_per_token_logps

def calculate_pad_tokens_in_prompt(
    input_ids: torch.Tensor,
    logits_to_keep: int,
    pad_token_id: int
) -> torch.Tensor:
    """Count left-padded tokens per sequence, e.g. [pad, pad, pad, cat] -> 3."""
    if logits_to_keep >= input_ids.shape[1]:
        raise ValueError("logits_to_keep must be smaller than the sequence length.")

    prompt_section = input_ids[:, :-logits_to_keep]

    padding_mask = (prompt_section == pad_token_id)

    pad_token_counts = padding_mask.sum(dim=1)

    return pad_token_counts

def create_completion_attention_mask(
    completion_input_ids: torch.Tensor,
    left_pad_tokens_per_prompt: torch.Tensor,
    max_left_pad: int,
    pad_token_id: int
) -> torch.Tensor:
    """Build a completion mask that zeros leading prompt and trailing pad tokens.

    For [p,p,p,c,c,c,pad,pad,pad] (p=sliced prompt, c=completion, pad=padding)
    this returns [0,0,0,1,1,1,0,0,0].
    """
    batch_size, completion_len = completion_input_ids.shape
    device = completion_input_ids.device

    num_tokens_to_mask = max_left_pad - left_pad_tokens_per_prompt

    indices = torch.arange(completion_len, device=device).unsqueeze(0)
    shift_mask = indices >= num_tokens_to_mask.unsqueeze(1)

    non_padding_mask = (completion_input_ids != pad_token_id)

    final_mask = shift_mask & non_padding_mask

    return final_mask

def left_pack_padding(tensor: torch.Tensor, pad_id: int) -> torch.Tensor:
    """Move all padding tokens in each sequence to the right."""
    mask = (tensor != pad_id)
    # stable=True since the binary mask is unordered.
    sorted_indices = torch.argsort(mask, dim=1, descending=True, stable=True)
    packed_tensor = torch.gather(tensor, 1, sorted_indices)
    return packed_tensor

def align_logprobs_with_mask(
    logprob_tensor: torch.Tensor,
    attention_mask: torch.Tensor,
    pad_value: float = 0.0
) -> torch.Tensor:
    """Align a log probability tensor with a given attention mask."""

    device = logprob_tensor.device
    batch_size, logprob_seq_len = logprob_tensor.shape
    mask_seq_len = attention_mask.shape[1]

    padded_logprobs = torch.full(
        attention_mask.shape,
        fill_value=pad_value,
        dtype=logprob_tensor.dtype,
        device=device
    )

    left_pad_counts = torch.argmax(attention_mask, dim=1)

    cols = torch.arange(logprob_seq_len, device=device)
    dest_indices = left_pad_counts.unsqueeze(1) + cols

    # Destination row indices, shape [batch_size, logprob_seq_len].
    row_indices = torch.arange(batch_size, device=device).unsqueeze(1).expand_as(dest_indices)

    # Keep only in-bounds destinations, then scatter via advanced indexing.
    valid_mask = dest_indices < mask_seq_len
    valid_rows = row_indices[valid_mask]
    valid_cols = dest_indices[valid_mask]
    valid_vals = logprob_tensor[valid_mask]
    padded_logprobs[valid_rows, valid_cols] = valid_vals

    return padded_logprobs

def align_completion_tool_mask(
    tool_mask: torch.Tensor,
    completion_mask: torch.Tensor,
) -> torch.Tensor:
    """Align a raw completion-length tool/env mask with Unsloth's repacked loss mask."""
    if tool_mask is None:
        return completion_mask
    if tool_mask.shape[0] != completion_mask.shape[0]:
        raise ValueError("tool_mask batch size must match completion_mask batch size.")

    tool_mask = tool_mask.to(device=completion_mask.device)
    if tool_mask.shape == completion_mask.shape:
        aligned_tool_mask = tool_mask
    else:
        aligned_tool_mask = align_logprobs_with_mask(
            tool_mask,
            completion_mask,
            pad_value=0,
        )
    return completion_mask * aligned_tool_mask.to(dtype=completion_mask.dtype)

def autotune_batch_and_chunks(
    total_input_rows,
    seq_len,
    hidden_size,
    vocab_size,
    dtype_bytes=16,
    multiplier=None
):
    if multiplier is None:
        final_m = max(4, seq_len // 4096)
    else:
        final_m = multiplier

    if torch.cuda.is_available():
        free_bytes, _ = torch.cuda.mem_get_info()
        limit_gb = (free_bytes / (1024**3))*.80
    elif hasattr(torch, "xpu") and torch.xpu.is_available():
        # XPU: estimate free memory as total - reserved.
        total_mem = torch.xpu.get_device_properties(0).total_memory
        reserved_mem = torch.xpu.memory_reserved()
        free_bytes = total_mem - reserved_mem
        limit_gb = (free_bytes / (1024**3)) * 0.80
    else:
        # Fallback: assume 8GB available.
        limit_gb = 8.0

    bytes_to_gb = 1024**3

    b_vals = torch.arange(total_input_rows, 0, -1, device='cpu', dtype=torch.float32)

    hidden_gb = (b_vals * seq_len * hidden_size * dtype_bytes) / bytes_to_gb

    base_logits = ((b_vals/total_input_rows) * b_vals * seq_len * vocab_size * dtype_bytes) / bytes_to_gb
    logits_gb = base_logits / final_m

    total_mem_gb = hidden_gb + logits_gb

    valid_mask = total_mem_gb <= limit_gb
    valid_indices = torch.nonzero(valid_mask, as_tuple=False)

    if valid_indices.shape[0] == 0:
        #This means your GPU will OOM
        return 4, final_m

    best_idx = valid_indices[0].item()
    final_b = int(b_vals[best_idx].item())

    return final_b, final_m

def sanitize_logprob(logprob):
    """Local port of trl.scripts.vllm_serve.sanitize_logprob.
    Filters NaN logprobs from vLLM outputs."""
    value = logprob.logprob
    if math.isnan(value):
        logging.getLogger(__name__).warning(
            f"Generated NaN logprob, token logprob '{logprob}' will be ignored"
        )
        return None
    return value
@dataclass
class UnslothKTOConfig(KTOConfig):
    """
    KTOConfig(output_dir: str | None = None, per_device_train_batch_size: int = 8, num_train_epochs: float = 3.0, max_steps: int = -1, learning_rate: float = 1e-06, lr_scheduler_type: transformers.trainer_utils.SchedulerType | str = 'linear', lr_scheduler_kwargs: dict | str | None = None, warmup_steps: float = 0, optim: transformers.training_args.OptimizerNames | str = 'adamw_torch_fused', optim_args: str | None = None, weight_decay: float = 0.0, adam_beta1: float = 0.9, adam_beta2: float = 0.999, adam_epsilon: float = 1e-08, optim_target_modules: None | str | list[str] = None, gradient_accumulation_steps: int = 1, average_tokens_across_devices: bool = True, max_grad_norm: float = 1.0, label_smoothing_factor: float = 0.0, bf16: bool | None = None, fp16: bool = False, bf16_full_eval: bool = False, fp16_full_eval: bool = False, tf32: bool | None = None, gradient_checkpointing: bool = True, gradient_checkpointing_kwargs: dict[str, typing.Any] | str | None = None, torch_compile: bool = False, torch_compile_backend: str | None = None, torch_compile_mode: str | None = None, use_liger_kernel: bool = False, liger_kernel_config: dict[str, bool] | None = None, use_cache: bool = False, neftune_noise_alpha: float | None = None, torch_empty_cache_steps: int | None = None, auto_find_batch_size: bool = False, logging_strategy: transformers.trainer_utils.IntervalStrategy | str = 'steps', logging_steps: float = 10, logging_first_step: bool = False, log_on_each_node: bool = True, logging_nan_inf_filter: bool = True, include_num_input_tokens_seen: str | bool = 'no', log_level: str = 'passive', log_level_replica: str = 'warning', disable_tqdm: bool | None = None, report_to: None | str | list[str] = 'none', run_name: str | None = None, project: str = 'huggingface', trackio_space_id: str | None = None, trackio_bucket_id: str | None = None, trackio_static_space_id: Union[str, NoneType, Literal[False]] = None, eval_strategy: transformers.trainer_utils.IntervalStrategy | str = 'no', eval_steps: float | None = None, eval_delay: float = 0, per_device_eval_batch_size: int = 8, prediction_loss_only: bool = False, eval_on_start: bool = False, eval_do_concat_batches: bool = True, eval_use_gather_object: bool = False, eval_accumulation_steps: int | None = None, include_for_metrics: list[str] = <factory>, batch_eval_metrics: bool = False, save_only_model: bool = False, save_strategy: transformers.trainer_utils.SaveStrategy | str = 'steps', save_steps: float = 500, save_on_each_node: bool = False, save_total_limit: int | None = None, enable_jit_checkpoint: bool = False, push_to_hub: bool = False, hub_token: str | None = None, hub_private_repo: bool | None = None, hub_model_id: str | None = None, hub_strategy: transformers.trainer_utils.HubStrategy | str = 'every_save', hub_always_push: bool = False, hub_revision: str | None = None, load_best_model_at_end: bool = False, metric_for_best_model: str | None = None, greater_is_better: bool | None = None, ignore_data_skip: bool = False, restore_callback_states_from_checkpoint: bool = False, full_determinism: bool = False, seed: int = 42, data_seed: int | None = None, use_cpu: bool = False, accelerator_config: dict | str | None = None, parallelism_config: accelerate.parallelism_config.ParallelismConfig | None = None, dataloader_drop_last: bool = False, dataloader_num_workers: int = 0, dataloader_pin_memory: bool = True, dataloader_persistent_workers: bool = False, dataloader_prefetch_factor: int | None = None, remove_unused_columns: bool = True, label_names: list[str] | None = None, train_sampling_strategy: str = 'sequential', length_column_name: str = 'length', ddp_find_unused_parameters: bool | None = None, ddp_bucket_cap_mb: int | None = None, ddp_broadcast_buffers: bool | None = None, ddp_static_graph: bool | None = None, ddp_backend: str | None = None, ddp_timeout: int = 1800, fsdp: str | None = None, fsdp_config: dict[str, typing.Any] | str | None = None, deepspeed: dict | str | None = None, debug: str | list[transformers.debug_utils.DebugOption] = '', skip_memory_metrics: bool = True, do_train: bool = False, do_eval: bool = False, do_predict: bool = False, resume_from_checkpoint: str | None = None, warmup_ratio: float | None = None, logging_dir: str | None = None, local_rank: int = -1, model_init_kwargs: dict[str, typing.Any] | str | None = None, trust_remote_code: bool = False, disable_dropout: bool = True, dataset_num_proc: int | None = None, max_length: int | None = 1024, pad_to_multiple_of: int | None = None, precompute_ref_log_probs: bool = False, precompute_ref_batch_size: int | None = None, loss_type: str = 'kto', beta: float = 0.1, desirable_weight: float = 1.0, undesirable_weight: float = 1.0, activation_offloading: bool = False, sync_ref_model: bool = False, ref_model_mixup_alpha: float = 0.6, ref_model_sync_steps: int = 512)
    """
    vllm_sampling_params: Optional[Any] = field(
        default = None,
        metadata = {'help': 'vLLM SamplingParams'},
    )
    unsloth_num_chunks : Optional[int] = field(
        default = -1,
        metadata = {'help': 'Chunk size to reduce memory usage. -1 is most efficient.'},
    )
    unsloth_logit_chunk_multiplier : Optional[int] = field(
            default = None,
            metadata = {'help': 'Multiplier for chunked logit computations.'},
        )
    unsloth_grpo_mini_batch : Optional[int] = field(
        default = None,
        metadata = {'help': 'Mini batch size for GRPO hidden state accumulation. Default is None unless user defines it.'},
    )
    max_seq_length : Optional[int] = field(
        default = None,
        metadata = {'help': 'Maximum sequence length to truncate to.'},
    )
    def __init__(
        self,
        output_dir = None,
        per_device_train_batch_size = 4,
        num_train_epochs = 3.0,
        max_steps = -1,
        learning_rate = 5e-05,
        lr_scheduler_type = 'linear',
        lr_scheduler_kwargs = None,
        warmup_steps = 0.1,
        optim = 'adamw_8bit',
        optim_args = None,
        weight_decay = 0.001,
        adam_beta1 = 0.9,
        adam_beta2 = 0.999,
        adam_epsilon = 1e-08,
        optim_target_modules = None,
        gradient_accumulation_steps = 2,
        average_tokens_across_devices = True,
        max_grad_norm = 1.0,
        label_smoothing_factor = 0.0,
        bf16 = False,
        fp16 = False,
        bf16_full_eval = False,
        fp16_full_eval = False,
        tf32 = None,
        gradient_checkpointing = True,
        gradient_checkpointing_kwargs = None,
        torch_compile = False,
        torch_compile_backend = None,
        torch_compile_mode = None,
        use_liger_kernel = False,
        liger_kernel_config = None,
        use_cache = False,
        neftune_noise_alpha = None,
        torch_empty_cache_steps = 250,
        auto_find_batch_size = False,
        logging_strategy = 'steps',
        logging_steps = 1,
        logging_first_step = False,
        log_on_each_node = True,
        logging_nan_inf_filter = False,
        include_num_input_tokens_seen = False,
        log_level = 'passive',
        log_level_replica = 'warning',
        disable_tqdm = None,
        report_to = 'none',
        run_name = None,
        project = 'huggingface',
        trackio_space_id = None,
        trackio_bucket_id = None,
        trackio_static_space_id = None,
        eval_strategy = 'no',
        eval_steps = None,
        eval_delay = 0,
        per_device_eval_batch_size = 4,
        prediction_loss_only = False,
        eval_on_start = False,
        eval_do_concat_batches = True,
        eval_use_gather_object = False,
        eval_accumulation_steps = 2,
        batch_eval_metrics = False,
        save_only_model = False,
        save_strategy = 'steps',
        save_steps = 500,
        save_on_each_node = False,
        save_total_limit = None,
        enable_jit_checkpoint = False,
        push_to_hub = False,
        hub_token = None,
        hub_private_repo = None,
        hub_model_id = None,
        hub_strategy = 'every_save',
        hub_always_push = False,
        hub_revision = None,
        load_best_model_at_end = False,
        metric_for_best_model = None,
        greater_is_better = None,
        ignore_data_skip = False,
        restore_callback_states_from_checkpoint = False,
        full_determinism = False,
        seed = 3407,
        data_seed = 3407,
        use_cpu = False,
        accelerator_config = None,
        parallelism_config = None,
        dataloader_drop_last = False,
        dataloader_num_workers = 0,
        dataloader_pin_memory = True,
        dataloader_persistent_workers = False,
        dataloader_prefetch_factor = None,
        remove_unused_columns = True,
        label_names = None,
        train_sampling_strategy = 'sequential',
        length_column_name = 'length',
        ddp_find_unused_parameters = None,
        ddp_bucket_cap_mb = None,
        ddp_broadcast_buffers = None,
        ddp_static_graph = None,
        ddp_backend = None,
        ddp_timeout = 1800,
        fsdp = None,
        fsdp_config = None,
        deepspeed = None,
        debug = '',
        skip_memory_metrics = True,
        do_train = False,
        do_eval = False,
        do_predict = False,
        resume_from_checkpoint = None,
        warmup_ratio = None,
        logging_dir = None,
        local_rank = -1,
        model_init_kwargs = None,
        trust_remote_code = False,
        disable_dropout = True,
        dataset_num_proc = None,
        max_length = 1024,
        pad_to_multiple_of = None,
        precompute_ref_log_probs = False,
        precompute_ref_batch_size = None,
        loss_type = 'kto',
        beta = 0.1,
        desirable_weight = 1.0,
        undesirable_weight = 1.0,
        activation_offloading = False,
        sync_ref_model = False,
        ref_model_mixup_alpha = 0.6,
        ref_model_sync_steps = 512,
        vllm_sampling_params = None,
        unsloth_num_chunks = -1,
        unsloth_logit_chunk_multiplier = None,
        unsloth_grpo_mini_batch = None,
        max_seq_length = None,
        **kwargs,
    ):
        if learning_rate < 1e-7: print(f'Unsloth: Your learning rate of `{learning_rate}` is too small and less than 1e-7! Consider increasing it, otherwise gradient updates will be close to 0!')
        if learning_rate > 1: print(f'Unsloth: Your learning rate of `{learning_rate}` is way too larger > 1! Consider decreasing it to 1e-1, otherwise gradient updates will explode!')
        if num_train_epochs is None:
            num_train_epochs = 3.0  # Default to 3 epochs if None, max_steps will override
        if output_dir is None and save_strategy == 'steps' and save_steps == 500:
            output_dir = 'unsloth_training_checkpoints'
            save_strategy = 'no'
        import multiprocessing as _mp
        if dataset_num_proc is None:
            if _mp.get_start_method() != 'fork':
                dataset_num_proc = None
            else:
                import psutil
                dataset_num_proc = min(max((psutil.cpu_count() or 1)+4, 2), 64)
                memory_gb_left = psutil.virtual_memory().available / (1024**3)
                if memory_gb_left <= 2: dataset_num_proc = 1
                else: dataset_num_proc = min(dataset_num_proc, int(memory_gb_left))
        if os.environ.get('UNSLOTH_ENABLE_FLEX_ATTENTION', '0') == '1':
            from unsloth_zoo.flex_attention import HAS_FLEX_ATTENTION
            if HAS_FLEX_ATTENTION and pad_to_multiple_of is None:
                from unsloth_zoo.flex_attention import FLEX_ATTENTION_BLOCK_SIZE
                pad_to_multiple_of = FLEX_ATTENTION_BLOCK_SIZE
        
        
        super().__init__(
            output_dir = output_dir,
            per_device_train_batch_size = per_device_train_batch_size,
            num_train_epochs = num_train_epochs,
            max_steps = max_steps,
            learning_rate = learning_rate,
            lr_scheduler_type = lr_scheduler_type,
            lr_scheduler_kwargs = lr_scheduler_kwargs,
            warmup_steps = warmup_steps,
            optim = optim,
            optim_args = optim_args,
            weight_decay = weight_decay,
            adam_beta1 = adam_beta1,
            adam_beta2 = adam_beta2,
            adam_epsilon = adam_epsilon,
            optim_target_modules = optim_target_modules,
            gradient_accumulation_steps = gradient_accumulation_steps,
            average_tokens_across_devices = average_tokens_across_devices,
            max_grad_norm = max_grad_norm,
            label_smoothing_factor = label_smoothing_factor,
            bf16 = bf16,
            fp16 = fp16,
            bf16_full_eval = bf16_full_eval,
            fp16_full_eval = fp16_full_eval,
            tf32 = tf32,
            gradient_checkpointing = gradient_checkpointing,
            gradient_checkpointing_kwargs = gradient_checkpointing_kwargs,
            torch_compile = torch_compile,
            torch_compile_backend = torch_compile_backend,
            torch_compile_mode = torch_compile_mode,
            use_liger_kernel = use_liger_kernel,
            liger_kernel_config = liger_kernel_config,
            use_cache = use_cache,
            neftune_noise_alpha = neftune_noise_alpha,
            torch_empty_cache_steps = torch_empty_cache_steps,
            auto_find_batch_size = auto_find_batch_size,
            logging_strategy = logging_strategy,
            logging_steps = logging_steps,
            logging_first_step = logging_first_step,
            log_on_each_node = log_on_each_node,
            logging_nan_inf_filter = logging_nan_inf_filter,
            include_num_input_tokens_seen = include_num_input_tokens_seen,
            log_level = log_level,
            log_level_replica = log_level_replica,
            disable_tqdm = disable_tqdm,
            report_to = report_to,
            run_name = run_name,
            project = project,
            trackio_space_id = trackio_space_id,
            trackio_bucket_id = trackio_bucket_id,
            trackio_static_space_id = trackio_static_space_id,
            eval_strategy = eval_strategy,
            eval_steps = eval_steps,
            eval_delay = eval_delay,
            per_device_eval_batch_size = per_device_eval_batch_size,
            prediction_loss_only = prediction_loss_only,
            eval_on_start = eval_on_start,
            eval_do_concat_batches = eval_do_concat_batches,
            eval_use_gather_object = eval_use_gather_object,
            eval_accumulation_steps = eval_accumulation_steps,
            batch_eval_metrics = batch_eval_metrics,
            save_only_model = save_only_model,
            save_strategy = save_strategy,
            save_steps = save_steps,
            save_on_each_node = save_on_each_node,
            save_total_limit = save_total_limit,
            enable_jit_checkpoint = enable_jit_checkpoint,
            push_to_hub = push_to_hub,
            hub_token = hub_token,
            hub_private_repo = hub_private_repo,
            hub_model_id = hub_model_id,
            hub_strategy = hub_strategy,
            hub_always_push = hub_always_push,
            hub_revision = hub_revision,
            load_best_model_at_end = load_best_model_at_end,
            metric_for_best_model = metric_for_best_model,
            greater_is_better = greater_is_better,
            ignore_data_skip = ignore_data_skip,
            restore_callback_states_from_checkpoint = restore_callback_states_from_checkpoint,
            full_determinism = full_determinism,
            seed = seed,
            data_seed = data_seed,
            use_cpu = use_cpu,
            accelerator_config = accelerator_config,
            parallelism_config = parallelism_config,
            dataloader_drop_last = dataloader_drop_last,
            dataloader_num_workers = dataloader_num_workers,
            dataloader_pin_memory = dataloader_pin_memory,
            dataloader_persistent_workers = dataloader_persistent_workers,
            dataloader_prefetch_factor = dataloader_prefetch_factor,
            remove_unused_columns = remove_unused_columns,
            label_names = label_names,
            train_sampling_strategy = train_sampling_strategy,
            length_column_name = length_column_name,
            ddp_find_unused_parameters = ddp_find_unused_parameters,
            ddp_bucket_cap_mb = ddp_bucket_cap_mb,
            ddp_broadcast_buffers = ddp_broadcast_buffers,
            ddp_static_graph = ddp_static_graph,
            ddp_backend = ddp_backend,
            ddp_timeout = ddp_timeout,
            fsdp = fsdp,
            fsdp_config = fsdp_config,
            deepspeed = deepspeed,
            debug = debug,
            skip_memory_metrics = skip_memory_metrics,
            do_train = do_train,
            do_eval = do_eval,
            do_predict = do_predict,
            resume_from_checkpoint = resume_from_checkpoint,
            warmup_ratio = warmup_ratio,
            logging_dir = logging_dir,
            local_rank = local_rank,
            model_init_kwargs = model_init_kwargs,
            trust_remote_code = trust_remote_code,
            disable_dropout = disable_dropout,
            dataset_num_proc = dataset_num_proc,
            max_length = max_length,
            pad_to_multiple_of = pad_to_multiple_of,
            precompute_ref_log_probs = precompute_ref_log_probs,
            precompute_ref_batch_size = precompute_ref_batch_size,
            loss_type = loss_type,
            beta = beta,
            desirable_weight = desirable_weight,
            undesirable_weight = undesirable_weight,
            activation_offloading = activation_offloading,
            sync_ref_model = sync_ref_model,
            ref_model_mixup_alpha = ref_model_mixup_alpha,
            ref_model_sync_steps = ref_model_sync_steps,**kwargs)
        self.vllm_sampling_params = vllm_sampling_params
        self.unsloth_num_chunks = unsloth_num_chunks
        if unsloth_grpo_mini_batch is not None:
            if self.generation_batch_size >= unsloth_grpo_mini_batch:
                self.unsloth_grpo_mini_batch = unsloth_grpo_mini_batch
            else:
                raise ValueError(
                    f"Unsloth GRPO mini batch size needs to be less than or equal to the effective generation batch size, "
                    f"which is self.per_device_train_batch_size * gradient_accumulation_steps."
                )
        self.unsloth_logit_chunk_multiplier = unsloth_logit_chunk_multiplier
        self.max_seq_length = max_seq_length
        # Unsloth: Remove use_reentrant=False forced by TRL 0.27.0+
        if getattr(self, 'gradient_checkpointing_kwargs', None) is not None:
            if 'use_reentrant' in self.gradient_checkpointing_kwargs:
                del self.gradient_checkpointing_kwargs['use_reentrant']

pass

class _UnslothKTOTrainer(_BaseTrainer):
    """
    Initialize KTOTrainer.

    Args:
        model (`str` or [`~transformers.PreTrainedModel`] or [`~peft.PeftModel`]):
            Model to be trained. Can be either:

            - A string, being the *model id* of a pretrained model hosted inside a model repo on huggingface.co, or a
              path to a *directory* containing model weights saved using
              [`~transformers.PreTrainedModel.save_pretrained`], e.g., `'./my_model_directory/'`. The model is loaded
              using `<ModelArchitecture>.from_pretrained` (where `<ModelArchitecture>` is derived from the model
              config) with the keyword arguments in `args.model_init_kwargs`.
            - A [`~transformers.PreTrainedModel`] object. Only causal language models are supported.
            - A [`~peft.PeftModel`] object. Only causal language models are supported.
        ref_model ([`~transformers.PreTrainedModel`], *optional*):
            Reference model used to compute the reference log probabilities.

            - If provided, this model is used directly as the reference policy.
            - If `None`, the trainer will automatically use the initial policy corresponding to `model`, i.e. the model
              state before KTO training starts.
        args ([`experimental.kto.KTOConfig`], *optional*):
            Configuration for this trainer. If `None`, a default configuration is used.
        train_dataset ([`~datasets.Dataset`] or [`~datasets.IterableDataset`]):
            The dataset to use for training.
        eval_dataset ([`~datasets.Dataset`], [`~datasets.IterableDataset`] or `dict[str, Dataset | IterableDataset]`):
            The dataset to use for evaluation.
        processing_class ([`~transformers.PreTrainedTokenizerBase`] or [`~transformers.ProcessorMixin`], *optional*):
            Processing class used to process the data. The padding side must be set to "left". If `None`, the
            processing class is loaded from the model's name with [`~transformers.AutoProcessor.from_pretrained`]. A
            padding token, `tokenizer.pad_token`, must be set. If the processing class has not set a padding token,
            `tokenizer.eos_token` will be used as the default.
        data_collator ([`~transformers.DataCollator`], *optional*):
            The data collator to use for training. If None is specified, the default data collator
            ([`~experimental.kto.kto_trainer.DataCollatorForUnpairedPreference`]) will be used which will pad the
            sequences to the maximum length of the sequences in the batch.
        callbacks (`list[transformers.TrainerCallback]`):
            The callbacks to use for training.
        optimizers (`tuple[torch.optim.Optimizer, torch.optim.lr_scheduler.LambdaLR]`):
            The optimizer and scheduler to use for training.
        peft_config ([`~peft.PeftConfig`], *optional*):
            PEFT configuration used to wrap the model. If `None`, the model is not wrapped.
        compute_metrics (`Callable[[EvalPrediction], dict]`, *optional*):
            The function to use to compute the metrics. Must take a `EvalPrediction` and return a dictionary string to
            metric values.
    """

    _tag_names = ["trl", "kto"]
    _name = "KTO"
    _paper = {
        "title": "KTO: Model Alignment as Prospect Theoretic Optimization",
        "id": "2402.01306",
        # docstyle-ignore
        "citation": textwrap.dedent("""\
            @article{ethayarajh2024kto,
                title        = {{KTO: Model Alignment as Prospect Theoretic Optimization}},
                author       = {Kawin Ethayarajh and Winnie Xu and Niklas Muennighoff and Dan Jurafsky and Douwe Kiela},
                year         = 2024,
                eprint       = {arXiv:2402.01306},
            }"""),
    }

    def __init__(
        self,
        model: "str | PreTrainedModel | PeftModel",
        ref_model: PreTrainedModel | None = None,
        args: KTOConfig | None = None,
        train_dataset: Dataset | IterableDataset | None = None,
        eval_dataset: Dataset | IterableDataset | dict[str, Dataset | IterableDataset] | None = None,
        processing_class: PreTrainedTokenizerBase | ProcessorMixin | None = None,
        data_collator: DataCollator | None = None,
        callbacks: list[TrainerCallback] | None = None,
        optimizers: tuple[torch.optim.Optimizer, torch.optim.lr_scheduler.LambdaLR] = (None, None),
        peft_config: "PeftConfig | None" = None,
        compute_metrics: Callable[[EvalLoopOutput], dict] | None = None,
    ):
        # Args
        if args is None:
            model_name = model if isinstance(model, str) else get_config_model_id(model.config)
            model_name = model_name.split("/")[-1]
            args = KTOConfig(f"{model_name}-KTO")

        if train_dataset is None:
            raise ValueError("`train_dataset` is required")
        elif isinstance(train_dataset, IterableDataset):
            # IterableDataset requires dispatch_batches=False because Accelerate's dispatch mode may try to concatenate
            # batches from multiple processes, leading to mismatch errors.
            if args.accelerator_config.dispatch_batches is True:
                logger.warning(
                    "You are using an `IterableDataset` for training with `dispatch_batches=True`. `dispatch_batches` "
                    "is forced to `False` when using an `IterableDataset`. To remove this warning, unset "
                    "`dispatch_batches` in `KTOConfig` or set it to `False`."
                )
            args.accelerator_config.dispatch_batches = False

        # Model
        if isinstance(model, str):
            model_init_kwargs = args.model_init_kwargs or {}
            # Distributed training requires device_map=None ["auto" fails]
            if args.distributed_state.distributed_type in ["MULTI_GPU", "DEEPSPEED"]:
                model_init_kwargs["device_map"] = None
            model_init_kwargs.setdefault("trust_remote_code", args.trust_remote_code)
            model = create_model_from_path(model, **model_init_kwargs)
        else:
            if args.model_init_kwargs is not None:
                logger.warning(
                    "You passed `model_init_kwargs` to the KTOConfig, but your model is already instantiated. "
                    "The `model_init_kwargs` will be ignored."
                )
        # Non-quantized models do not have the `is_loaded_in_{8,4}bit` attributes, whereas quantized models do
        _is_quantized_model = getattr(model, "is_loaded_in_4bit", False) or getattr(model, "is_loaded_in_8bit", False)
        if ref_model is model:
            raise ValueError(
                "`model` and `ref_model` cannot be the same object. In most cases you should omit `ref_model` and "
                "we'll initialize it to a copy of `model` for you."
            )

        # Processing class
        if processing_class is None:
            processing_class = AutoProcessor.from_pretrained(
                get_config_model_id(model.config), trust_remote_code=args.trust_remote_code
            )
        if isinstance(processing_class, ProcessorMixin):
            self._tokenizer = processing_class.tokenizer
            self._is_vlm = True
        elif isinstance(processing_class, PreTrainedTokenizerBase):
            self._tokenizer = processing_class
            self._is_vlm = False
        else:
            raise TypeError("The `processing_class` must be either a `PreTrainedTokenizerBase` or a `ProcessorMixin`")
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # PEFT
        if False:
            if not is_peft_available():
                raise ImportError(
                    "You passed `peft_config` but the `peft` library is not installed. "
                    "Install it with `pip install trl[peft]`."
                )
            if not isinstance(peft_config, PeftConfig):
                raise TypeError(
                    f"`peft_config` must be a `peft.PeftConfig` instance (e.g. `peft.LoraConfig`), "
                    f"got {type(peft_config).__name__}."
                )
            if is_peft_model(model):
                raise ValueError(
                    "You passed a `PeftModel` instance together with a `peft_config` to the trainer. Please first merge "
                    "and unload the existing adapter, save the resulting base model, and then pass that base model along "
                    "with the new `peft_config` to the trainer."
                )
            # Create PEFT model
            # ZeRO-3 + PEFT for non-quantized models:
            # - PEFT's default autocast_adapter_dtype=True upcasts LoRA adapter params to fp32 even when the base model is bf16.
            # - ZeRO-3's _allgather_params_coalesced allocates output buffers using the dtype of the first persistent parameter,
            #   so mixed-dtype persistent_parameters [bf16 base + fp32 LoRA] cause a TypeError on the first optimizer step.
            # - Passing autocast_adapter_dtype=False keeps adapter params in the base model dtype [bf16], fixing the mismatch.
            # - This is safe: the fp32 upcast is a QLoRA-specific concern [low-bit quantized base models], not needed for
            #   non-quantized bf16 training.
            # - See:
            #   - TRL issue: https://github.com/huggingface/trl/issues/6089
            #   - Upstream issue: https://github.com/deepspeedai/DeepSpeed/issues/8072
            # - autocast_adapter_dtype was introduced in PEFT 0.12.0; before, no upcast existed: no need to pass the kwarg
            get_peft_model_kwargs = {}
            if (
                args.deepspeed_plugin is not None
                and args.deepspeed_plugin.zero_stage == 3
                and not _is_quantized_model
                and Version(peft.__version__) >= Version("0.12.0")
            ):
                get_peft_model_kwargs["autocast_adapter_dtype"] = False
            model = get_peft_model(model, peft_config, **get_peft_model_kwargs)

        elif is_peft_model(model) and ref_model is None:
            # If the model is a PEFT model with a pretrained adapter, we need to create a "ref" adapter that is a copy
            # of the "default" adapter, so that we can use it as the reference model during KTO training. PEFT only
            # supports one adapter per model when the LoRA config uses `target_parameters` [see peft#3340], so in that
            # case we skip the "ref" adapter and compute the reference log probs with adapters disabled, i.e. with the
            # base model.
            default_config = model.peft_config["default"]
            if isinstance(default_config, LoraConfig) and default_config.target_parameters:
                logger.warning(
                    "PEFT can't add a frozen reference adapter alongside one that uses `target_parameters` "
                    "(peft#3340], so the reference log probs are computed from the base model [adapters disabled]. "
                    "If you wrapped the model only to apply LoRA, pass a `peft_config` to the trainer instead; if you "
                    "wrapped it deliberately (pretrained adapter or custom init), note that the base model matches "
                    "your adapter only when it's freshly zero-initialized. If it is, this warning is safe to ignore."
                )
            else:
                model.add_adapter("ref", default_config)
                for name, param in model.named_parameters():
                    if ".default." in name:
                        ref_name = name.replace(".default.", ".ref.")
                        ref_param = model.get_parameter(ref_name)
                        ref_param.data.copy_(param.data)

        # When using gradient checkpointing with PEFT, we need to enable input gradients. transformers.Trainer normally
        # handles this, but a bug currently prevents it; see https://github.com/huggingface/transformers/issues/42489
        if is_peft_model(model) and args.gradient_checkpointing:
            model.enable_input_require_grads()

        # When using QLoRA, the PEFT adapter weights are converted to bf16 to follow the recommendations from the
        # original paper [see https://huggingface.co/papers/2305.14314, paragraph 3]. Normally, this can be done by
        # passing `autocast_adapter_dtype=False` to `get_peft_model`, but this option is not yet supported for
        # quantized models. See: https://github.com/huggingface/peft/issues/2889
        if _is_quantized_model:
            for param in model.parameters():
                if param.requires_grad:
                    param.data = param.data.to(torch.bfloat16)

        # Vision dataset detection
        dataset_sample = next(iter(train_dataset))
        self._is_vision_dataset = "image" in dataset_sample or "images" in dataset_sample
        if self._is_vision_dataset and not self._is_vlm:
            raise ValueError(
                "The dataset appears to be vision-related (contains 'image' or 'images' keys), but the provided "
                "model does not seem to be a vision-language model. Please check your model and dataset."
            )
        if self._is_vision_dataset and args.precompute_ref_log_probs:
            raise ValueError(
                "`precompute_ref_log_probs=True` is not supported for vision datasets. For vision-language "
                "models, all data processing is performed on the fly rather than upfront. "
                "Set `precompute_ref_log_probs=False`."
            )
        if self._is_vision_dataset and ("chosen" in dataset_sample or "rejected" in dataset_sample):
            raise ValueError(
                "Vision datasets must be in unpaired format with `completion` and `label` columns. "
                "Paired format (`chosen`/`rejected`) is not supported for vision datasets because "
                "iterating over the full dataset to unpair it would be too expensive for large image "
                "collections. Unpair your dataset first: `dataset = unpair_preference_dataset(dataset)`."
            )

        # Data collator
        calculate_kl = args.loss_type not in ["apo_zero_unpaired"]
        if data_collator is None and not self._is_vision_dataset:
            data_collator = DataCollatorForUnpairedPreference(
                pad_token_id=self._tokenizer.pad_token_id,
                max_length=args.max_length,
                pad_to_multiple_of=args.pad_to_multiple_of,
            )
        elif data_collator is None and self._is_vision_dataset:
            data_collator = DataCollatorForVisionUnpairedPreference(
                processor=processing_class,
                max_length=args.max_length,
                calculate_kl=calculate_kl,
                pad_to_multiple_of=args.pad_to_multiple_of,
            )

        # Training arguments
        self.beta = args.beta
        self.precompute_ref_logps = args.precompute_ref_log_probs
        self.loss_type = args.loss_type
        self.desirable_weight = args.desirable_weight
        self.undesirable_weight = args.undesirable_weight
        self.aux_loss_enabled = getattr(model.config, "output_router_logits", False)
        self.aux_loss_coef = getattr(model.config, "router_aux_loss_coef", 0.0)
        self.calculate_KL = calculate_kl
        if self.calculate_KL and args.train_sampling_strategy != "sequential":
            raise ValueError(
                f"Loss type `'{args.loss_type}'` estimates the KL divergence term and requires "
                f"`train_sampling_strategy='sequential'` because the KL completion for each example is precomputed "
                f"against its neighbors in a fixed-order batch; any other strategy breaks that pairing. "
                f"Got `train_sampling_strategy='{args.train_sampling_strategy}'`."
            )
        if self.calculate_KL and args.per_device_train_batch_size <= 1:
            raise ValueError(
                "Actual (not effective) batch size must be > 1. KTO will not work properly because the KL term will be equivalent to the implied reward."
            )
        if self.aux_loss_enabled and self.aux_loss_coef == 0.0:
            logger.warning(
                "You set `output_router_logits` to `True` in the model config, but `router_aux_loss_coef` is set to "
                "`0.0`, meaning the auxiliary loss will not be used. Either set `router_aux_loss_coef` to a value "
                "greater than `0.0`, or set `output_router_logits` to `False` if you don't want to use the auxiliary "
                "loss.",
            )

        # Dataset
        # Skip dataset preparation for VLMs: tokenization and image processing happen on-the-fly in the collator.
        if not self._is_vision_dataset:
            train_dataset = self._prepare_dataset(train_dataset, processing_class, args, "train")
            if eval_dataset is not None:
                if isinstance(eval_dataset, dict):
                    eval_dataset = {
                        key: self._prepare_dataset(dataset, processing_class, args, key)
                        for key, dataset in eval_dataset.items()
                    }
                else:
                    eval_dataset = self._prepare_dataset(eval_dataset, processing_class, args, "eval")

        # Transformers explicitly set use_reentrant=True in the past to silence a PyTorch warning, but the default was
        # never updated once PyTorch switched to recommending use_reentrant=False. Until that change lands upstream
        # [see https://github.com/huggingface/transformers/pull/43203] and is released [most likely in 5.0.0], we
        # default to the recommended non-reentrant behavior here, while preserving any user-provided value.
        if args.gradient_checkpointing and Version(transformers.__version__) < Version("5.0.0"):
            args.gradient_checkpointing_kwargs = args.gradient_checkpointing_kwargs or {}
            args.gradient_checkpointing_kwargs.setdefault("use_reentrant", False)

        super().__init__(
            model=model,
            args=args,
            data_collator=data_collator,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            processing_class=processing_class,
            compute_metrics=compute_metrics,
            callbacks=callbacks,
            optimizers=optimizers,
        )

        # Initialize activation offloading context
        if self.args.activation_offloading:
            self.maybe_activation_offload_context = get_act_offloading_ctx_manager(model=self.model)
        else:
            self.maybe_activation_offload_context = contextlib.nullcontext()

        # Reference model
        if ref_model is None:
            if is_peft_model(self.model) or args.precompute_ref_log_probs:
                # If PEFT is used, the reference model is not needed since the adapter can be disabled to revert to the
                # initial model. If precompute_ref_log_probs is True, the reference model does not need to be kept in
                # memory during training.
                self.ref_model = None
            else:
                ref_model_init_kwargs = args.model_init_kwargs or {}
                # Distributed training requires device_map=None ["auto" fails]
                if self.args.distributed_state.distributed_type in ["MULTI_GPU", "DEEPSPEED"]:
                    ref_model_init_kwargs["device_map"] = None
                ref_model_init_kwargs.setdefault("trust_remote_code", args.trust_remote_code)
                ref_model_path = get_config_model_id(self.model.config)
                self.ref_model = create_model_from_path(ref_model_path, **ref_model_init_kwargs)
        else:
            self.ref_model = ref_model

        # Disable dropout in the model and reference model
        if args.disable_dropout:
            disable_dropout_in_model(model)
            if self.ref_model is not None:
                disable_dropout_in_model(self.ref_model)

        # Initialize the metrics
        self._metrics = {"train": defaultdict(list), "eval": defaultdict(list)}

        # Gradient accumulation requires scaled loss. Normally, loss scaling in the parent class depends on whether the
        # model accepts loss-related kwargs. Since we compute our own loss, this check is irrelevant. We set
        # self.model_accepts_loss_kwargs to False to enable scaling.
        self.model_accepts_loss_kwargs = False

        # Add tags to the model
        self.model.add_model_tags(self._tag_names)

        if self.ref_model is not None:
            if self.is_deepspeed_enabled:
                self.ref_model = prepare_deepspeed(self.ref_model, self.accelerator)
            elif self.is_fsdp_enabled:
                self.ref_model = prepare_fsdp(self.ref_model, self.accelerator)
            else:
                self.ref_model = self.accelerator.prepare_model(self.ref_model, evaluation_mode=True)

        if args.sync_ref_model:
            if is_peft_model(self.model):
                raise NotImplementedError(
                    "You passed `sync_ref_model=True` while using a PEFT model, which is currently not supported. "
                    "With PEFT, KTOTrainer does not keep a separate reference model in memory; instead, it recovers "
                    "reference behavior by temporarily disabling the adapter. As a result, there is no standalone "
                    "`ref_model` instance to synchronize. Use `sync_ref_model=False`, or opt for full fine-tuning if "
                    "you need a synced reference model. If you need `sync_ref_model` to work with PEFT, please open a "
                    "feature request at https://github.com/huggingface/trl/issues."
                )
            if args.precompute_ref_log_probs:
                raise ValueError(
                    "You cannot use `sync_ref_model=True` together with `precompute_ref_log_probs=True`. "
                    "`precompute_ref_log_probs=True` assumes a fixed reference model, but with `sync_ref_model=True` "
                    "the reference model is periodically updated during training, making any precomputed reference "
                    "log-probs stale. Set `precompute_ref_log_probs=False` or disable `sync_ref_model`."
                )
            self.add_callback(SyncRefModelCallback(ref_model=self.ref_model, accelerator=self.accelerator))

        self.use_liger_kernel = args.use_liger_kernel
        # Import Liger kernel if enabled
        if self.use_liger_kernel:
            if not is_liger_kernel_available():
                raise ImportError(
                    "You set `use_liger_kernel=True` but the liger kernel is not available. "
                    "Please install liger-kernel first: `pip install liger-kernel`"
                )
            if self.loss_type in ["apo_zero_unpaired"]:
                raise ValueError(
                    "You cannot set `loss_type='apo_zero_unpaired'` with liger-kernel."
                    "Only KTO loss is supported with liger-kernel."
                )
            if self.precompute_ref_logps:
                raise ValueError(
                    "You cannot use `precompute_ref_log_probs=True` with liger kernel. Please set "
                    "`precompute_ref_log_probs=False`."
                )
            if is_peft_model(self.model):
                raise ValueError(
                    "You cannot use `use_liger_kernel=True` with Peft models. Please set `use_liger_kernel=False`."
                )
            self.liger_loss_fn = LigerFusedLinearKTOLoss(beta=self.beta, use_ref_model=(self.ref_model is not None))

        if self.precompute_ref_logps:
            if isinstance(self.train_dataset, IterableDataset) or isinstance(
                self.eval_dataset, (IterableDataset, IterableDatasetDict)
            ):
                raise ValueError(
                    "`precompute_ref_log_probs=True` is not supported with IterableDataset. Please use a map-style "
                    "Dataset or set `precompute_ref_log_probs=False`."
                )
            self.train_dataset = self._precompute_ref_logps(
                self.train_dataset,
                "train",
                self.args.precompute_ref_batch_size or self.args.per_device_train_batch_size,
            )
            if self.eval_dataset is not None:
                if isinstance(self.eval_dataset, dict):
                    self.eval_dataset = {
                        name: self._precompute_ref_logps(
                            dataset, name, self.args.precompute_ref_batch_size or self.args.per_device_eval_batch_size
                        )
                        for name, dataset in self.eval_dataset.items()
                    }
                else:
                    self.eval_dataset = self._precompute_ref_logps(
                        self.eval_dataset,
                        "eval",
                        self.args.precompute_ref_batch_size or self.args.per_device_eval_batch_size,
                    )

    def _tokenize(
        self,
        processing_class: PreTrainedTokenizerBase | ProcessorMixin,
        input: str | list,
        **kwargs,
    ) -> dict[str, list]:
        """Tokenize a single example for dataset preprocessing.

        Dispatches to `apply_chat_template` for conversational input (list of message dicts) and to `__call__` for
        non-conversational input (str).

        Args:
            processing_class ([`~transformers.PreTrainedTokenizerBase`] or [`~transformers.ProcessorMixin`]):
                The tokenizer or processor to use.
            input (`str` or `list`):
                A string for non-conversational input, or a list of message dicts for conversational input.
            **kwargs:
                Forwarded to `apply_chat_template` (e.g. `add_generation_prompt`, `return_assistant_tokens_mask`).

        Returns:
            `dict` with at least an `"input_ids"` key mapping to a flat `list[int]`.
        """
        if isinstance(input, list):  # conversational: list of message dicts
            if self._is_vlm:
                input = prepare_multimodal_messages(input)
            result = processing_class.apply_chat_template(input, tokenize=True, return_dict=True, **kwargs)
        else:  # non-conversational: plain text string
            result = processing_class(text=input)
        # VLMs emit a batch dimension even for single examples; unwrap it
        if self._is_vlm:
            return {k: v[0] for k, v in result.items()}
        return result

    def _get_kl_dataset(
        self,
        dataset: Dataset | IterableDataset,
        dataset_name: str,
        args: KTOConfig,
    ) -> Dataset | IterableDataset:
        """
        Creates the KL dataset by creating mismatched (prompt, completion) pairs for KL divergence estimation.

        Args:
            dataset (`Dataset` or `IterableDataset`):
                Tokenized dataset with `prompt_ids` and `completion_ids` columns.
            dataset_name (`str`):
                Name used in progress bar descriptions.
            args ([`KTOConfig`]):
                Training arguments providing `per_device_train_batch_size` and `dataset_num_proc`.

        Returns:
            `Dataset` or `IterableDataset` with a single `KL_completion_ids` column.
        """
        map_kwargs = {}
        if isinstance(dataset, Dataset):  # IterableDataset does not support num_proc or desc
            map_kwargs["num_proc"] = args.dataset_num_proc
            map_kwargs["desc"] = f"Extracting KL {dataset_name} dataset"
        kl_dataset = dataset.map(
            _get_kl_completion_ids, batched=True, batch_size=args.per_device_train_batch_size, **map_kwargs
        )

        def rename_kl_fn(example):
            return {"KL_completion_ids": example["completion_ids"]}

        if isinstance(dataset, Dataset):  # `IterableDataset.map` does not support `desc`
            map_kwargs["desc"] = f"Assembling KL {dataset_name} dataset"
        column_names = get_dataset_column_names(dataset)
        kl_dataset = kl_dataset.map(
            rename_kl_fn,
            remove_columns=[c for c in get_dataset_column_names(kl_dataset) if c in column_names],
            **map_kwargs,
        )
        return kl_dataset

    def _prepare_dataset(
        self,
        dataset: Dataset | IterableDataset,
        processing_class: PreTrainedTokenizerBase | ProcessorMixin,
        args: KTOConfig | None,
        dataset_name: str,
    ) -> Dataset | IterableDataset:
        # Build the kwargs for the `map` function
        map_kwargs = {}
        if isinstance(dataset, Dataset):  # IterableDataset does not support num_proc
            map_kwargs["num_proc"] = args.dataset_num_proc

        # Compute that only on the main process for faster data processing.
        # see: https://github.com/huggingface/trl/pull/1255
        with PartialState().main_process_first():
            # Extract the prompt if needed
            first_example = next(iter(dataset))
            if "prompt" not in first_example:
                if isinstance(dataset, Dataset):  # `IterableDataset.map` does not support `desc`
                    map_kwargs["desc"] = f"Extracting prompt from {dataset_name} dataset"
                dataset = dataset.map(extract_prompt, **map_kwargs)

            # Unpair the dataset if needed
            first_example = next(iter(dataset))
            if "chosen" in first_example and "rejected" in first_example:
                if isinstance(dataset, Dataset):  # `IterableDataset.map` does not support `desc`
                    map_kwargs["desc"] = f"Unpairing {dataset_name} dataset"
                dataset = unpair_preference_dataset(dataset, **map_kwargs)

            # Add EOS token if needed: non-conversational only
            first_example = next(iter(dataset))
            if not is_conversational(first_example):
                if isinstance(dataset, Dataset):  # `IterableDataset.map` does not support `desc`
                    map_kwargs["desc"] = f"Adding EOS to {dataset_name} dataset"

                def add_eos(example, eos_token):
                    if not example["completion"].endswith(eos_token):
                        example["completion"] = example["completion"] + eos_token
                    return example

                dataset = dataset.map(add_eos, fn_kwargs={"eos_token": self._tokenizer.eos_token}, **map_kwargs)

            # Tokenize dataset
            if isinstance(dataset, Dataset):  # `IterableDataset.map` does not support `desc`
                map_kwargs["desc"] = f"Tokenizing {dataset_name} dataset"

            def tokenize_fn(example, processing_class):
                if is_conversational(example):
                    chat_template_kwargs = example.get("chat_template_kwargs", {})
                    prompt_ids = self._tokenize(
                        processing_class,
                        example["prompt"],
                        add_generation_prompt=True,
                        **chat_template_kwargs,
                    )["input_ids"]
                    prompt_completion_ids = self._tokenize(
                        processing_class,
                        example["prompt"] + example["completion"],
                        **chat_template_kwargs,
                    )["input_ids"]
                else:
                    prompt_ids = self._tokenize(processing_class, example["prompt"])["input_ids"]
                    prompt_completion_ids = self._tokenize(
                        processing_class, example["prompt"] + example["completion"]
                    )["input_ids"]

                if not prompt_completion_ids[: len(prompt_ids)] == prompt_ids:
                    logger.warning(
                        "Mismatch between tokenized prompt and the start of tokenized prompt+completion. "
                        "This may be due to unexpected tokenizer behavior, whitespace issues, or special "
                        "token handling. Verify that the tokenizer is processing text consistently."
                    )

                return {
                    "prompt_ids": prompt_ids,
                    "completion_ids": prompt_completion_ids[len(prompt_ids) :],
                }

            dataset = dataset.map(tokenize_fn, fn_kwargs={"processing_class": processing_class}, **map_kwargs)

            # Get KL datasets if needed
            if self.calculate_KL:
                # create pairs for estimating the KL term by flipping the matched pairs in each batch of size total_batch_size
                # i.e., (x_1, y_1), ..., (x_n, y_n) --> (x_1, y_n), ..., (x_n, y_1) = (x'_1, y'_1), ..., (x'_n, y'_n)
                kl_dataset = self._get_kl_dataset(dataset, dataset_name, args)
                dataset = concatenate_datasets([dataset, kl_dataset], axis=1)

            # Calculate dataset desirability balance
            if dataset_name == "train" and isinstance(dataset, Dataset):  # IterableDataset does not support len
                num_desirable = max(sum(dataset["label"]), 1)
                num_undesirable = max(len(dataset["label"]) - num_desirable, 1)  # "label" is binary

                if num_desirable != num_undesirable:
                    # The lower and upper bounds come from Eq. (8) of https://huggingface.co/papers/2402.01306
                    des_weight_lower_bound = round((num_undesirable * self.undesirable_weight / num_desirable) * 1, 2)
                    des_weight_upper_bound = round(
                        (num_undesirable * self.undesirable_weight / num_desirable) * 1.33, 2
                    )
                    und_weight_lower_bound = round((num_desirable * self.desirable_weight / num_undesirable) / 1.33, 2)
                    und_weight_upper_bound = round((num_desirable * self.desirable_weight / num_undesirable) / 1, 2)

                    des_weight_in_range = des_weight_lower_bound <= self.desirable_weight <= des_weight_upper_bound
                    und_weight_in_range = und_weight_lower_bound <= self.undesirable_weight <= und_weight_upper_bound

                    if not (des_weight_in_range or und_weight_in_range):
                        logger.warning(
                            "You have different amounts of desirable/positive and undesirable/negative examples but the "
                            "weights on the desirable and undesirable losses don't seem to be in an ideal range. Based "
                            f"on your data, we recommend EITHER "
                            f"desirable_weight in [{des_weight_lower_bound}, {des_weight_upper_bound}] or "
                            f"undesirable_weight in [{und_weight_lower_bound}, {und_weight_upper_bound}] (but NOT BOTH). "
                            "See the documentation on how to optimally set these weights.",
                        )
        return dataset

    def _set_signature_columns_if_needed(self):
        # If `self.args.remove_unused_columns` is True, non-signature columns are removed.
        # By default, this method sets `self._signature_columns` to the model's expected inputs (usually, "input_ids"
        # and "attention_mask").
        if self._signature_columns is None:
            if self._is_vision_dataset:
                self._signature_columns = [
                    "prompt",
                    "completion",
                    "image",
                    "images",
                    "label",
                    "chat_template_kwargs",
                ]
            else:
                self._signature_columns = [
                    "prompt_ids",
                    "completion_ids",
                    "KL_completion_ids",
                    "label",
                    "ref_logps",
                    "ref_KL_logps",
                ]

    def _get_train_sampler(self, train_dataset: Dataset | None = None) -> Sampler | None:
        if self.calculate_KL and Version(transformers.__version__) < Version("5.2.0"):
            if train_dataset is None:
                train_dataset = self.train_dataset
            if train_dataset is None or not has_length(train_dataset):
                return None
            return SequentialSampler(train_dataset)
        return super()._get_train_sampler(
            train_dataset
        )  # Override training step to add activation offloading context.

    def _precompute_ref_logps(self, dataset: Dataset, name: str, batch_size: int) -> Dataset:
        model_hash = hash_module(self.ref_model or self.model)
        fingerprint = Hasher.hash((dataset._fingerprint, model_hash, self.calculate_KL))
        cache_file = dataset._get_cache_file_path(fingerprint)
        if os.path.exists(cache_file):
            return concatenate_datasets([dataset, Dataset.from_file(cache_file)], axis=1)

        dataloader = DataLoader(
            dataset,
            batch_size=batch_size,
            collate_fn=self.data_collator,
            num_workers=self.args.dataloader_num_workers,
            pin_memory=self.args.dataloader_pin_memory,
            shuffle=False,
        )
        data_loader = self.accelerator.prepare(dataloader)
        ref_logps = []
        ref_KL_logps = []
        for padded_batch in tqdm(iterable=data_loader, desc=f"Computing reference log probs for {name} dataset"):
            ref_logp, ref_KL_logp = self.compute_ref_log_probs(padded_batch)
            if self.calculate_KL:
                ref_logp, ref_KL_logp = self.accelerator.gather_for_metrics((ref_logp, ref_KL_logp))
                ref_KL_logps.append(ref_KL_logp.cpu())
            else:
                ref_logp = self.accelerator.gather_for_metrics(ref_logp)
            ref_logps.append(ref_logp.cpu())

        ref_logps = torch.cat(ref_logps)
        if self.calculate_KL:
            ref_KL_logps = torch.cat(ref_KL_logps)

        if self.accelerator.is_main_process:

            def add_ref_logps(batch, indices):
                result = {"ref_logps": ref_logps[indices]}
                if self.calculate_KL:
                    result.update({"ref_KL_logps": ref_KL_logps[indices]})
                return result

            dataset.map(
                add_ref_logps,
                with_indices=True,
                batched=True,
                remove_columns=dataset.column_names,
                new_fingerprint=fingerprint,
                desc=f"Caching reference log probs for {name} dataset",
            )
        self.accelerator.wait_for_everyone()

        return concatenate_datasets([dataset, Dataset.from_file(cache_file)], axis=1)

    def compute_ref_log_probs(self, inputs):
        """Computes reference log probabilities for a single padded batch."""
        with torch.no_grad(), disable_gradient_checkpointing(self.model, self.args.gradient_checkpointing_kwargs):
            if self.ref_model is None:
                if is_peft_model(self.model):
                    model = self.accelerator.unwrap_model(self.model)
                    with use_adapter(model, adapter_name="ref" if "ref" in model.peft_config else None):
                        completion_logits = self.model(
                            inputs["completion_input_ids"],
                            attention_mask=inputs["completion_attention_mask"],
                        ).logits

                        if self.calculate_KL:
                            KL_logits = self.model(
                                inputs["KL_completion_input_ids"],
                                attention_mask=inputs["KL_completion_attention_mask"],
                            ).logits
                else:
                    completion_logits = self.model(
                        inputs["completion_input_ids"],
                        attention_mask=inputs["completion_attention_mask"],
                    ).logits

                    if self.calculate_KL:
                        KL_logits = self.model(
                            inputs["KL_completion_input_ids"],
                            attention_mask=inputs["KL_completion_attention_mask"],
                        ).logits
            else:
                completion_logits = self.ref_model(
                    inputs["completion_input_ids"], attention_mask=inputs["completion_attention_mask"]
                ).logits

                if self.calculate_KL:
                    KL_logits = self.ref_model(
                        inputs["KL_completion_input_ids"],
                        attention_mask=inputs["KL_completion_attention_mask"],
                    ).logits

        shift_logits = completion_logits[:, :-1, :]
        per_token_logps = selective_log_softmax(shift_logits, inputs["completion_input_ids"][:, 1:])
        per_token_logps[inputs["completion_mask"][:, 1:] == 0] = 0.0
        completion_logps = per_token_logps.sum(-1)

        if self.calculate_KL:
            shift_KL_logits = KL_logits[:, :-1, :]
            KL_per_token_logps = selective_log_softmax(shift_KL_logits, inputs["KL_completion_input_ids"][:, 1:])
            KL_per_token_logps[inputs["KL_completion_mask"][:, 1:] == 0] = 0.0
            KL_logps = KL_per_token_logps.sum(-1)
        else:
            KL_logps = None

        return completion_logps, KL_logps

    def _compute_kl_logps(self, model, batch):
        """Compute KL log probabilities for a given batch."""
        KL_logps = None
        if self.calculate_KL:
            _non_model_keys = {
                "completion_input_ids",
                "completion_attention_mask",
                "completion_mask",
                "KL_completion_mask",
                "KL_completion_token_type_ids",
                "KL_completion_mm_token_type_ids",
                "label",
                "ref_logps",
                "ref_KL_logps",
            }
            KL_model_kwargs = {k: v for k, v in batch.items() if k not in _non_model_keys}
            KL_model_kwargs["input_ids"] = KL_model_kwargs.pop("KL_completion_input_ids")
            KL_model_kwargs["attention_mask"] = KL_model_kwargs.pop("KL_completion_attention_mask")
            # KL sequences have different widths from the main completion after flush_left; override token-type
            # tensors with the KL-specific ones the collator built for exactly this purpose.
            if "KL_completion_token_type_ids" in batch:
                KL_model_kwargs["token_type_ids"] = batch["KL_completion_token_type_ids"]
            if "KL_completion_mm_token_type_ids" in batch:
                KL_model_kwargs["mm_token_type_ids"] = batch["KL_completion_mm_token_type_ids"]

            with torch.no_grad():
                KL_logits = model(**KL_model_kwargs).logits

            shift_KL_logits = KL_logits[:, :-1, :]
            KL_per_token_logps = selective_log_softmax(shift_KL_logits, batch["KL_completion_input_ids"][:, 1:])
            KL_per_token_logps[batch["KL_completion_mask"][:, 1:] == 0] = 0.0
            KL_logps = KL_per_token_logps.sum(-1)
        return KL_logps

    def _compute_loss_liger(self, model, inputs, return_outputs):
        if return_outputs:
            raise RuntimeError(
                "return_outputs=True is not supported with the Liger KTO loss. The Liger loss computes the loss "
                "without materializing logits, so outputs cannot be returned."
            )
        mode = "train" if self.model.training else "eval"
        batch = {k: (v.to(self.accelerator.device) if isinstance(v, torch.Tensor) else v) for k, v in inputs.items()}

        labels = torch.tensor(batch["label"])
        num_chosen = labels.sum().to(self.accelerator.device)
        num_rejected = (len(labels) - num_chosen).to(self.accelerator.device)

        policy_KL_logps = self._compute_kl_logps(model, batch)
        ref_KL_logps = self._compute_kl_logps(self.ref_model, batch)
        if self.calculate_KL:
            kl = (policy_KL_logps - ref_KL_logps).mean().detach()
            kl = self.accelerator.gather_for_metrics(kl).mean().clamp(min=0)
        else:
            kl = torch.zeros(1).to(self.accelerator.device)

        _non_model_keys = {
            "completion_mask",
            "KL_completion_input_ids",
            "KL_completion_attention_mask",
            "KL_completion_mask",
            "KL_completion_token_type_ids",
            "KL_completion_mm_token_type_ids",
            "label",
            "ref_logps",
            "ref_KL_logps",
        }
        model_kwargs = {k: v for k, v in batch.items() if k not in _non_model_keys}
        model_kwargs["input_ids"] = model_kwargs.pop("completion_input_ids")
        model_kwargs["attention_mask"] = model_kwargs.pop("completion_attention_mask")
        model_kwargs["use_cache"] = False
        if self.aux_loss_enabled:
            model_kwargs["output_router_logits"] = True

        # `base_model` gives the inner module (skipping `lm_head`) — text decoder for LMs, multimodal wrapper for
        # VLMs (so vision-token injection runs before the text decoder). `get_decoder()` won't do: on VLMs it
        # returns just the text stack and feeds image-placeholder IDs through it.
        # Pre-5.0 transformers VLMs set `base_model_prefix = ""` so `base_model is self` (re-runs `lm_head`).
        # Fall back to `.model` there.
        if self._is_vlm and Version(transformers.__version__) < Version("5.0.0"):
            backbone, ref_backbone = model.model, self.ref_model.model
        else:
            backbone, ref_backbone = model.base_model, self.ref_model.base_model

        outputs = backbone(**model_kwargs)

        # reference model
        with torch.no_grad(), disable_gradient_checkpointing(self.model, self.args.gradient_checkpointing_kwargs):
            ref_outputs = ref_backbone(**{k: v for k, v in model_kwargs.items() if k != "output_router_logits"})
        lm_head = model.get_output_embeddings()
        ref_lm_head = self.ref_model.get_output_embeddings()

        shift_completion_mask = batch["completion_mask"][:, 1:]
        target = batch["completion_input_ids"][:, 1:].clone()
        target[shift_completion_mask == 0] = -100

        (
            loss,
            (
                chosen_logps_sum,
                rejected_logps_sum,
                chosen_logits_sum,
                rejected_logits_sum,
                chosen_rewards_sum,
                rejected_rewards_sum,
            ),
        ) = self.liger_loss_fn(
            _input=outputs.last_hidden_state[:, :-1],
            lin_weight=lm_head.weight,
            target=target,
            bias=lm_head.bias if hasattr(lm_head, "bias") else None,
            preference_labels=torch.tensor(batch["label"], dtype=torch.bool).to(self.accelerator.device),
            ref_input=ref_outputs.last_hidden_state[:, :-1],
            ref_weight=ref_lm_head.weight,
            ref_bias=ref_lm_head.bias if hasattr(lm_head, "bias") else None,
            kl=kl,
        )
        if self.aux_loss_enabled:
            loss += self.aux_loss_coef * outputs.aux_loss

        self._metrics[mode]["kl"].append(kl.item())

        all_num_chosen = self.accelerator.gather_for_metrics(num_chosen).sum().item()
        all_num_rejected = self.accelerator.gather_for_metrics(num_rejected).sum().item()

        if all_num_chosen > 0:
            self._metrics[mode]["rewards/chosen"].append(
                self.accelerator.gather_for_metrics(chosen_rewards_sum.nansum()).nansum().item() / all_num_chosen
            )
            self._metrics[mode]["logps/chosen"].append(
                self.accelerator.gather_for_metrics(chosen_logps_sum.nansum()).nansum().item() / all_num_chosen
            )
            self._metrics[mode]["logits/chosen"].append(
                self.accelerator.gather_for_metrics(chosen_logits_sum.nansum()).nansum().item() / all_num_chosen
            )

        if all_num_rejected > 0:
            self._metrics[mode]["rewards/rejected"].append(
                self.accelerator.gather_for_metrics(rejected_rewards_sum.nansum()).nansum().item() / all_num_rejected
            )
            self._metrics[mode]["logps/rejected"].append(
                self.accelerator.gather_for_metrics(rejected_logps_sum.nansum()).nansum().item() / all_num_rejected
            )
            self._metrics[mode]["logits/rejected"].append(
                self.accelerator.gather_for_metrics(rejected_logits_sum.nansum()).nansum().item() / all_num_rejected
            )

        if all_num_chosen > 0 and all_num_rejected > 0:
            self._metrics[mode]["rewards/margins"].append(
                self._metrics[mode]["rewards/chosen"][-1] - self._metrics[mode]["rewards/rejected"][-1]
            )

        return loss

    def _compute_loss(self, model, inputs, return_outputs):
        """Compute the KTO loss and other metrics for the given batch of inputs for train or test."""
        mode = "train" if self.model.training else "eval"
        batch = {k: (v.to(self.accelerator.device) if isinstance(v, torch.Tensor) else v) for k, v in inputs.items()}

        labels = torch.tensor(batch["label"])
        num_chosen = labels.sum().to(self.accelerator.device)
        num_rejected = (len(labels) - num_chosen).to(self.accelerator.device)

        policy_KL_logps = self._compute_kl_logps(model, batch)

        _non_model_keys = {
            "completion_mask",
            "KL_completion_input_ids",
            "KL_completion_attention_mask",
            "KL_completion_mask",
            "KL_completion_token_type_ids",
            "KL_completion_mm_token_type_ids",
            "label",
            "ref_logps",
            "ref_KL_logps",
        }
        model_kwargs = {k: v for k, v in batch.items() if k not in _non_model_keys}
        model_kwargs["input_ids"] = model_kwargs.pop("completion_input_ids")
        model_kwargs["attention_mask"] = model_kwargs.pop("completion_attention_mask")
        if self.aux_loss_enabled:
            model_kwargs["output_router_logits"] = True

        outputs = model(**model_kwargs)
        if self.aux_loss_enabled:
            aux_loss = outputs.aux_loss

        shift_logits = outputs.logits[:, :-1, :]
        per_token_logps = selective_log_softmax(shift_logits, batch["completion_input_ids"][:, 1:])
        per_token_logps[batch["completion_mask"][:, 1:] == 0] = 0.0
        completion_logps = per_token_logps.sum(-1)

        if completion_logps.shape[0] != len(batch["label"]):
            raise ValueError(
                "There is a mismatch between the number of examples in this batch and the number of "
                "examples for which an output sequence was predicted."
            )

        device = outputs.logits.device
        bool_labels = torch.as_tensor(batch["label"], dtype=torch.bool, device=device)
        chosen_idx = torch.nonzero(bool_labels, as_tuple=False).view(-1)
        rejected_idx = torch.nonzero(~bool_labels, as_tuple=False).view(-1)

        policy_chosen_logps = completion_logps.index_select(0, chosen_idx)
        policy_rejected_logps = completion_logps.index_select(0, rejected_idx)
        policy_chosen_logits = outputs.logits.index_select(0, chosen_idx)
        policy_rejected_logits = outputs.logits.index_select(0, rejected_idx)

        if self.precompute_ref_logps:
            ref_chosen_logps = batch["ref_logps"].index_select(0, chosen_idx)
            ref_rejected_logps = batch["ref_logps"].index_select(0, rejected_idx)
            if self.calculate_KL:
                ref_KL_logps = batch["ref_KL_logps"]
            else:
                ref_KL_logps = None
        else:
            ref_model_kwargs = {k: v for k, v in model_kwargs.items() if k != "output_router_logits"}
            with torch.no_grad(), disable_gradient_checkpointing(self.model, self.args.gradient_checkpointing_kwargs):
                if is_peft_model(self.model) and self.ref_model is None:
                    ref_model_unwrapped = self.accelerator.unwrap_model(self.model)
                    with use_adapter(
                        ref_model_unwrapped, adapter_name="ref" if "ref" in ref_model_unwrapped.peft_config else None
                    ):
                        ref_KL_logps = self._compute_kl_logps(self.model, batch)
                        ref_outputs = self.model(**ref_model_kwargs)
                else:
                    ref_KL_logps = self._compute_kl_logps(self.ref_model, batch)
                    ref_outputs = self.ref_model(**ref_model_kwargs)
            ref_shift_logits = ref_outputs.logits[:, :-1, :]
            ref_per_token_logps = selective_log_softmax(ref_shift_logits, batch["completion_input_ids"][:, 1:])
            ref_per_token_logps[batch["completion_mask"][:, 1:] == 0] = 0.0
            ref_completion_logps = ref_per_token_logps.sum(-1)
            ref_chosen_logps = ref_completion_logps.index_select(0, chosen_idx)
            ref_rejected_logps = ref_completion_logps.index_select(0, rejected_idx)

        if self.calculate_KL:
            kl = (policy_KL_logps - ref_KL_logps).mean().detach()
            kl = self.accelerator.gather_for_metrics(kl).mean().clamp(min=0)
        else:
            kl = torch.zeros(1).to(policy_chosen_logps.device)
        # Chosen losses
        if policy_chosen_logps.shape[0] != 0 or ref_chosen_logps.shape[0] != 0:
            chosen_logratios = policy_chosen_logps - ref_chosen_logps

            if self.loss_type == "kto":
                # Eqn (7) of the KTO paper (https://huggingface.co/papers/2402.01306)
                chosen_losses = 1 - F.sigmoid(self.beta * (chosen_logratios - kl))
            elif self.loss_type == "apo_zero_unpaired":
                # Unpaired variant of Eqn (7) of the APO paper (https://huggingface.co/papers/2408.06266)
                # Use this loss when you believe the chosen outputs are better than your model's default output
                chosen_losses = 1 - F.sigmoid(self.beta * chosen_logratios)

            chosen_rewards = self.beta * chosen_logratios.detach()

        else:
            # lists can't be empty -- if they are, then accelerate.gather will hang
            chosen_losses = torch.Tensor([]).to(self.accelerator.device)
            chosen_rewards = torch.Tensor([]).to(self.accelerator.device)
        # Rejected losses
        if policy_rejected_logps.shape[0] != 0 or ref_rejected_logps.shape[0] != 0:
            rejected_logratios = policy_rejected_logps - ref_rejected_logps

            if self.loss_type == "kto":
                rejected_losses = 1 - F.sigmoid(self.beta * (kl - rejected_logratios))
            elif self.loss_type == "apo_zero_unpaired":
                rejected_losses = F.sigmoid(self.beta * rejected_logratios)

            rejected_rewards = self.beta * rejected_logratios.detach()
        else:
            # lists can't be empty -- if they are, then accelerate.gather will hang
            rejected_losses = torch.Tensor([]).to(self.accelerator.device)
            rejected_rewards = torch.Tensor([]).to(self.accelerator.device)
        losses = torch.cat(
            (self.desirable_weight * chosen_losses, self.undesirable_weight * rejected_losses),
            0,
        )

        self._metrics[mode]["kl"].append(kl.item())

        all_num_chosen = self.accelerator.gather_for_metrics(num_chosen).sum().item()
        all_num_rejected = self.accelerator.gather_for_metrics(num_rejected).sum().item()

        if all_num_chosen > 0:
            self._metrics[mode]["rewards/chosen"].append(
                self.accelerator.gather_for_metrics(chosen_rewards.nansum()).nansum().item() / all_num_chosen
            )
            self._metrics[mode]["logps/chosen"].append(
                self.accelerator.gather_for_metrics(policy_chosen_logps.nansum()).nansum().item() / all_num_chosen
            )
            self._metrics[mode]["logits/chosen"].append(
                self.accelerator.gather_for_metrics(policy_chosen_logits.nansum()).nansum().item() / all_num_chosen
            )

        if all_num_rejected > 0:
            self._metrics[mode]["rewards/rejected"].append(
                self.accelerator.gather_for_metrics(rejected_rewards.nansum()).nansum().item() / all_num_rejected
            )
            self._metrics[mode]["logps/rejected"].append(
                self.accelerator.gather_for_metrics(policy_rejected_logps.nansum()).nansum().item() / all_num_rejected
            )
            self._metrics[mode]["logits/rejected"].append(
                self.accelerator.gather_for_metrics(policy_rejected_logits.nansum()).nansum().item() / all_num_rejected
            )

        if all_num_chosen > 0 and all_num_rejected > 0:
            self._metrics[mode]["rewards/margins"].append(
                self._metrics[mode]["rewards/chosen"][-1] - self._metrics[mode]["rewards/rejected"][-1]
            )

        loss = losses.nanmean()
        if self.aux_loss_enabled:
            loss += self.aux_loss_coef * aux_loss

        return (loss, outputs) if return_outputs else loss

    def evaluate(
        self,
        eval_dataset: Dataset | dict[str, Dataset] | None = None,
        ignore_keys: list[str] | None = None,
        metric_key_prefix: str = "eval",
    ) -> dict[str, float]:
        # When a dataset is passed directly to `evaluate` (e.g. a held-out test set), preprocess it the same way
        # `__init__` does, so that `evaluate` accepts the same dataset types as the trainer. `_prepare_dataset` is
        # idempotent: it skips datasets that are already tokenized. A `str` selects a dataset that was already prepared
        # at init time, so it's left untouched.
        if not self._is_vision_dataset and eval_dataset is not None and not isinstance(eval_dataset, str):
            if isinstance(eval_dataset, dict):
                eval_dataset = {
                    key: self._prepare_dataset(dataset, self.processing_class, self.args, key)
                    for key, dataset in eval_dataset.items()
                }
            else:
                eval_dataset = self._prepare_dataset(eval_dataset, self.processing_class, self.args, "eval")
            # With `precompute_ref_log_probs`, `_compute_loss` reads the reference log-probs from the batch, so they
            # must be precomputed here as well, mirroring `__init__`.
            if self.precompute_ref_logps:
                batch_size = self.args.precompute_ref_batch_size or self.args.per_device_eval_batch_size
                if isinstance(eval_dataset, dict):
                    eval_dataset = {
                        name: self._precompute_ref_logps(dataset, name, batch_size)
                        for name, dataset in eval_dataset.items()
                    }
                else:
                    eval_dataset = self._precompute_ref_logps(eval_dataset, "eval", batch_size)
        return super().evaluate(
            eval_dataset=eval_dataset, ignore_keys=ignore_keys, metric_key_prefix=metric_key_prefix
        )

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        try:
            if self.use_liger_kernel:
                return self._compute_loss_liger(model, inputs, return_outputs)
            return self._compute_loss(model, inputs, return_outputs)
        except ValueError as e:
            if "Image features and image tokens do not match" in str(e) and self.args.max_length is not None:
                raise ValueError(
                    f"The current `max_length` ({self.args.max_length}) is too short and causes image placeholder "
                    f"tokens in `input_ids` to be truncated, while the corresponding image features remain intact. "
                    f"Please increase `max_length` or set it to `None` to disable truncation."
                ) from e
            raise

    # Override training step to add activation offloading context.
    def training_step(self, *args, **kwargs):
        with self.maybe_activation_offload_context:
            return super().training_step(*args, **kwargs)

    def log(self, logs: dict[str, float], start_time: float | None = None) -> None:
        mode = "train" if self.model.training else "eval"
        metrics = {key: sum(val) / len(val) for key, val in self._metrics[mode].items()}  # average the metrics
        # This method can be called both in training and evaluation. When called in evaluation, the keys in `logs`
        # start with "eval_". We need to add the prefix "eval_" to the keys in `metrics` to match the format.
        if mode == "eval":
            metrics = {f"eval_{key}": val for key, val in metrics.items()}
        logs.update(metrics)
        super().log(logs, start_time)
        self._metrics[mode].clear()

    # During eval, Trainer calls prediction_step. If no labels are present in the inputs, it only runs forward and
    # returns logits. We override prediction_step to force compute_loss, because this trainer doesn't involve labels.
    def prediction_step(self, model, inputs, prediction_loss_only, ignore_keys: list[str] | None = None):
        inputs = self._prepare_inputs(inputs)
        with torch.no_grad(), self.compute_loss_context_manager():
            if prediction_loss_only:
                loss = self.compute_loss(model, inputs, return_outputs=False)  # logits aren't materialized with liger
                logits, labels = None, None
            else:
                loss, outputs = self.compute_loss(model, inputs, return_outputs=True)
                logits, labels = outputs.logits, inputs["completion_input_ids"]
        return loss, logits, labels

    # Ensure the model card is saved along with the checkpoint
    def _save_checkpoint(self, model, trial):
        if self.args.hub_model_id is None:
            model_name = Path(self.args.output_dir).name
        else:
            model_name = self.args.hub_model_id.split("/")[-1]
        self.create_model_card(model_name=model_name)
        super()._save_checkpoint(model, trial)
class UnslothKTOTrainer(_UnslothKTOTrainer):
    """
    KTOTrainer(*args, **kwargs)
    """
    def __init__(
        self,
        model,
        ref_model = None,
        args = None,
        train_dataset = None,
        eval_dataset = None,
        processing_class = None,
        data_collator = None,
        callbacks = None,
        peft_config = None,
        compute_metrics = None,
        **kwargs
    ):
        if args is None: args = UnslothKTOConfig()
        use_bf16 = getattr(args, 'bf16', False)
        if type(use_bf16) is not bool: use_bf16 = False
        use_fp16 = getattr(args, 'fp16', False)
        if type(use_fp16) is not bool: use_fp16 = False
        force_float32 = False
        full_finetuning = os.environ.get('UNSLOTH_ENABLE_FULL_FINETUNING', '0') == '1'
        if not full_finetuning and (os.environ.get('UNSLOTH_FORCE_FLOAT32', '0') == '1'):
            print('Unsloth: Switching to float32 training since model cannot work with float16')
            force_float32 = True
        mixed_precision_dtype = os.environ.get('UNSLOTH_MIXED_PRECISION', 'float32')
        dtype = getattr(model.config, 'dtype', None) or getattr(model.config, 'torch_dtype', None)
        if dtype is None: dtype = model.get_input_embeddings().weight.dtype
        from unsloth_zoo.utils import _get_dtype
        dtype = _get_dtype(dtype)
        float16 = dtype == torch.float16
        if not force_float32 and (float16 and use_bf16): raise TypeError('Unsloth: Model is in float16 precision but you want to use bfloat16 precision. Set fp16 to `True` and bf16 to `False`')
        if not force_float32 and (not float16 and use_fp16): raise TypeError('Unsloth: Model is in bfloat16 precision but you want to use float16 precision. Set fp16 to `False` and bf16 to `True`')
        if force_float32:
            # Forced float32 training
            args.fp16 = False
            args.bf16 = False
            os.environ['ACCELERATE_MIXED_PRECISION'] = 'no'
            if hasattr(args, 'mixed_precision'): args.mixed_precision = 'no'
            # args.mixed_precision is a new argument which needs to be set now
        elif (not use_bf16 and not use_fp16) and mixed_precision_dtype == 'float32':
            # Mixed precision training
            args.fp16 = float16
            args.bf16 = not float16
            os.environ['ACCELERATE_MIXED_PRECISION'] = 'fp16' if float16 else 'bf16'
            if hasattr(args, 'mixed_precision'): args.mixed_precision = 'fp16' if float16 else 'bf16'
            # args.mixed_precision is a new argument which needs to be set now
        elif mixed_precision_dtype == 'bfloat16':
            # Both False since bfloat16 full finetuning doesn't do any autocasting.
            args.fp16 = False
            args.bf16 = False
            os.environ['ACCELERATE_MIXED_PRECISION'] = 'no'
            if hasattr(args, 'mixed_precision'): args.mixed_precision = 'no'
            # args.mixed_precision is a new argument which needs to be set now
        
        if getattr(args, 'eval_dataset', None) is not None and getattr(args, 'eval_strategy', 'no') == 'no':
            args.eval_strategy = 'steps'
            if getattr(args, 'eval_steps', None) is None: args.eval_steps = 0.1
        ga_steps = getattr(args, 'gradient_accumulation_steps', None)
        if ga_steps is not None and ga_steps > 1:
            from transformers import __version__ as transformers_version
            if Version(transformers_version) <= Version('4.45.2'):
                print('**** Unsloth: Please use our fixed gradient_accumulation_steps by updating transformers, TRL and Unsloth!\n'
                      '`pip install --upgrade --no-cache-dir --force-reinstall --no-deps unsloth transformers trl unsloth_zoo`')
        if getattr(args, 'eval_strategy', 'no') != 'no':
            eval_bsz = getattr(args, 'per_device_eval_batch_size', 8)
            if eval_bsz == 8 and args.per_device_train_batch_size < eval_bsz: args.per_device_eval_batch_size = args.per_device_train_batch_size
            if getattr(args, 'eval_accumulation_steps', None) is None and ga_steps is not None: args.eval_accumulation_steps = ga_steps
        fp16_full_eval = getattr(args, 'fp16_full_eval', False)
        if type(fp16_full_eval) is not bool: fp16_full_eval = False
        bf16_full_eval = getattr(args, 'bf16_full_eval', False)
        if type(bf16_full_eval) is not bool: bf16_full_eval = False
        if args.fp16 and bf16_full_eval: args.bf16_full_eval = False; args.fp16_full_eval = True
        if args.bf16 and fp16_full_eval: args.bf16_full_eval = True; args.fp16_full_eval = False
        if force_float32:
            args.bf16_full_eval = False
            args.fp16_full_eval = False
        elif os.environ.get('UNSLOTH_MIXED_PRECISION', 'float32') == 'bfloat16':
            args.bf16_full_eval = True
            args.fp16_full_eval = False
        elif not bf16_full_eval and not fp16_full_eval:
            args.bf16_full_eval = args.bf16
            args.fp16_full_eval = args.fp16
        _output_logits = False
        if locals().get('compute_metrics', None) is not None: _output_logits = True
        if locals().get('preprocess_logits_for_metrics', None) is not None: _output_logits = True
        if _output_logits:
            os.environ['UNSLOTH_RETURN_LOGITS'] = '1'
        if model is not None:
            _warnings_issued = getattr(model, 'warnings_issued', None)
            if _warnings_issued is None:
                model.warnings_issued = {}
            elif not isinstance(_warnings_issued, dict):
                try:
                    model.warnings_issued = dict(_warnings_issued)
                except Exception:
                    model.warnings_issued = {}
        if 'max_seq_length' not in locals() and not hasattr(args, 'max_seq_length'):
            pass
        else:
            model_max_seq_length = getattr(model, 'max_seq_length', None)
            args_max_seq_length  = getattr(args,  'max_seq_length', None)
            if args_max_seq_length is None and model_max_seq_length is not None:
                max_seq_length = model.max_seq_length
                if hasattr(args, 'max_seq_length'): args.max_seq_length = max_seq_length
            elif args_max_seq_length is not None and model_max_seq_length is not None:
                if args_max_seq_length > model_max_seq_length:
                    print('Unsloth: You set `max_seq_length` as ' + str(args_max_seq_length) + ' but '
                           'the maximum the model supports is ' + str(model_max_seq_length) + '. We shall reduce it.')
                    args.max_seq_length = model_max_seq_length
        if model is not None and hasattr(model, 'for_training'):
            model.for_training(use_gradient_checkpointing=getattr(args, 'gradient_checkpointing', True))
        if 'tokenizer' in locals() and hasattr(tokenizer, 'padding_side'): tokenizer.padding_side = 'right'
        if 'processing_class' in locals():
            if hasattr(processing_class, 'padding_side'): processing_class.padding_side = 'right'
            if hasattr(processing_class, 'tokenizer') and hasattr(processing_class.tokenizer, 'padding_side'): processing_class.tokenizer.padding_side = 'right'
        __tokenizer = processing_class if 'processing_class' in locals() else tokenizer
        from unsloth_zoo.vision_utils import UnslothVisionDataCollator
        if not isinstance(data_collator, UnslothVisionDataCollator):
            if isinstance(data_collator, DataCollatorForSeq2Seq) and 'labels' not in train_dataset.column_names:
                data_collator = TransformersDataCollatorForLanguageModeling(
                    __tokenizer,
                    mlm = False,
                    mlm_probability = 0.0,
                    pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),
                )
            elif isinstance(data_collator, TransformersDataCollatorForLanguageModeling) and 'labels' in train_dataset.column_names:
                data_collator = DataCollatorForSeq2Seq(
                    __tokenizer,
                    pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),
                )
        else:
            if hasattr(args, 'remove_unused_columns'): args.remove_unused_columns = False
            if hasattr(args, 'dataset_text_field'): args.dataset_text_field = ''
            if hasattr(args, 'dataset_kwargs'): args.dataset_kwargs = {'skip_prepare_dataset': True}
        if not isinstance(data_collator, UnslothVisionDataCollator):
            if not hasattr(__tokenizer, 'pad') and hasattr(__tokenizer, 'tokenizer'):
                if isinstance(data_collator, DataCollatorForSeq2Seq):
                    data_collator = DataCollatorForSeq2Seq(
                        __tokenizer.tokenizer,
                        pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),
                    )
                elif isinstance(data_collator, TransformersDataCollatorForLanguageModeling):
                    data_collator = TransformersDataCollatorForLanguageModeling(
                        __tokenizer.tokenizer,
                        mlm = False,
                        mlm_probability = 0.0,
                        pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),
                    )
        other_metrics = []
        
        from unsloth_zoo.logging_utils import PatchRLStatistics
        PatchRLStatistics('kto_trainer', other_metrics)
        
        # [TODO] Fix up DataParallel multiplying batch sizes
        # [TODO] DDP works, but DP seems to not work? [TODO]
        if getattr(args, "parallel_mode", None) == ParallelMode.NOT_DISTRIBUTED and args.n_gpu > 1:
            if getattr(args, "_n_gpu", 1) != 1:
                args._n_gpu = 1
        if "model" in locals() and hasattr(model, "for_training"):
            model.for_training(use_gradient_checkpointing=getattr(args, 'gradient_checkpointing', True))
        super().__init__(
            model = model,
            ref_model = ref_model,
            args = args,
            train_dataset = train_dataset,
            eval_dataset = eval_dataset,
            processing_class = processing_class,
            data_collator = data_collator,
            callbacks = callbacks,
            peft_config = peft_config,
            compute_metrics = compute_metrics,**kwargs)
        if "model" in locals() and hasattr(model, "for_inference"):
            model.for_inference()
        if hasattr(self, 'neftune_hook_handle'):
            self.neftune_hook_handle.remove()
            if hasattr(self, 'neftune_hook_handle'): del self.neftune_hook_handle
        if getattr(args, 'neftune_noise_alpha', None) is not None:
            model.get_input_embeddings().neftune_noise_alpha = self.neftune_noise_alpha
        pass
        if hasattr(self, 'accelerator'):
            scaler = self.accelerator.scaler
            current_model = model
            while hasattr(current_model, 'model'):
                current_model.accelerator_scaler = scaler
                current_model = current_model.model
            current_model.accelerator_scaler = scaler
        pass
        if hasattr(self, 'train'):
            self.train = MethodType(prepare_for_training_mode(self.__class__.train), self)
        pass
        if hasattr(self, 'llm') and self.llm is not None and hasattr(self.llm, 'get_tokenizer'):
            _vllm_tok = self.llm.get_tokenizer()
            _pc = getattr(self, 'processing_class', None) or getattr(self, 'tokenizer', None)
            if _vllm_tok is not None and _pc is not None and getattr(_pc, 'chat_template', None) is not None and getattr(_vllm_tok, 'chat_template', None) is None:
                _vllm_tok.chat_template = _pc.chat_template
        pass
        
pass


if hasattr(logger, "addFilter"):
    import logging
    class HideLoggingMessage(logging.Filter):
        def __init__(self, text): self.text = text
        def filter(self, x): return not (self.text in x.getMessage())
    pass
    logger.addFilter(HideLoggingMessage("`use_cache=True`"))

