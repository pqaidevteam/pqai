import json
from config.config import models_dir


class Dataset():

	def __init__(self, samples):
		self._samples = samples
		self._name = 'Dataset'

	def __getitem__(self, index):
		return self._samples[index]

	def __len__(self):
		return len(self._samples)


class PoC(Dataset):

	file = f'{models_dir}PoC_v0.2.txt'

	def __init__(self):
		super().__init__(self.load())

	def load(self):
		samples = []
		file = open(self.file)
		for line in file:
			[anc, pos, cpc, negs] = json.loads(line.strip())
			sample = {'anc': anc, 'pos': pos, 'negs': negs, 'cpc': cpc}
			samples.append(sample)
		file.close()
		return samples


class AugCPC(Dataset):
	pass
	
