from buff import DataSet, create_folder, log, analyze_length_count, analyze_vocab_count
from typing import NamedTuple, List
import re
import math
from collections import defaultdict
import os

usable_data_sets = {"full_train": ("dataset/OntoNotes4/train.char.bmes",
                                   "dataset/OntoNotes4/train.goldseg.bmes",
                                   "dataset/OntoNotes4/dev.char.bmes",
                                   "dataset/OntoNotes4/dev.goldseg.bmes"),
                    "small_train": ("dataset/OntoNotes4/small_train.char.bmes",
                                    "dataset/OntoNotes4/small_train.goldseg.bmes",
                                    "dataset/OntoNotes4/small_train.char.bmes",
                                    "dataset/OntoNotes4/small_train.goldseg.bmes")
                    }


def load_sentences(file_path, sep=r"\s+"):
    ret = []
    sentence = []
    for line in open(file_path, encoding='utf8'):
        line = line.strip("\n")
        if line == "":
            if not sentence == []:
                ret.append(sentence)
                sentence = []
        else:
            sentence.append(re.split(sep, line))
    return ret


SpanLabel = NamedTuple("SpanLabel", [("b", int),
                                     ("e", int),
                                     ("y", int)])
SpanPred = NamedTuple("SpanPred", [("b", int),
                                   ("e", int),
                                   ("pred", int),
                                   ("prob", float)])
Datum = NamedTuple("Datum", [("chars", List[int]),
                             ("bichars", List[int]),
                             ("segs", List[int]),
                             ("labels", List[SpanLabel])])


def load_vocab(vocab_path):
    token2idx = {}
    for line in open(vocab_path, encoding='utf8'):
        split = line.split(" ")
        token2idx[split[0]] = int(split[1])
    idx2token = {v: k for k, v in token2idx.items()}
    return token2idx, idx2token


def gen_vocab(data_path, out_folder,
              char_count_gt=3,
              bichar_count_gt=2,
              use_cache=False):
    if use_cache and os.path.exists(out_folder):
        log("cache for vocab exists.")
        return
    sentences = load_sentences(data_path)

    char_count = defaultdict(lambda: 0)
    bichar_count = defaultdict(lambda: 0)
    ner_labels = []  # BE-*
    for sentence in sentences:
        for line_idx, line in enumerate(sentence):
            char_count[line[0]] += 1
            if line[1] not in ner_labels:
                ner_labels.append(line[1])
            if line_idx < len(sentence) - 1:
                bichar_count[line[0] + sentence[line_idx + 1][0]] += 1
            else:
                bichar_count[line[0] + "<EOS>"] += 1

    char_count = dict(sorted(char_count.items(), key=lambda x: x[1], reverse=True))
    bichar_count = dict(sorted(bichar_count.items(), key=lambda x: x[1], reverse=True))

    # gen char vocab
    char_vocab = {"<PAD>": 0, "<OOV>": 1}
    for i, k in enumerate(char_count.keys()):
        if char_count[k] > char_count_gt:
            char_vocab[k] = len(char_vocab)
    analyze_vocab_count(char_count)

    # gen char vocab
    bichar_vocab = {"<PAD>": 0, "<OOV>": 1}
    for i, k in enumerate(bichar_count.keys()):
        if bichar_count[k] > bichar_count_gt:
            bichar_vocab[k] = len(bichar_vocab)
    analyze_vocab_count(bichar_count)

    # seg vocab
    seg_vocab = {"<PAD>": 0, "B": 1, "M": 2, "E": 3, "S": 4}

    # gen label vocab
    label_vocab = {"NONE": 0}
    for label in ner_labels:
        found = re.search(".*-(.*)", label)
        if found:
            if found.group(1) not in label_vocab:
                label_vocab[found.group(1)] = len(label_vocab)

    # write to file
    create_folder(out_folder)
    for ele in {"char.vocab": char_vocab,
                "bichar.vocab": bichar_vocab,
                "label.vocab": label_vocab,
                "seg.vocab": seg_vocab}.items():
        f_out = open("{}/{}".format(out_folder, ele[0]), "w", encoding='utf8')
        for k, v in ele[1].items():
            f_out.write("{} {}\n".format(k, v))
        f_out.close()


class ConllDataSet(DataSet):

    def __init__(self, ner_path, seg_path,
                 char2idx, bichar2idx, seg2idx, label2idx,
                 max_text_len=math.inf,
                 max_span_len=math.inf,
                 sort_by_length=False):
        super(ConllDataSet, self).__init__()

        ner_sentences = load_sentences(ner_path)
        seg_sentences = load_sentences(seg_path)

        self.__longest_text_len = -1
        self.__longest_span_len = -1

        __span_length_count = defaultdict(lambda: 0)
        __sentence_length_count = defaultdict(lambda: 0)

        for sid in range(len(ner_sentences)):
            chars, bichars, segs, labels = [], [], [], []

            ner_sen = ner_sentences[sid]
            seg_sen = seg_sentences[sid]
            sen_len = len(ner_sen)

            for cid in range(sen_len):
                char = ner_sen[cid][0]
                chars.append(char2idx[char] if char in char2idx else char2idx["<OOV>"])
                __sentence_length_count[len(chars)] += 1

                bichar = char + ner_sen[cid + 1][0] if cid < sen_len - 1 else char + "<EOS>"
                bichars.append(bichar2idx[bichar] if bichar in bichar2idx else bichar2idx["<OOV>"])

                segs.append(seg2idx[seg_sen[cid][1]])

                if re.match(r"^[BS]", ner_sen[cid][1]):
                    state, label = ner_sen[cid][1].split("-")
                    label_b = cid
                    label_e = cid
                    label_y = label2idx[label]
                    if state == 'B':
                        while True:
                            next_state, _ = ner_sen[label_e][1].split("-")
                            if next_state == "E":
                                break
                            label_e += 1
                    if state == 'S':
                        pass

                    __span_length_count[label_e - label_b + 1] += 1
                    if label_e - label_b + 1 <= max_span_len:
                        labels.append(SpanLabel(b=label_b, e=label_e, y=label_y))
                        self.__longest_span_len = max(self.__longest_span_len, label_e - label_b + 1)

            if len(chars) < max_text_len:
                self.data.append(Datum(chars=chars, bichars=bichars, segs=segs, labels=labels))
                self.__longest_text_len = max(self.__longest_text_len, len(chars))

        if sort_by_length:
            self.data = sorted(self.data, key=lambda x: len(x[0]), reverse=True)
        log("Dataset statistics for {}".format(ner_path))
        log("Sentence")
        analyze_length_count(__sentence_length_count)
        log("Span")
        analyze_length_count(__span_length_count)

    @property
    def longest_text_len(self):
        return self.__longest_text_len

    @property
    def longest_span_len(self):
        return self.__longest_span_len
