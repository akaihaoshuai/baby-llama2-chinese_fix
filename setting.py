from argparse import ArgumentParser
import yaml
import json
import math

def get_parser_args(parser=None):
    if parser is None:
        parser = ArgumentParser()
        
    parser.add_argument("--prompt", type=str, default='你好', help="path to config")
    parser.add_argument("--model_config", type=str, default='config/config.yaml', help="path to config")
    parser.add_argument("--train_config", type=str, default='config/train.yaml', help="path to config")
    parser.add_argument("--ds_config", type=str, default='config/deepspeed.json', help="path to config")
    parser.add_argument("--train_data_path", type=list, default=['./data/pretrain_data.bin'], help="path to config")
    parser.add_argument("--valid_data_path", type=list, default=['./data/pretrain_data.bin'], help="path to config")
    parser.add_argument("--test_data_path", type=list, default=['./data/pretrain_data.bin'], help="path to config")
    parser.add_argument("--out_dir", type=str, default='out', help="path to config")
    parser.add_argument("--model_path", type=str, default='best.pth', help="path to config")
    parser.add_argument("--lora_path", type=str, default='', help="")

    # model param
    parser.add_argument("--max_seq_len", type=int, default=1024)
    parser.add_argument("--word_embed_proj_dim", type=int, default=512)
    parser.add_argument("--hidden_size", type=int, default=512)
    parser.add_argument("--n_layers", type=int, default=8)
    parser.add_argument("--n_heads", type=int, default=8)
    parser.add_argument("--n_kv_heads", type=int, default=0, help="0及其以下,则取n_heads的值,为MHQ.为1则是MQA,大于1且小于n_layers则为GQA")
    parser.add_argument("--multiple_of", type=int, default=32)
    parser.add_argument("--rope_beta", type=float, default=10000.0)
    parser.add_argument("--rope_scaling_factor", type=float, default=1.0)
    parser.add_argument("--rope_scaling_type", default="linear", choices=['linear', 'dynamic', 'clex'])
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--use_bias", type=bool, default=True)
    parser.add_argument("--do_layer_norm_before", type=bool, default=True)
    parser.add_argument("--norm_eps", type=float, default=0.00001)
    parser.add_argument("--flash_attention", type=bool, default=False)
    parser.add_argument("--load_in_lowbit", type=int, default=-1, choices=[-1, 2, 3, 4]) 
    parser.add_argument("--load_in_lowbit_groupsize", type=int, default=-1)
    parser.add_argument('--load_in_quant_type', type=str, default="gptq", choices=['gptq', 'llm_int8', 'awq', 'onebit']) # 暂只支持gptq
    parser.add_argument('--act_fn', type=str, default="silu", choices=['silu', 'silu', 'relu', 'gelu_pytorch_tanh', 'gelu_new', 'gelu']) # 暂只支持gptq
    parser.add_argument("--pad_token_id", type=int, default=1)
    parser.add_argument("--bos_token_id", type=int, default=2)
    parser.add_argument("--eos_token_id", type=int, default=2)

    parser.add_argument("--dtype", type=str, default='float16', help="path to config")
    parser.add_argument("--vocab_size", type=int, default=64793)
    parser.add_argument("--vocab_file", type=str, default='./tokenizer_model/chatglm_tokenizer/tokenizer.model', help="path to config")
    parser.add_argument('--architectures', type=str, default="JerryForCausalLM", choices=['JerryForCausalLM'])
    parser.add_argument('--use_shift_short_attn', type=bool, default=False)
    parser.add_argument('--group_size_ratio', type=float, default=0.25)
    parser.add_argument('--use_ssa_min_seq', type=int, default=8192)
    parser.add_argument('--cache_type', type=str, default="recent", choices=['recent', 'all'])
    parser.add_argument('--cache_start_size', type=int, default=10)
    parser.add_argument('--cache_recent_size', type=int, default=2048)
    parser.add_argument("--use_neftune", type=bool, default=True)
    parser.add_argument("--neftune_noise_alpha", type=float, default=0.1)
    
    # finetune
    parser.add_argument("--sft_data_path", type=str, default='./data/sft_data.csv', help="path to config")
    parser.add_argument("--sft_long_data_path_train", type=str, default='./data/sft_data.csv', help="path to config")
    parser.add_argument("--sft_long_data_path_val", type=str, default='./data/sft_data.csv', help="path to config")
    parser.add_argument('--ft_type', type=str, default="full_ft", choices=['full_ft', 'lora', 'dora'])
    parser.add_argument('--lora_mudule', type=str, default="all", choices=['linear', 'embedding', 'all'])
    parser.add_argument("--lora_attn_dim", type=int, default=8)
    parser.add_argument("--lora_attn_alpha", type=int, default=128)
    parser.add_argument("--lora_dropout", type=float, default=0.0)
    parser.add_argument("--lora_r_dropout", type=float, default=0.0)

    parser.add_argument('--merge_lora_to_save', type=bool, default=False, help="merge_lora_to_save")
    parser.add_argument('--merge_lora_on_load', type=bool, default=False, help="merge_lora_on_load")

    # train params
    parser.add_argument("--use_deepspeed", type=bool, default=False)
    parser.add_argument("--max_epoch", type=int, default=2)
    parser.add_argument("--log_iters", type=int, default=200)
    parser.add_argument("--save_iters", type=int, default=1000)
    parser.add_argument("--eval_iters", type=int, default=200)
    parser.add_argument("--eval_only", type=bool, default=False)
    parser.add_argument("--always_save_ckpt", type=bool, default=True)
    parser.add_argument("--init_from", type=str, default='scratch', help="path to config")
    parser.add_argument("--grad_accum_steps", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--learning_rate", type=float, default=3e-4)
    parser.add_argument("--weight_decay", type=float, default=1e-1)
    parser.add_argument("--beta1", type=float, default=0.9)
    parser.add_argument("--beta2", type=float, default=0.95)
    parser.add_argument("--grad_clip", type=float, default=1.0)
    parser.add_argument("--decay_lr", type=bool, default=True)
    parser.add_argument("--warmup_iters", type=int, default=1000)
    parser.add_argument("--lr_decay_iters", type=int, default=80000)
    parser.add_argument('--optimizer_type', type=str, default="AdamW", choices=['AdamW', 'GaLoreAdamW', 'GaLoreAdamW8bit', 'GaLoreAdafactor'])


    # learning rate decay settings
    parser.add_argument("--min_lr", type=float, default=1e-5)
    # DDP settings
    parser.add_argument("--backend", type=str, default='nccl', help="path to config")
    # system
    parser.add_argument("--device", type=str, default='cuda', help="path to config")
    parser.add_argument("--compile", type=bool, default=False)
    parser.add_argument("--local_rank", type=int, default=0)

    # eval
    parser.add_argument("--max_new_tokens", type=int, default=100)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_k", type=int, default=30)
    parser.add_argument("--top_p", type=float, default=0.4)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--shot", type=int, default=0, help='zero shot')


    # ppo
    parser.add_argument("--rw_data_path", type=str, default='./data/hh-rlhf/helpful-base', help="path to config")
    parser.add_argument("--ppo_data_path", type=str, default='./data/ppo_data', help="path to config")
    parser.add_argument("--reward_lm_loss_factor", type=float, default=0.0)
    parser.add_argument("--validation_metric", type=str, default='loss')
    parser.add_argument("--eps", type=float, default=0.000001)
    parser.add_argument("--num_prefetch", type=int, default=32)
    parser.add_argument("--num_workers", type=int, default=1)
    parser.add_argument('--num_rollouts', type=int, default=64, help='nums of samples in current replay buffer')
    parser.add_argument('--critic_lr', type=float, default=15e-7, help='learning rate of critic model')
    parser.add_argument('--reward_clip', type=float, default=10., help='reward clip')
    parser.add_argument('--pg_clip', type=float, default=0.2, help='pg loss clip')
    parser.add_argument('--value_clip', type=float, default=0.2, help='value clip for critic model')
    parser.add_argument('--entropy_clip', type=float, default=35., help='entropy loss clip')
    parser.add_argument('--advantage_clip', type=float, default=0.5, help='clip advantage')
    parser.add_argument('--kl_penalty_weight', type=float, default=0.02, help='kl penalty')
    parser.add_argument('--vf_loss_weight', type=float, default=1., help='vf loss weight')
    parser.add_argument('--entropy_loss_weight', type=float, default=0., help='entropy loss weight')
    parser.add_argument('--ppo_pretrain_loss_weight', type=float, default=0., help='add pretrain loss in PPO training: ppo-rtx')

    # Trick and method options for PPO
    parser.add_argument('--use_reward_clip', action='store_true', help='use reward clip')
    parser.add_argument('--use_reward_scaling', action='store_true', help='use reward scaling')
    parser.add_argument('--use_reward_norm', action='store_true', help='user reward norm')
    parser.add_argument('--use_critic_loss_clip', action='store_true', help='use critic loss clip')
    parser.add_argument('--use_policy_loss_clip', action='store_true', help='use policy loss clip')
    parser.add_argument('--use_advantage_norm', action='store_true', help='use advantage norm')
    parser.add_argument('--use_advantage_clip', action='store_true', help='use advantage clip')
    parser.add_argument('--use_ppo_pretrain_loss', action='store_true', help='use ppo pretrain loss')
    parser.add_argument('--use_entropy_loss', action='store_true', help='use ppo entropy loss')


    # demo
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8898)

    parser.add_argument("--use_tensorboard", type=bool, default=True)

    return parser.parse_args()


