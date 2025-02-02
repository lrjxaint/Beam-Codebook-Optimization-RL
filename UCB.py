# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:07:44 2019

@author: (Ethan) Yuqiang Heng
"""


import numpy as np

class UCB():
    def __init__(self, num_arms:int, scale_factor):
        self.num_arms = num_arms
        self.scale_factor = scale_factor
        self.Nt = np.zeros(self.num_arms)
        self.Qt = np.zeros(self.num_arms)
        self.t = 1
  
    def select_arms(self, k:int):
        chosen = []
        while len(chosen) < k:
            pool = np.setdiff1d(np.arange(self.num_arms),chosen)
            Nt_pool = self.Nt[pool]
            if np.any(Nt_pool==0):
                sel = pool[np.where(Nt_pool==0)[0][0]]
                chosen.append(sel)
            else:
                Qt_pool = self.Qt[pool]
#                ucb_pool = np.divide(Qt_pool,Nt_pool) + np.sqrt(2*np.log(self.t)/Nt_pool)
                ucb_pool = Qt_pool + np.sqrt(3/2*np.log(self.t)/Nt_pool)
                sel = pool[np.argmax(ucb_pool)]
                chosen.append(sel)
        binary_selection = np.zeros(self.num_arms).astype(int)
        binary_selection[chosen] = 1
        return binary_selection
    
    def greedy_select_arms(self, k:int):
        chosen = []
        while len(chosen) < k:
            pool = np.setdiff1d(np.arange(self.num_arms),chosen)
            Nt_pool = self.Nt[pool]
            if np.any(Nt_pool==0):
                sel = pool[np.where(Nt_pool==0)[0][0]]
                chosen.append(sel)
            else:
                Qt_pool = self.Qt[pool]
                sel = pool[np.argmax(Qt_pool)]
                chosen.append(sel)
        binary_selection = np.zeros(self.num_arms).astype(int)
        binary_selection[chosen] = 1
        return binary_selection
  
    def update(self, chosen_arms_multi_binary, rewards_multi_discrete):
        chosen_arms = np.where(chosen_arms_multi_binary)[0]
        rewards = rewards_multi_discrete[chosen_arms]/self.scale_factor
        self.Nt[chosen_arms]+=1
        old_Qt_chosen = self.Qt[chosen_arms]
        self.Qt[chosen_arms] = old_Qt_chosen + np.divide(rewards-old_Qt_chosen, self.Nt[chosen_arms])
        self.t+=1
        return None
    
class Oracle():
    def __init__(self, oversampling_factor = 1, greedy=True):
        self.oversampling_factor = oversampling_factor
        self.n_antenna = 64
        self.n_arms = int(self.oversampling_factor*self.n_antenna)
        self.bfdirections = np.arccos(np.linspace(np.cos(-np.pi/2),np.cos(np.pi/2),self.n_arms))
        self.codebook_all = np.zeros((self.n_arms,self.n_antenna),dtype=np.complex_)
        self.greedy = greedy
        for i in range(self.n_arms):
            phi = self.bfdirections[i]
            arr_response_vec = [-1j*np.pi*k*np.cos(phi) for k in range(self.n_antenna)]
            self.codebook_all[i,:] = np.exp(arr_response_vec)/np.sqrt(self.n_antenna)
        self.codebook_xcorrelation = abs(np.matmul(self.codebook_all, np.transpose(np.conj(self.codebook_all))))**2
        
    def calc_pairwise_coorrelation(self, a, At):
        pairwise_correlation = [self.codebook_xcorrelation[a,i] for i in At]
        return pairwise_correlation

    def incremental_util(self, a, At, s):
        if len(At) == 0:
            raw_utility_vec = np.zeros(self.n_arms)
            pairwise_correlation_all = self.calc_pairwise_coorrelation(a, np.arange(self.n_arms))
            for i in np.arange(self.n_arms):
                raw_utility_vec[i] = abs(pairwise_correlation_all[i]*s[i])
            return sum(raw_utility_vec)
        else:
            unselected = np.setdiff1d(np.arange(self.n_arms),At)
            pairwise_correlation_all = self.calc_pairwise_coorrelation(a, np.arange(self.n_arms))
            raw_utility_vec = np.zeros(self.n_arms)
            for i in unselected:
                correlation_i = sum(self.calc_pairwise_coorrelation(i,At))/len(At)
                raw_utility_vec[i] = abs(pairwise_correlation_all[i]*s[i]*(1-correlation_i))
            return sum(raw_utility_vec)

    def select(self,u:np.array, k:int):
        if self.greedy:
            chosen = []
            for i in range(k):
                pool = np.setdiff1d(np.arange(len(u)),chosen)
                u_pool = u[pool]
                sel = pool[np.argmax(u_pool)]
                chosen.append(sel)
            return chosen    
        else:
            chosen = []
            for i in range(k):
                pool = np.setdiff1d(np.arange(len(u)),chosen)
                increment_utils = [self.incremental_util(a, chosen, u) for a in pool]
                sel = pool[np.argmax(increment_utils)]
                chosen.append(sel)
            return chosen
                    
def oracle(u:np.array, k:int):
    #u: estimated mean of each arm
    #k: number of arms to select
    chosen = []
    for i in range(k):
        pool = np.setdiff1d(np.arange(len(u)),chosen)
        u_pool = u[pool]
        sel = pool[np.argmax(u_pool)]
        chosen.append(sel)
    return chosen

        
class CUCB():
    def __init__(self, num_arms:int, scale_factor):
        self.num_arms = num_arms
        self.scale_factor = scale_factor
        self.Nt = np.zeros(self.num_arms)
        self.Qt = np.zeros(self.num_arms)
        self.t = 1
        self.oracle = Oracle(oversampling_factor = int(num_arms/64), greedy=False)
  
    def select_arms(self, k:int):
        if self.t <= self.num_arms: #initialization steps
            chosen = []
            chosen.append(self.t-1)
            pool = np.setdiff1d(np.arange(self.num_arms),chosen)
            chosen.extend(np.random.choice(pool, k-1, replace=False))
        else:     
            assert(all(self.Nt > 0))
            ucb_all = self.Qt + np.sqrt(3/2*np.log(self.t)/self.Nt)
#            chosen = oracle(ucb_all, k)
            chosen = self.oracle.select(ucb_all,k)
        binary_selection = np.zeros(self.num_arms).astype(int)
        binary_selection[chosen] = 1
        return binary_selection
    
    def greedy_select_arms(self, k:int):
#        chosen = oracle(self.Qt, k)
        chosen = self.oracle.select(self.Qt,k)
        binary_selection = np.zeros(self.num_arms).astype(int)
        binary_selection[chosen] = 1
        return binary_selection
  
    def update(self, chosen_arms_multi_binary, rewards_multi_discrete):
        chosen_arms = np.where(chosen_arms_multi_binary)[0]
        rewards = rewards_multi_discrete[chosen_arms]/self.scale_factor
        self.Nt[chosen_arms]+=1
        old_Qt_chosen = self.Qt[chosen_arms]
        self.Qt[chosen_arms] = old_Qt_chosen + np.divide(rewards-old_Qt_chosen, self.Nt[chosen_arms])
        self.t+=1
        return None
 
import matplotlib.pyplot as plt
from InitialAccessEnv import InitialAccessEnv
from tqdm import tqdm  

def ucb_train_test(max_arr_rate = 10, 
                   n_ssb = 16,
                   oversampling_f = 1,
                   num_train_step = 50, 
                   test_every = 1, 
                   num_test_steps = 50,
                   snr_percentile = 100):
    n_antenna = 64
    codebook_size = oversampling_f*n_antenna
    n_test_steps = int(num_train_step/test_every)
    rewards = np.zeros((n_test_steps,num_test_steps))
    env = InitialAccessEnv(oversampling_factor=oversampling_f,num_beams_possible=n_ssb,snr_thold_percentil = snr_percentile, bandit=True)
    ucb = CUCB(num_arms=codebook_size,scale_factor=max_arr_rate)   
    all_beams = []
    for train_step_idx in tqdm(range(num_train_step)):
#    for train_step_idx in range(num_train_step):
        a_t = ucb.select_arms(n_ssb)
        s_t_1, r_t, done, info = env.step(a_t)
        ucb.update(a_t, s_t_1)
        if train_step_idx % test_every == 0:
            for i in range(num_test_steps):
                a_t = ucb.greedy_select_arms(n_ssb)
                s_t_1, r_t, done, info = env.step(a_t)
                rewards[int(train_step_idx/test_every),i] = r_t
                all_beams.extend(np.where(info["new_arrival"]>0)[0])
    true_usable_beams, true_beam_count = np.unique(all_beams,return_counts=True)
    predicted_beams = np.where(ucb.greedy_select_arms(n_ssb)>0)[0]
    return ucb, rewards, true_usable_beams, true_beam_count, predicted_beams

#if __name__ == "__main__":
#    n_antenna = 64
#    arr_rate = 5
#    n_ssb = 32
#    oversample_f = 4
#    snr_pt = 95
#    n_run = 1
#    n_train = 200
#    test_interval = 10
#    n_test = 10
#    codebook_size = n_antenna*oversample_f
#    all_rewards = np.zeros((n_run, int(n_train/test_interval)))
#    for run_idx in range(n_run):
#        ucb, rewards, true_usable_beams, true_beam_count, predicted_beams = ucb_train_test(max_arr_rate = arr_rate, 
#                                                                                           n_ssb = n_ssb,
#                                                                                           oversampling_f = oversample_f,
#                                                                                           num_train_step = n_train, 
#                                                                                           test_every = test_interval, 
#                                                                                           num_test_steps = n_test,
#                                                                                           snr_percentile = snr_pt)
#        all_rewards[run_idx,:] = rewards.mean(axis=1)
#    y = all_rewards.mean(axis=0)
#    x = np.arange(0,n_train,test_interval)
#    plt.figure(0)
#    plt.plot(x, y)
#    plt.xlabel('number of training steps')
#    plt.ylabel('reward')
##    plt.savefig('CUCB_greedy_training_progress_%dchoose%d_%dp.eps'%(codebook_size,n_ssb,snr_pt), format='eps', dpi=300) 
#    plt.savefig('CUCB_nongreedy_training_progress_%dchoose%d_%dp.eps'%(codebook_size,n_ssb,snr_pt), format='eps', dpi=300)   
    
if __name__ == "__main__":
    n_antenna = 64
    arr_rate = 5
    n_ssb = 32
    oversample_f = 4
    snr_pt = 95
    n_run = 10
    n_train = 100
    test_interval = 5
    n_test = 10
    codebook_size = n_antenna*oversample_f
    all_rewards = np.zeros((n_run, int(n_train/test_interval)))
    for run_idx in range(n_run):
        ucb, rewards, true_usable_beams, true_beam_count, predicted_beams = ucb_train_test(max_arr_rate = arr_rate, 
                                                                                           n_ssb = n_ssb,
                                                                                           oversampling_f = oversample_f,
                                                                                           num_train_step = n_train, 
                                                                                           test_every = test_interval, 
                                                                                           num_test_steps = n_test,
                                                                                           snr_percentile = snr_pt)
        all_rewards[run_idx,:] = rewards.mean(axis=1)
    y = all_rewards.mean(axis=0)
    x = np.arange(0,n_train,test_interval)
    y_max = all_rewards.max(axis = 0)
    y_min = all_rewards.min(axis = 0)
    y_err_asym = [y_min, y_max]
    y_err = all_rewards.max(axis = 0) - all_rewards.min(axis = 0)
    plt.figure(0)
    plt.errorbar(x, y, yerr = y_err_asym)
    plt.xlabel('number of training steps')
    plt.ylabel('reward')
#    plt.savefig('CUCB_greedy_training_progress_%dchoose%d_%dp.eps'%(codebook_size,n_ssb,snr_pt), format='eps', dpi=300) 
    plt.savefig('CUCB_nongreedy_morerun_errbar_training_progress_%dchoose%d_%dp.eps'%(codebook_size,n_ssb,snr_pt), format='eps', dpi=300)   
    
#if __name__ == "__main__":
#    n_antenna = 64
#    arr_rate = 5
#    n_ssb = 32
#    oversample_f = 4
#    snr_pt = 95
#    n_train = 500
#    test_interval = 1
#    n_test = 10
#    codebook_size = n_antenna*oversample_f
#    ucb, rewards, true_usable_beams, true_beam_count, predicted_beams = ucb_train_test(max_arr_rate = arr_rate, 
#                                                                                       n_ssb = n_ssb,
#                                                                                       oversampling_f = oversample_f,
#                                                                                       num_train_step = n_train, 
#                                                                                       test_every = test_interval, 
#                                                                                       num_test_steps = n_test,
#                                                                                       snr_percentile = snr_pt)
#    print(np.setdiff1d(true_usable_beams,predicted_beams))
#    plt.figure(0)
#    plt.plot(rewards.mean(axis=1))
#    print(true_usable_beams)
#    print(predicted_beams)
#    true_beam_dist = np.zeros(codebook_size)
#    true_beam_dist[true_usable_beams] = true_beam_count/sum(true_beam_count)
#    plt.figure(1)
#    plt.bar(np.arange(codebook_size),true_beam_dist)
#    plt.xlabel('beam index')
#    plt.ylabel('frequency')
##    plt.title('true dist of beams')
#    plt.savefig('True_beam_freq_%dchoose%d_%dp.eps'%(codebook_size,n_ssb,snr_pt), format='eps', dpi=300) 
#    plt.figure(2)
#    plt.bar(np.arange(codebook_size),ucb.Qt)
#    plt.xlabel('beam index')
#    plt.ylabel('estimated expected reward')
##    plt.title('UCB estimated reward of beams')     
#    plt.savefig('CUCB_nongreedy_beam_weight_%dchoose%d_%dp.eps'%(codebook_size,n_ssb,snr_pt), format='eps', dpi=300)   

    
#if __name__ == "__main__":
#    max_arr_rate = 20
#    num_run = 1
#    n_ssb = 32
#    oversampling_f = 1
#    codebook_size = oversampling_f*64
#    num_step = 1000
#    all_beams = []
#    all_rewards = np.zeros((num_run,num_step))
#    optimal_rewards = np.zeros((num_run,num_step))
#    regrets = np.zeros((num_run,num_step))
#    for run_idx in range(num_run):
#        print(run_idx)
#        env = InitialAccessEnv(oversampling_factor=oversampling_f,num_beams_possible=n_ssb,snr_thold_percentil = 98,bandit=True)
#        ucb = UCB(num_arms=codebook_size,scale_factor=max_arr_rate)
#        rewards_hist = []
#        optimal_reward_hist = []
#        for step_idx in tqdm(range(num_step)):
#            a_t = ucb.select_arms(n_ssb)
#            s_t_1, r_t, done, info = env.step(a_t)
#            all_beams.extend(np.where(info["new_arrival"]>0)[0])
#            optimal_reward = sum(info["new_arrival"])
#            assert(r_t == sum(s_t_1))
#            ucb.update(a_t, s_t_1)
#            all_rewards[run_idx,step_idx] = r_t
#            optimal_rewards[run_idx,step_idx] = optimal_reward
#            regrets[run_idx,step_idx] = optimal_reward-r_t
##            optimal_reward_hist.append(optimal_reward)
##    plt.plot(all_rewards.mean(axis=0), label = 'rewards')
##    plt.plot(optimal_rewards.mean(axis=0), label = 'optimal rewards')
##    plt.legend()
#    plt.figure(0)
#    plt.plot(regrets.mean(axis=0))
#    plt.title('regret vs nsteps')
#    unique_beams,beam_count = np.unique(all_beams,return_counts=True)
#    beam_count_all = np.zeros(codebook_size)
#    beam_count_all[unique_beams]=beam_count
#    plt.figure(1)
#    plt.bar(np.arange(codebook_size),beam_count_all)
#    plt.title('true dist of beams')
#    plt.figure(2)
#    plt.bar(np.arange(codebook_size),ucb.Qt)
#    plt.title('UCB estimated reward of beams')
#import matplotlib.pyplot as plt
#from InitialAccessEnv import InitialAccessEnv
#from tqdm import tqdm  
#from multiprocessing import Pool
#
#def run_ucb(x):
#    max_arr_rate = 20
#    num_step = 100
#    regret = []
#    env = InitialAccessEnv(bandit=True)
#    ucb = UCB(num_arms=64,scale_factor=max_arr_rate)
#    for step_idx in range(num_step):
#        a_t = ucb.select_arms(32)
#        s_t_1, r_t, done, info = env.step(a_t)
#        optimal_reward = sum(info["new_arrival"])
#        ucb.update(a_t, s_t_1)
#        regret.append(optimal_reward - r_t)
#    return regret
#        
#if __name__ == "__main__":
#    with Pool(processes=25) as pool:
#        results = list(tqdm(pool.imap(run_ucb, range(100)), total=100))
        
#    plt.plot(all_rewards.mean(axis=0), label = 'rewards')
#    plt.plot(optimal_rewards.mean(axis=0), label = 'optimal rewards')
#    plt.legend()
        
        
