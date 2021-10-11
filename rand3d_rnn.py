# -*- coding: utf-8 -*-
"""rand3d_rnn.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vOKbVK3iK6wnFpZ_T2lknRGxFf5oxidC
"""

### train rnn
import torch
import time
from torch.autograd import Variable
import numpy as np
import numpy.random as npr
import matplotlib.pyplot as plt

npr.seed(1)
N = 200 #RNN units
S = 24 #input (2 x 12)
R = 1 #readout
B = 1 #batches per epoch
NK = 5 # number of conditions
kmax = 20 # max distance between input patterns
tmin, tmax = 1, 10 # max reaction time

Nepochs = 40000
doplot = True
Nepochsplot = Nepochs / 40 #plot output every certain number of epochs
dt = .1
T = 15
period = 5
NT = int(T/dt)
input_scale = 0.1
dist_scale = 1

lr = .001
sig = 0 #noise in initial state

t = dt*np.arange(NT)

dist = Variable(torch.arange(1, NK + 1, 1), requires_grad=False) * (dist_scale/NK)
tstar = Variable(torch.arange(tmin, tmax + 1, (tmax + 1 - tmin) / NK), requires_grad=False) # linear model
#tstar = (10*torch.sin(2*np.pi*dist) + 20).round()  # sin model

# ***** this is for pre-training; load data from aec here instead of s1 *****

s1 = input_scale * (2 * Variable(torch.rand(int(S/2), B), requires_grad=False).repeat(NT, 1, 1) - 1)   # reference pattern
#ds = input_scale * (2 * Variable(torch.rand(int(S/2), B), requires_grad=False).repeat(NT, 1, 1) - 1)
#s2 = Variable(torch.empty(NK, NT, int(S/2), B), requires_grad=False)
rtarg = Variable(torch.empty(NK, NT, R, B), requires_grad=False)
for i in range(NK):
  #s2[i] = s1 + dist[i] * ds                                                     # pattern to match
  rtarg[i] = Variable(torch.zeros(NT, R, B), requires_grad=False)
  rtarg[i, :int(tstar[i] / dt), 0, 0] = torch.arange(0, 1, dt / tstar[i])       # ramp
  rtarg[i, int(tstar[i] / dt):, 0, 0] = 1                                         # bound

ws0 = np.random.standard_normal([N, S]).astype(np.float32)/np.sqrt(S)
J0 = np.random.standard_normal([N, N]).astype(np.float32)/np.sqrt(N)
wr0 = np.random.standard_normal([R, N]).astype(np.float32)/np.sqrt(N)
b0 = np.zeros([N, 1]).astype(np.float32)

ws = Variable(torch.from_numpy(ws0), requires_grad=True)
J = Variable(torch.from_numpy(J0), requires_grad=True)
wr = Variable(torch.from_numpy(wr0), requires_grad=True)
b = Variable(torch.from_numpy(b0), requires_grad=True)

opt = torch.optim.Adam([J, wr, b, ws], lr=lr)

xinit = 0.01*torch.randn(N, 1)
losslist, losslist2 = [], []
prevt = time.time()
for ei in range(Nepochs):

    print(ei, "\r", end='')
    x = xinit + sig*torch.randn(N, B)
    xa = torch.zeros(NT, N, B) #save the hidden states for each time bin for plotting
    r = torch.zeros(NT, R, B)
    idx = npr.randint(0, NK, size=None)
    ds = input_scale * (2 * Variable(torch.rand(int(S / 2), B), requires_grad=False).repeat(NT, 1, 1) - 1)
    s = torch.cat((s1, s1 + dist[idx] * ds), dim=1)
    #s = torch.cat((s1, s2[idx]), dim=1)

    for ti in range(NT):
        x = x + dt*(-x + torch.tanh(ws.mm(s[ti, :, :]) + J.mm(x) + b))
        xa[ti, :, :] = x
        r[ti, :, :] = wr.mm(x)

    tbound = int(tstar[idx] / dt)
    loss = torch.sum(torch.pow(r[:tbound] - rtarg[idx, :tbound], 2)) / (tbound*B)
    losslist.append(loss.item())
    print('\r' + str(ei + 1) + '/' + str(Nepochs) + '\t Err:' + str(loss.item()), end='')

    #do BPTT
    loss.backward()
    opt.step()
    opt.zero_grad()

    if doplot and (ei == 0 or ei % Nepochsplot == 0 or ei > (Nepochs - 20)):
        if ei < (Nepochs - 20):
            plt.clf()
        #plt.subplot(211)
        plt.plot(rtarg.numpy()[idx, :, 0, 0])
        plt.plot(r.detach().numpy()[:, 0, 0])
        #plt.subplot(212)
        #plt.plot(xa.detach().numpy()[:,:,0])
        plt.pause(0.001) #I had to do this to get the plot to refresh, not sure why
        plt.draw()
print("train time: ", time.time() - prevt)

from scipy.signal import medfilt
p = plt.figure(figsize=(6, 6))
plt.loglog(losslist, color='red')
#plt.loglog(losslist2, color='blue')
ax = plt.gca()
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.xlabel('Training Epoch', fontsize=18)
plt.ylabel('Loss', fontsize=18)
plt.tight_layout()
#p.savefig('rnnloss.png', dpi=200)

dist = Variable(torch.arange(1, NK + 1, 1),requires_grad=False) * (dist_scale/NK)
tstar = Variable(torch.arange(tmin, tmax, (tmax - tmin) / NK),requires_grad=False) # linear model
#tstar = Variable(torch.arange(tmin, tmax, (tmax - tmin) / NK),requires_grad=False)  # sin model