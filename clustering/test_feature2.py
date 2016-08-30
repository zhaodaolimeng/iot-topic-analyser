# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:48:33 2016

@author: limeng
"""

import numpy as np

input0 = [57.82,58.87,54.12,54.33,49.29,42.33,45.63,59.2,53.33,57.48,54.04,65.47,42.31,42.25,69.27,52.9,52.71,49.78,69.99,50.95,42.42,44.54,54.97,57.87,50.77,51.59,52.64,50.35,44.5,44.03,51.12,52.39,54.86,41.44,55.9,48.68,77.04,77.07,76.76,76.54,79.36,78.37,78.12,77.91,76.96,76.81,76.02,79.7,77.56,73.73,76.07,75.49,36.21,32.67,43.92,45.97,53.92,54.69,75.16,51.58,48.05,43.32,51.41,55.96,57.89,52.67,63.89,51.61,45.51,42.92,52.96,64.08,52.83,57.4,67.33,47.56,50.07,44.15,55.77,56,59.43,53.52,55.6,49.74,43.84,43.08,52.38,65.43,54.9,66.52,67.82,52.67,42.15,41.9,56.83,58.09,66.76,67.48,62.95,53.86]
input1 = [57.82,58.87,54.12,54.33,49.29,42.33,45.63,59.2,53.33]

'''
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

widths = np.arange(1, 11)
cwtmatr = signal.cwt(input, signal.ricker, widths)
plt.imshow(cwtmatr, extent=[0, 100, 1, 11], cmap='PRGn', aspect='auto',
           vmax=abs(cwtmatr).max(), vmin=-abs(cwtmatr).max())
plt.show()
'''

from scipy.fftpack import fft
import matplotlib.pyplot as plt

# Number of sample points
y = input1
N = len(y)
# sample spacing
T = 1.0 / 800.0
x = np.linspace(0.0, N*T, N)
yf = fft(y)
xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

plt.plot(xf, 2.0/N * np.abs(yf[0:N/2]))
plt.grid()
plt.show()



'''
import matplotlib.pyplot as plt

# np.histogram(input, bins=np.range(min(input), max(input), 5))
plt.hist(input, bins='auto')  # plt.hist passes it's arguments to np.histogram
plt.title("Histogram with 'auto' bins")
plt.show()
'''
db = DBSCAN(eps=0.3, min_samples=10).fit(X)
core_samples_mask = np.zeros_like(db.labels_, dtype=bool)


