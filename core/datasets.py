import json
from config.config import models_dir
from core.db import get_patent_data

class PoC:

	def __init__(self):
		self.datapoints = []
		self.file = models_dir + 'PoC_v0.2.txt'
		self.loaded = False

	def load(self):
		"""Load the datapoints from txt file into `self.datapoints`
		
		Returns:
		    bool: True if successfully loaded, else False
		"""
		try:
			with open(self.file, 'r') as file:
				lines = file.read().strip().splitlines()
			for line in lines:
				[pn, cit, cpc, sims] = json.loads(line)
				datapoint = {
					'patent': pn,
					'citation': cit,
					'similars': sims,
					'common_cpc': cpc
				}
				self.datapoints.append(datapoint)
			lines = None
			self.loaded = True
			return True
		except:
			return False

	def __getitem__(self, i):
		"""Get i-th data point.
		
		Args:
		    i (int): Index of the datapoint
		
		Returns:
		    dict: Datapoint
		"""
		if not self.loaded:
			self.load()
		return self.datapoints[i]

	def __len__(self):
		"""Get the number of datapoints in the dataset.
		
		Returns:
		    int: Length of the dataset
		"""
		if not self.loaded:
			self.load()
		return len(self.datapoints)

	def get_datapoint(self, i , fields=[]):
		datapoint = self[i]
		if not fields:
			return datapoint

		pat_data = get_patent_data(datapoint['patent'], only_bib=True)
		cit_data = get_patent_data(datapoint['citation'], only_bib=True)
		sims_data = [get_patent_data(sim, only_bib=True)
						for sim in datapoint['similars']]
		common_cpc = datapoint['common_cpc']

		datapoint = {}
		datapoint['patent'] = {field: pat_data[field] for field in fields}
		datapoint['citation'] = {field: cit_data[field] for field in fields}
		datapoint['similars'] = [{field: sim_data[field]
										for field in fields}
										for sim_data in sims_data]
		datapoint['common_cpc'] = common_cpc
		return datapoint
		
			
	
