import os
import time
from contextlib import nullcontext
import numpy as np
import torch
from torch.distributed import destroy_process_group
from torch.nn.parallel import DistributedDataParallel as DDP
import pandas as pd
from src.data.dataset_sft import SFTDataset
from src.data.dataset_pretrain import PretrainDataset
import torch.nn.functional as F
from tokenizer_model import ChatGLMTokenizer
from src.share import *
from src.utils import *
from setting import *
import deepspeed

def sft_epoch(epoch,opt,train_loader,optimizer,model_engine,logger):
    iter_per_epoch=len(train_loader)
    start_time=time.time()
    
    start_time=time.time()
    iter_per_epoch=len(train_loader)

    ave_time = []
    for step, (X, Y, loss_mask) in enumerate(train_loader):
        single_time_start=time.time()

        X=X.to(opt.device)
        Y=Y.to(opt.device)
        _, loss, _ = model_engine(X, Y)
        
        # immediately async prefetch next batch while model is doing the forward pass on the GPU
        # backward pass, with gradient scaling if training in fp16
        model_engine.backward(loss)
        model_engine.step()

        single_time_end=time.time()
        ave_time.append(single_time_end - single_time_start)
        if len(ave_time) > 50:
            del(ave_time[0])
        # print(f'model train ave time: {round(mean(ave_time),6)} s')

        #打印日志
        if step % opt.log_interval == 0:
            spend_time=time.time()-start_time
            logger.info(
                    'Epoch:[{}/{}] ({}/{}) loss:{:.3f} lr:{:.7f}  epoch_time: {} min.'.format(
                        epoch,
                        opt.max_epoch, 
                        step, 
                        iter_per_epoch,
                        loss, 
                        optimizer.param_groups[-1]['lr'],
                        spend_time / (step+1) * iter_per_epoch // 60 - spend_time // 60))


def ft_model(opt):
    master_process, ddp_local_rank,ctx= init_ddp(ddp, opt)
    
    if master_process:
        os.makedirs(opt.out_dir, exist_ok=True)

    print(f'**************model_path: {opt.model_path}**************')

    # 并行环境初始化
    ds_config = read_deepspeed_config(opt)
    if master_process:
        print(ds_config)

    #init model
    model=init_model(opt)
    model_path, state_dict, lora_path, lora_state_dict = read_ckpt(opt.model_path)
    load_weight(model, state_dict)
    model.to(opt.device)
    if opt.ft_type == 'lora':
        from src.loralib.utils import mark_only_lora_as_trainable
        mark_only_lora_as_trainable(model)
        
    if master_process:
        model.print_params()

    # optimizer
    optimizer = configure_optimizers(model, opt.weight_decay, opt.learning_rate, 
                                     (opt.beta1, opt.beta2), opt.device, False)
    
    # deepspeed初始化
    deepspeed.init_distributed()
    model_engine, optimizer_engine, _, _ = deepspeed.initialize(
        config=ds_config,
        model=model,
        optimizer=optimizer,
        model_parameters=filter(lambda p: p.requires_grad, model.parameters()),
    )

    # wrap model into DDP container
    if ddp:
        # Ignore the `freqs_cis` buffer so that DDP does not broadcast it at
        # construction time since NCCL does not support `ComplexFloat`
        prefix = "_orig_mod." if opt.compile else ""
        model._ddp_params_and_buffers_to_ignore = {prefix + "freqs_cis"}
        model = DDP(model, device_ids=[ddp_local_rank])
        #
    
    #-----init dataloader------
    tokenizer = ChatGLMTokenizer(vocab_file=opt.vocab_file)

    print(f"====================prepear dataset====================")

    train_ds = SFTDataset(opt.sft_data_path,tokenizer, max_length=opt.max_seq_len)
    if ddp:
        train_sampler = torch.utils.data.distributed.DistributedSampler(train_ds)
    else:
        train_sampler = None
    train_loader = torch.utils.data.DataLoader(
        train_ds,
        batch_size=opt.batch_size,
        pin_memory=False,
        drop_last=False,
        shuffle=False,        
        num_workers=0,
        sampler=train_sampler
    )
    val_ds = PretrainDataset(opt.valid_data_path, max_length=256)
    val_loader = torch.utils.data.DataLoader(
        val_ds,
        batch_size=opt.batch_size,
        pin_memory=False,
        drop_last=False,
        shuffle=False,        
        num_workers=0,
    )

    print(f"====================sft_epoch====================")

    model_save_type = 'lora' if opt.ft_type =='lora' else 'all'

    # sft loop
    best_val_loss = 0.0
    for epoch in range(opt.max_epoch):
        if train_sampler is not None:
            train_sampler.set_epoch(epoch)
    
        sft_epoch(epoch,opt,train_loader,optimizer,model_engine,logger)
        val_loss=valid_epoch(model_engine, val_loader, opt, logger)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            logger.info('best val_loss: {} best_epoch: {} '.format(best_val_loss,epoch))
            if master_process:  #一般用0，当然，可以选任意的rank保存。
                save_path = '{}/pretrain_{}_ft_best_{}.pth'.format(save_dir,model_name.split('.')[0], epoch)
                save_model(model, save_path, model_save_type)

        if master_process:  #一般用0，当然，可以选任意的rank保存。
            save_path = '{}/pretrain_{}_ft_epoch_{}.pth'.format(save_dir,model_name.split('.')[0], epoch)
            save_model(model, save_path, model_save_type)

    if ddp:
        destroy_process_group()

# I/O
if __name__=="__main__":
    opt = get_parser_args()
    
    # 遍历out目录下的所有pretrain文件夹,全部sft处理
    pretrain_list = os.listdir(opt.out_dir)
    for pretrain_model in pretrain_list:
        model_path = os.path.join(opt.out_dir, pretrain_model)
        if 'pretrain' in model_path and os.path.isdir(model_path):
            opt.config = os.path.join(model_path, 'config.yaml')
            opt,config = parser_model_config(opt, is_train=False)

            if opt.ft_type == 'lora':
                save_dir =model_path.replace('pretrain', 'lora_ft_ds')
            else:
                save_dir =model_path.replace('pretrain', 'fft_ds')
            
            if not os.path.exists(save_dir): os.makedirs(save_dir)

            # 保存一份参数
            with open(os.path.join(save_dir,'config.yaml'), "w") as file:
                import yaml
                file.write(yaml.dump(config))

            model_list = os.listdir(model_path)
            for model_ in model_list:
                if model_.endswith('.pth'):
                    opt.model_path = os.path.join(model_path, model_)
                    model_name = model_.split('.')[0]

                    log_dir = os.path.join(save_dir,f'{model_name}_log.log')
                    # if os.path.exists(log_dir):
                    #     os.remove(log_dir) 
                    logger = get_logger(log_dir)

                    ddp = int(os.environ.get("RANK", -1)) != -1  # is this a ddp run?

                    # -----------------------------------------------------------------------------
                    config_keys = [
                        k
                        for k, v in globals().items()
                        if not k.startswith("_") and isinstance(v, (int, float, bool, str))
                    ]
                    # exec(open("configurator.py").read())  # overrides from command line or config file
                    # config = {k: globals()[k] for k in config_keys}  # will be useful for logging
                    # -----------------------------------------------------------------------------
                    opt.batch_size = 2
                    ft_model(opt)
