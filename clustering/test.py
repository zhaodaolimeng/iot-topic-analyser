# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:48:33 2016

@author: limeng
"""

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np



import pickle


raw = pickle.load(open('raw.pickle','rb'))
raw_str = pickle.dumps(raw, 2)

with open("out.pickle", "wb") as text_file:
    text_file.write(raw_str)
    
