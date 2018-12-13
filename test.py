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


import torch


class LL(torch.nn.Module):
    def __init__(self):
        super(LL, self).__init__()
        self.w = torch.nn.Parameter(torch.Tensor(10, 10))


if __name__ == '__main__':
    import re
    for x in LL().cuda().parameters():
        print(x.size())