def parser_all_config(opt):
    opt, model_config = parser_model_config(opt)
    opt, train_config = parser_train_config(opt)
    return opt, model_config, train_config


def read_config(config_path):
    if config_path.endswith('.yaml'):
        with open(config_path) as f:
            config = yaml.load(f, Loader=yaml.Loader)
    elif config_path.endswith('.json'):
        with open(config_path) as f:
            config = json.load(f)

    return config

def parser_model_config(opt):
    model_config = read_config(opt.model_config)
    
    if None != model_config:
        if model_config.get('max_seq_len') is not None:
            opt.max_seq_len = model_config.get('max_seq_len', opt.max_seq_len)
        elif model_config.get('max_position_embeddings') is not None:
            opt.max_seq_len = model_config.get('max_position_embeddings', opt.max_seq_len)


        opt.word_embed_proj_dim = model_config.get('word_embed_proj_dim', opt.word_embed_proj_dim)
        opt.hidden_size = model_config.get('hidden_size', opt.hidden_size)
        opt.n_layers = model_config.get('n_layers', opt.n_layers)
        opt.n_heads = model_config.get('n_heads', opt.n_heads)
        opt.n_kv_heads = model_config.get('n_kv_heads', opt.n_kv_heads)
        opt.multiple_of = model_config.get('multiple_of', opt.multiple_of)
        opt.rope_beta = model_config.get('rope_beta', opt.rope_beta)
        opt.rope_scaling_factor = model_config.get('rope_scaling_factor', opt.rope_scaling_factor)
        opt.rope_scaling_type = model_config.get('rope_scaling_type', opt.rope_scaling_type)
        opt.dropout = model_config.get('dropout', opt.dropout)
        opt.do_layer_norm_before = model_config.get('do_layer_norm_before', opt.do_layer_norm_before)
        opt.norm_eps = model_config.get('norm_eps', opt.norm_eps)
        opt.use_bias = model_config.get('use_bias', opt.use_bias)
        opt.flash_attention = model_config.get('flash_attention', opt.flash_attention)
        opt.load_in_lowbit = model_config.get('load_in_lowbit', opt.load_in_lowbit)
        opt.load_in_lowbit_groupsize = model_config.get('load_in_lowbit_groupsize', opt.load_in_lowbit_groupsize)
        opt.load_in_quant_type = model_config.get('load_in_quant_type', opt.load_in_quant_type)
        opt.dtype = model_config.get('dtype', opt.dtype)
        opt.act_fn = model_config.get('act_fn', opt.act_fn)
        opt.pad_token_id = model_config.get('pad_token_id', opt.pad_token_id)
        opt.bos_token_id = model_config.get('bos_token_id', opt.bos_token_id)
        opt.eos_token_id = model_config.get('eos_token_id', opt.eos_token_id)
        
        opt.vocab_size = model_config.get('vocab_size', opt.vocab_size)
        opt.vocab_file = model_config.get('vocab_file', opt.vocab_file)
        opt.architectures = model_config.get('architectures', opt.architectures)
        opt.use_neftune = model_config.get('use_neftune', opt.use_neftune)
        opt.neftune_noise_alpha = model_config.get('neftune_noise_alpha', opt.neftune_noise_alpha)
        opt.use_shift_short_attn = model_config.get('use_shift_short_attn', opt.use_shift_short_attn)
        opt.group_size_ratio = model_config.get('group_size_ratio', opt.group_size_ratio)
        opt.use_ssa_min_seq = model_config.get('use_ssa_min_seq', opt.use_ssa_min_seq)
        opt.cache_type = model_config.get('cache_type', opt.cache_type)
        opt.cache_start_size = model_config.get('cache_start_size', opt.cache_start_size)
        opt.cache_recent_size = model_config.get('cache_recent_size', opt.cache_recent_size)

    return opt, model_config

