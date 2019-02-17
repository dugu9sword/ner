import argparse


class ProgramArgs(argparse.Namespace):
    # Never use True/False !
    def __init__(self):
        super(ProgramArgs, self).__init__()
        self.max_span_length = 10
        self.max_sentence_length = 120
        self.char_count_gt = 2
        self.bichar_count_gt = 2

        self.token_type = "rnn"

        self.crf = 0.0

        self.opt_type = "adam"
        self.lr = 0.001
        self.momentum = 0.
        self.lr_epoch = 20
        self.lr_gamma = 0.95

        # embedding settings
        self.char_emb_size = 50
        self.bichar_emb_size = 0
        self.seg_emb_size = 25
        self.pos_emb_size = 25
        self.pos_bmes = 'off'
        self.char_emb_pretrain = "word2vec/lattice_lstm/gigaword_chn.all.a2b.uni.ite50.vec"
        # self.char_emb_pretrain = "word2vec/sgns/sgns.merge.char"
        # self.char_emb_pretrain = "word2vec/fasttext/wiki.zh.vec"
        # self.char_emb_pretrain = "off"

        self.bichar_emb_pretrain = 'off'
        # self.bichar_emb_pretrain = "word2vec/lattice_lstm/gigaword_chn.all.a2b.bi.ite50.vec"

        # transformer config
        self.tfer_num_layer = 2
        self.tfer_num_head = 1
        self.tfer_head_dim = 128

        # rnn config
        self.rnn_num_layer = 2
        self.rnn_hidden = 256

        # fragment encoder
        self.frag_type = "rnn"
        self.frag_fusion = 'cat'
        self.frag_fofe_alpha = 0.5
        self.frag_use_sos = "on"

        # fragment attention
        self.frag_att_type = 'off'
        self.frag_att_head = 2

        # context encoder
        self.ctx_type = 'off'

        self.num_nonlinear = 2

        # lexicon embedding
        self.match_mode = "mix"
        self.match_head = 2     # 1,2,3...: multi-head attention; 0: vanilla attention
        self.match_emb_size = 25
        self.lexicon_emb_pretrain = "word2vec/lattice_lstm/ctb.50d.vec"
        self.lexicon_emb_dim = 50

        # loss
        self.focal_gamma = 0
        self.focal_reduction = "mean"

        # regularization
        self.drop_default = 0.1
        self.drop_segpos = 0.1
        self.drop_token_encoder = 0.1
        # self.drop_frag = 0.1
        self.drop_nonlinear = 0
        self.weight_decay = 1e-5

        self.use_sparse_embed = "on"

        # development config
        self.batch_size = 32
        self.epoch_fix_char_emb = 5
        self.epoch_fix_lexicon_emb = 5
        self.load_from_cache = "on"
        self.train_on = "on"
        self.use_data_set = "thu"
        self.epoch_max = 30
        self.epoch_show_train = 60
        self.model_name = "off"
        self.model_ckpt = -1
        self.check_nan = "off"

    @staticmethod
    def parse(verbose=False) -> "ProgramArgs":
        parser = argparse.ArgumentParser()
        default_args = ProgramArgs()
        for key, value in default_args.__dict__.items():
            if type(value) == bool:
                raise Exception("Bool value is not supported!!!")
            parser.add_argument('--{}'.format(key),
                                action='store',
                                default=value,
                                type=type(value),
                                dest=str(key))
        parsed_args = parser.parse_args(namespace=default_args)
        if verbose:
            print("Args:")
            for key, value in parsed_args.__dict__.items():
                print("\t--{}={}".format(key, value))
        assert isinstance(parsed_args, ProgramArgs)
        return parsed_args  # type: ProgramArgs


config = ProgramArgs.parse(True)
