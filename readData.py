# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 10:14:21 2023

@author: wyx
"""

#%% 读取IEEE 33配电网数据
import numpy as np
import pandas as pd
# bigM
bigM = 100
basekV = 12.66
baseMVA = 10
baseI = 789.89
# 节点数据
T_set = np.arange(24)
dT = 1
B_num = 33
B_set = np.arange(33)
# 电压上下限
vmin = 0.9*0.9
vmax = 1.05*1.05
# 支路数据
# line
branchData = pd.read_excel('powerDatanfo.xlsx',sheet_name='Line').values
f = branchData[:, 0].astype('int')
t = branchData[:, 1].astype('int')
branch_num = len(f)
r = branchData[:,2]/(basekV ** 2 / baseMVA)
x = branchData[:,3]/(basekV ** 2 / baseMVA)
branch_ij = list(zip(f,t))
branch_ji = list(zip(t,f))
branch_ij_all = branch_ij+branch_ji
I_ijmax = (500*500)/baseI**2
# r
r_ij = dict(zip(branch_ij,r))
# x
x_ij = dict(zip(branch_ij,x))

# 读取有功无功数据
PData = pd.read_excel('powerData.xlsx',sheet_name='ActiveLoad').values
# activa load
P_in_it = {(i,t):PData[i,t+1]/baseMVA for i in range(B_num) for t in T_set}
# reactive load
QData = pd.read_excel('powerData.xlsx',sheet_name='ReactiveLoad').values
Q_in_it = {(i,t):QData[i,t+1]/baseMVA for i in range(B_num) for t in T_set}

# 读取DG数据
dgData = pd.read_excel('powerData.xlsx',sheet_name='Dg').values
dgNode = dgData[:,1].astype('int')
dgPmax_it = dict(zip(dgNode,dgData[:,2]/baseMVA))
dgPmin_it = dict(zip(dgNode,dgData[:,3]/baseMVA))
dgQmax_it = dict(zip(dgNode,dgData[:,4]/baseMVA))
dgQmin_it = dict(zip(dgNode,dgData[:,5]/baseMVA))
dgSmax_it = dict(zip(dgNode,dgData[:,6]/baseMVA))
comment_set = list(set(B_set)-set(dgNode))
buy_node = [0]
# 节点连接关系
Ninsert_set = {node:branchData[branchData[:,0]==node][:,1].astype('int').tolist() for node in B_set }
Nout_set = {node:branchData[branchData[:,1]==node][:,0].astype('int').tolist() for node in B_set }
N_all_set = {node:branchData[branchData[:,0]==node][:,1].astype('int').tolist()+branchData[branchData[:,1]==node][:,0].astype('int').tolist()for node in B_set}
# # 储能数据
# P_char_max = 0.2/baseMVA
# P_dis_max = 0.2/baseMVA
# eta = 0.9
# N_max = 2

