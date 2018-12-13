from .public import *
import torch
from torch.nn.utils.rnn import PackedSequence

__model_path__ = "saved/models"


def cast_list(array):
    if isinstance(array, torch.Tensor):
        return cast_list(array.detach().cpu().numpy())
    if isinstance(array, list):
        return cast_list(np.array(array))
    if isinstance(array, np.ndarray):
        return array.squeeze().tolist()

def set_gpu_device(device_id):
    torch.cuda.set_device(device_id)


def gpu(*x):
    if torch.cuda.is_available():
        if len(x) == 1:
            return x[0].cuda()
        else:
            return map(lambda m: m.cuda(), x)
    else:
        if len(x) == 1:
            return x[0]
        else:
            return x


def load_model(model, saved_model_name, checkpoint=-1):
    if not os.path.exists(__model_path__):
        os.makedirs(__model_path__, exist_ok=True)
    if checkpoint == -1:
        for file in os.listdir(__model_path__):
            file = file[:-5]
            name = file.split('@')[0]
            ckpt = int(file.split('@')[1])
            if name == saved_model_name and ckpt > checkpoint:
                checkpoint = ckpt
    path = "{}/{}@{}.ckpt".format(__model_path__, saved_model_name, checkpoint)
    if not os.path.exists(path):
        log("Checkpoint not found.")
    else:
        log("Checkpoint found, restoring from {}".format(checkpoint))
        if not torch.cuda.is_available():
            model.load_state_dict(torch.load(path, map_location=lambda storage, loc: storage))
        else:
            model.load_state_dict(torch.load(path))
    return checkpoint


def save_model(model, saved_model_name, checkpoint):
    if not os.path.exists(__model_path__):
        os.makedirs(__model_path__, exist_ok=True)
    if checkpoint == -1:
        checkpoint = 0
    torch.save(model.state_dict(), "{}/{}@{}.ckpt".format(
        __model_path__, saved_model_name, checkpoint))
    return checkpoint + 1


class TimingSaver:
    def __init__(self, model, model_name, seconds, init_ckpt=-1):
        self.model = model
        self.model_name = model_name
        self.seconds = seconds
        self.last_time = time.time()
        self.ckpt = load_model(model=self.model,
                               saved_model_name=self.model_name,
                               checkpoint=init_ckpt)

    def save(self):
        curr_time = time.time()
        if curr_time - self.last_time > self.seconds:
            self.ckpt = save_model(model=self.model,
                                   saved_model_name=self.model_name,
                                   checkpoint=self.ckpt)
            self.last_time = curr_time


def ten2var(x):
    return gpu(torch.autograd.Variable(x))


def long2var(x):
    return gpu(torch.autograd.Variable(torch.LongTensor(x)))


def float2var(x):
    return gpu(torch.autograd.Variable(torch.FloatTensor(x)))


def var2list(x):
    return x.cpu().data.numpy().tolist()


def var2num(x):
    return x.cpu().data[0]


def load_word2vec(embedding: torch.nn.Embedding,
                  word2vec_file,
                  word_dict: Dict[str, int],
                  cached_name=None):
    cache = "{}".format(cached_name)
    if cached_name and exist_var(cache):
        log("Load from cache {}".format(cache))
        pre_word_embedding = load_var(cache)
    else:
        pre_word_embedding = np.random.normal(0, 0.1, size=embedding.weight.size())
        wordvec_file = open(word2vec_file, errors='ignore')
        x = 0
        for line in wordvec_file.readlines():
            x += 1
            log("Process line {} in file {}".format(x, word2vec_file))
            split = line.split(' ')
            if len(split) < 10:
                continue  # for word2vec, the first line is meta info: (NUMBER, SIZE)
            if split[-1] == '\n':
                split = split[:-1]
            word = split[0]
            emb = split[1:]
            if word in word_dict:
                pre_word_embedding[word_dict[word]] = \
                    np.array(list(map(float, emb)))
        save_var(pre_word_embedding, cache)
    embedding.weight.data.copy_(torch.from_numpy(pre_word_embedding))


def reverse_pack_padded_sequence(inputs, lengths, batch_first=False):
    if lengths[-1] <= 0:
        raise ValueError("length of all samples has to be greater than 0, "
                         "but found an element in 'lengths' that is <=0")
    if batch_first:
        inputs = inputs.transpose(0, 1)

    steps = []
    batch_sizes = []
    lengths_iter = reversed(lengths)
    current_length = next(lengths_iter)
    batch_size = inputs.size(1)
    if len(lengths) != batch_size:
        raise ValueError("lengths array has incorrect size")

    for step, step_value in enumerate(inputs, 1):
        steps.append(step_value[:batch_size])
        batch_sizes.append(batch_size)

        while step == current_length:
            try:
                new_length = next(lengths_iter)
            except StopIteration:
                current_length = None
                break

            if current_length > new_length:  # remember that new_length is the preceding length in the array
                raise ValueError("lengths array has to be sorted in decreasing order")
            batch_size -= 1
            current_length = new_length
        if current_length is None:
            break
    return PackedSequence(torch.cat(steps), batch_sizes)