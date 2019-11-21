# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:39:29 2019

@author: (Ethan) Yuqiang Heng
"""
import numpy as np
import gym
from gym import spaces
from gym.utils import seeding
from BeamRLUtils import GaussianCenters

h_imag_fname = "H_Matrices FineGrid/MISO_Static_FineGrid_Hmatrices_imag.npy"
h_real_fname = "H_Matrices FineGrid/MISO_Static_FineGrid_Hmatrices_real.npy"
ue_loc_fname = "H_Matrices FineGrid/MISO_Static_FineGrid_UE_location.npy"
IA_rsrp_threshold = 0
n_antenna = 64
oversample_factor = 4

nseg = int(n_antenna*oversample_factor)
#generate array response vectors
bins = np.linspace(-np.pi/2,np.pi/2,nseg+1)
#bins = [(i-nseg/2)*2*np.pi/nseg for i in range(nseg+1)]
#bins = [i*2*np.pi/nseg for i in range(nseg+1)]
bfdirections = [(bins[i]+bins[i+1])/2 for i in range(nseg)]
codebook_all = np.zeros((nseg,n_antenna),dtype=np.complex_)
for i in range(nseg):
    phi = bfdirections[i]
    #array response vector original
    arr_response_vec = [1j*np.pi*k*np.sin(phi) for k in range(n_antenna)]
    #array response vector for rotated ULA
    #arr_response_vec = [1j*np.pi*k*np.sin(phi+np.pi/2) for k in range(64)]
    codebook_all[i,:] = np.exp(arr_response_vec)/np.sqrt(n_antenna)

class InitialAccessEnv(gym.Env):
    
    def _init_(self,
               num_beams_possible: int,
               codebook_size: int):
        self.num_beams_possible = num_beams_possible
        self.codebook_size = codebook_size
        self.action_space = spaces.MultiBinary(codebook_size)
        self.n_ue_per_beam = np.zeros((codebook_size))
        self.true_state = np.zeros((codebook_size))
        self.gaussian_center = GaussianCenters()
        self.h = np.load(h_real_fname) + 1j*np.load(h_imag_fname)
        self.ue_loc = np.load(ue_loc_fname)
#        self.unique_x = np.unique(self.ue_loc[:,0])
#        self.unique_y = np.unique(self.ue_loc[:,1])
        self.codebook_all = codebook_all
        self.IA_thold = 0 
        self.new_UE_idx = 0
        self.existing_UEs = {}
        self.t = 0
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return seed
    
    def step(self, action):
        
        self.t += 1
        
        raise NotImplementedError
    
    def reset(self):
        
        raise NotImplementedError
    
    def beam_association(self, ue_idc:np.array):
        """
        input: 
            ue_h: n_ue x n_antenna array of channel matrices of arriving UEs
        procedure:
            1. find the number of UEs that can achieve IA using each beam in codebook_all -> nvalid_ue_per_beam
            2. store arriving UEs into existing_UEs: ue_idx -> (enter_time, [viable beams])
        
        """
        ue_h = self.h[ue_idc,:] #n_ue x n_antenna channel matrices
        bf_gains = np.matmul(ue_h, np.transpose(self.codebook_all)) #shape n_ue x codebook_size
        nvalid_ue_per_beam = np.sum(bf_gains >= self.IA_thold, axis=0)
        assert len(nvalid_ue_per_beam) == self.codebook_size
        
        ue_store_idc = [self.new_UE_idx+i for i in range(len(ue_idc))]
        self.new_UE_idx += len(ue_idc)
        for i in range(len(ue_idc)):
            self.existing_UEs[ue_store_idc[i]] = (t, [])
        
        raise NotImplementedError
        
    def closest_ue(self, ue_pos:np.array):
        """
        input: 
            ue_loc: lx2 array of x,y coordinates of ues generated from gaussian center
        output:
            lx1 vector of index of ues with ray-traced channels that are closest to the target ues
        """
        #currently calc. l2 distance of all ue data points, can be more efficient
        closest_idx = [np.argmin((self.ue_loc[:,0]-ue_pos[i,0])**2 + (self.ue_loc[:,1]-ue_pos[i,1])**2) for i in range(ue_pos.shape[0])]
        return closest_idx
            
    def gen_arriving_ue(self):
        """
        generate n_ue (from Poisson dist.) new arriving UEs w/. locations (from Gaussian dist.)
        find the closest UE position that has ray-traced channel matrix
        return a n_ue x 1 array of the UE indices
        """
        n_ue, ue_raw_pos = self.gaussian_center.sample() #ue_raw_pos has shape n_ue x 2
        ue_idc = self.closest_ue(ue_raw_pos) #idx of closest ues  
        return ue_idc
             
        

import matplotlib.pyplot as plt
       
if __name__ == "__main__":
    loc = np.load(ue_loc_fname)
    x = loc[:,0]
    y = loc[:,1]
    plt.figure(figsize=(16, 16))
    plt.plot(x,y)
    plt.show()