def parser_train_config(opt):
    train_config = read_config(opt.train_config)
    
    dataset_params_yaml = train_config.get('dataset_params')
    if None != dataset_params_yaml:
        opt.train_data_path = dataset_params_yaml.get('train_data_path', opt.train_data_path)
        opt.valid_data_path = dataset_params_yaml.get('valid_data_path', opt.valid_data_path)
        opt.sft_data_path = dataset_params_yaml.get('sft_data_path', opt.sft_data_path)
        opt.sft_long_data_path_train = dataset_params_yaml.get('sft_long_data_path_train', opt.sft_long_data_path_train)
        opt.sft_long_data_path_val = dataset_params_yaml.get('sft_long_data_path_val', opt.sft_long_data_path_val)
        opt.test_data_path = dataset_params_yaml.get('test_data_path', opt.test_data_path)
    
    opt.model_path = train_config.get('model_path',opt.model_path)
    opt.merge_lora_to_save = train_config.get('merge_lora_to_save', opt.merge_lora_to_save)
    opt.merge_lora_on_load = train_config.get('merge_lora_on_load', opt.merge_lora_on_load)

    # train
    train_params_yaml = train_config.get('train_params')
    if None != train_params_yaml:
        opt.use_deepspeed = train_params_yaml.get('use_deepspeed', opt.use_deepspeed)
        opt.max_epoch = train_params_yaml.get('max_epoch', opt.max_epoch)
        opt.log_iters = train_params_yaml.get('log_iters', opt.log_iters)
        opt.save_iters = train_params_yaml.get('save_iters', opt.save_iters)
        opt.eval_iters = train_params_yaml.get('eval_iters', opt.eval_iters)
        opt.eval_only = train_params_yaml.get('eval_only', opt.eval_only)
        opt.always_save_ckpt = train_params_yaml.get('always_save_ckpt', opt.always_save_ckpt)
        opt.init_from = train_params_yaml.get('init_from', opt.init_from)
        opt.grad_accum_steps = train_params_yaml.get('grad_accum_steps', opt.grad_accum_steps)
        opt.batch_size = train_params_yaml.get('batch_size', opt.batch_size)
        opt.learning_rate = train_params_yaml.get('learning_rate', opt.learning_rate)
        opt.weight_decay = train_params_yaml.get('weight_decay', opt.weight_decay)
        opt.beta1 = train_params_yaml.get('beta1', opt.beta1)
        opt.beta2 = train_params_yaml.get('beta2', opt.beta2)
        opt.grad_clip = train_params_yaml.get('grad_clip', opt.grad_clip)
        opt.decay_lr = train_params_yaml.get('decay_lr', opt.decay_lr)
        opt.warmup_iters = train_params_yaml.get('warmup_iters', opt.warmup_iters)
        opt.min_lr = train_params_yaml.get('min_lr', opt.min_lr)
        opt.backend = train_params_yaml.get('backend', opt.backend)
        opt.device = train_params_yaml.get('device', opt.device)
        opt.compile = train_params_yaml.get('compile', opt.compile)
        opt.optimizer_type = train_params_yaml.get('optimizer_type', opt.optimizer_type)

    # fine_tuning_params_yaml = train_config.get('fine_tuning_params')
    # if None != fine_tuning_params_yaml:
    #     opt.ft_type = fine_tuning_params_yaml.get('ft_type', opt.ft_type)
    #     opt.lora_mudule = fine_tuning_params_yaml.get('lora_mudule', opt.lora_mudule)
    #     opt.lora_attn_dim = fine_tuning_params_yaml.get('lora_attn_dim', opt.lora_attn_dim)
    #     opt.lora_attn_alpha = fine_tuning_params_yaml.get('lora_attn_alpha', opt.lora_attn_alpha)
    #     opt.lora_dropout = fine_tuning_params_yaml.get('lora_dropout', opt.lora_dropout)
    #     opt.lora_r_dropout = fine_tuning_params_yaml.get('lora_r_dropout', opt.lora_r_dropout)

    # eval
    eval_params_yaml = train_config.get('eval_params')
    if None != eval_params_yaml:
        opt.max_new_tokens = eval_params_yaml.get('max_new_tokens', opt.max_new_tokens)
        opt.temperature = eval_params_yaml.get('temperature', opt.temperature)
        opt.top_k = eval_params_yaml.get('top_k', opt.top_k)
        opt.top_p = eval_params_yaml.get('top_p', opt.top_p)
        opt.seed = eval_params_yaml.get('seed', opt.seed)
        opt.shot = eval_params_yaml.get('shot', opt.shot)

    ppo_params_yaml = train_config.get('ppo_params')
    if None != ppo_params_yaml:
        opt.rw_data_path = ppo_params_yaml.get('rw_data_path', opt.rw_data_path)
        opt.ppo_data_path = ppo_params_yaml.get('ppo_data_path', opt.ppo_data_path)
        opt.reward_lm_loss_factor = ppo_params_yaml.get('reward_lm_loss_factor', opt.reward_lm_loss_factor)
        opt.validation_metric = ppo_params_yaml.get('validation_metric', opt.validation_metric)
        opt.eps = ppo_params_yaml.get('eps', opt.eps)
        opt.num_prefetch = ppo_params_yaml.get('num_prefetch', opt.num_prefetch)
        opt.num_workers = ppo_params_yaml.get('num_workers', opt.num_workers)
        opt.num_rollouts = ppo_params_yaml.get('num_rollouts', opt.num_rollouts)
        opt.critic_lr = ppo_params_yaml.get('critic_lr', opt.critic_lr)
        opt.reward_clip = ppo_params_yaml.get('reward_clip', opt.reward_clip)
        opt.pg_clip = ppo_params_yaml.get('pg_clip', opt.pg_clip)
        opt.value_clip = ppo_params_yaml.get('value_clip', opt.value_clip)
        opt.entropy_clip = ppo_params_yaml.get('entropy_clip', opt.entropy_clip)
        opt.advantage_clip = ppo_params_yaml.get('advantage_clip', opt.advantage_clip)
        opt.kl_penalty_weight = ppo_params_yaml.get('kl_penalty_weight', opt.kl_penalty_weight)
        opt.vf_loss_weight = ppo_params_yaml.get('vf_loss_weight', opt.vf_loss_weight)
        opt.entropy_loss_weight = ppo_params_yaml.get('entropy_loss_weight', opt.entropy_loss_weight)
        opt.ppo_pretrain_loss_weight = ppo_params_yaml.get('ppo_pretrain_loss_weight', opt.ppo_pretrain_loss_weight)
        opt.use_entropy_loss = ppo_params_yaml.get('use_entropy_loss', opt.use_entropy_loss)
        opt.use_reward_clip = ppo_params_yaml.get('use_reward_clip', opt.use_reward_clip)
        opt.use_reward_scaling = ppo_params_yaml.get('use_reward_scaling', opt.use_reward_scaling)
        opt.use_reward_norm = ppo_params_yaml.get('use_reward_norm', opt.use_reward_norm)
        opt.use_advantage_norm = ppo_params_yaml.get('use_advantage_norm', opt.use_advantage_norm)
        opt.use_advantage_clip = ppo_params_yaml.get('use_advantage_clip', opt.use_advantage_clip)
        opt.use_critic_loss_clip = ppo_params_yaml.get('use_critic_loss_clip', opt.use_critic_loss_clip)
        opt.use_policy_loss_clip = ppo_params_yaml.get('use_policy_loss_clip', opt.use_policy_loss_clip)
        opt.use_ppo_pretrain_loss = ppo_params_yaml.get('use_ppo_pretrain_loss', opt.use_ppo_pretrain_loss)


    return opt, train_config

def set_fine_tuning_paras_to_config(opt, model_config, train_config):
    fine_tuning_params = dict()
    fine_tuning_params['ft_type'] = opt.ft_type
    fine_tuning_params['lora_mudule'] = opt.lora_mudule
    fine_tuning_params['lora_attn_dim'] = opt.lora_attn_dim
    fine_tuning_params['lora_attn_alpha'] = opt.lora_attn_alpha
    fine_tuning_params['lora_dropout'] = opt.lora_dropout
    fine_tuning_params['lora_r_dropout'] = opt.lora_r_dropout
    train_config['fine_tuning_params'] = fine_tuning_params

    if None != model_config:
        orig_rope_scaling_factor = model_config.get('rope_scaling_factor', 1.0)
        ori_max_seq_len = model_config.get('max_seq_len', 1024)
    else:
        orig_rope_scaling_factor = 1.0
        ori_max_seq_len = 1024

    if ori_max_seq_len:
        ori_max_seq_len *= orig_rope_scaling_factor
        if opt.max_seq_len > ori_max_seq_len:
            opt.rope_scaling_factor = float(math.ceil(opt.max_seq_len / ori_max_seq_len))


def read_deepspeed_config(opt):
    ds_config = read_config(opt.ds_config)

    ds_config['optimizer']['params']['lr']=opt.learning_rate
    ds_config['optimizer']['params']['betas'][0]=opt.beta1
    ds_config['optimizer']['params']['betas'][0]=opt.beta2
    ds_config['optimizer']['params']['weight_decay']=opt.weight_decay

    # ds_config['train_batch_size']=opt.batch_size  # 如果设置了grad_accum_steps和train_micro_batch_size_per_gpu，则忽略
    ds_config['train_micro_batch_size_per_gpu']=opt.batch_size  # 不考虑梯度处理
    ds_config['grad_accum_steps']=opt.grad_accum_steps  # 梯度累积

    ds_config['scheduler']['params']['warmup_num_steps']=opt.warmup_iters  # 

    ds_config['steps_per_print']=opt.log_iters  # 
    ds_config['gradient_clipping']=opt.grad_clip  # 

    return ds_config