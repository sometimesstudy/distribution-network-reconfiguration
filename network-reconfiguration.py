# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 19:54:58 2023

@author: wyx
"""
#%% 定义变量
from gurobipy import *
from readData import *
import networkx as nx
model = Model('distflow')
# DG出力
P_dg_it = model.addVars(dgNode,T_set,name='P_dg_it')
Q_dg_it = model.addVars(dgNode,T_set,name='Q_dg_it')
# 外部购电
P_buy_it = model.addVars(buy_node,T_set,lb=-GRB.INFINITY,name='P_buy_it')
Q_buy_it = model.addVars(buy_node,T_set,lb=-GRB.INFINITY,name='Q_buy_it')
# 支路电流
L_ijt = model.addVars(branch_ij,T_set,ub=I_ijmax,name='L_ijt')
# 节点电压
v_it = model.addVars(B_set,T_set,lb=vmin,ub=vmax,name='v_it')
# 支路有功
P_ijt = model.addVars(branch_ij, T_set,lb=-GRB.INFINITY,name='P_ijt')
# 支路无功
Q_ijt = model.addVars(branch_ij, T_set,lb=-GRB.INFINITY,name='Q_ijt')
# 支路开断
alpha_ij = model.addVars(branch_ij,T_set,lb=0,ub=1,name='alpha')
beta_ij = model.addVars(branch_ij,T_set,vtype=GRB.BINARY,name='beta_ij')
beta_ji = model.addVars(branch_ji,T_set,vtype=GRB.BINARY,name='beta_ji')
#%% 约束
# DG出力约束
model.addConstrs((P_dg_it[i,t]<=dgPmax_it[i] for i in dgNode for t in T_set),name='DGPmax')
model.addConstrs((P_dg_it[i,t]>=dgPmin_it[i] for i in dgNode for t in T_set),name='DGPmin')
model.addConstrs((Q_dg_it[i,t]<=dgQmax_it[i] for i in dgNode for t in T_set),name='DGQmax')
model.addConstrs((Q_dg_it[i,t]>=dgQmin_it[i] for i in dgNode for t in T_set),name='DGQmin')
# 潮流方程
# DG节点
model.addConstrs((P_dg_it[i,t]-P_in_it[i,t]==quicksum(P_ijt[i,j,t] for j in Ninsert_set[i])  
                  - quicksum(P_ijt[k,i,t] - r_ij[k,i]*L_ijt[k,i,t] for k in Nout_set[i]) 
                  for t in T_set for i in dgNode ),name='nodePbalance1')
model.addConstrs((Q_dg_it[i,t]-Q_in_it[i,t]==quicksum(Q_ijt[i,j,t] for j in Ninsert_set[i]) 
                  - quicksum(Q_ijt[k,i,t] - x_ij[k,i]*L_ijt[k,i,t]for k in Nout_set[i]) 
                  for t in T_set for i in dgNode ),name='nodeQbalance2')
# 普通节点
model.addConstrs((-P_in_it[i,t]==quicksum(P_ijt[i,j,t] for j in Ninsert_set[i] if (i,j) in branch_ij) 
                  - quicksum(P_ijt[k,i,t] - r_ij[k,i]*L_ijt[k,i,t] for k in Nout_set[i]if (k,i) in branch_ij) 
                  for t in T_set for i in comment_set[1:]) ,name='nodePbalance3')
model.addConstrs((-Q_in_it[i,t]==quicksum(Q_ijt[i,j,t] for j in Ninsert_set[i]) 
                  - quicksum(Q_ijt[k,i,t]- x_ij[k,i]*L_ijt[k,i,t] for k in Nout_set[i]) 
                  for t in T_set for i in comment_set[1:]),name='nodeQbalance4')
# 对外购电
model.addConstrs((P_buy_it[i,t]-P_in_it[i,t]==quicksum(P_ijt[i,j,t] for j in Ninsert_set[i])  
                  - quicksum(P_ijt[k,i,t]- r_ij[k,i]*L_ijt[k,i,t] for k in Nout_set[i]) 
                  for t in T_set for i in buy_node ),name='firstnode1')
model.addConstrs((Q_buy_it[i,t]-P_in_it[i,t]==quicksum(Q_ijt[i,j,t] for j in Ninsert_set[i])  
                  - quicksum(Q_ijt[k,i,t] - x_ij[k,i]*L_ijt[k,i,t] for k in Nout_set[i]) 
                  for t in T_set for i in buy_node ),name='firstnode2')
# 电压约束
model.addConstrs((v_it[j,t]<=bigM*(1-alpha_ij[i,j,t])+v_it[i,t]-2*(r_ij[i,j]*P_ijt[i,j,t]
                +x_ij[i,j]*Q_ijt[i,j,t]+(r_ij[i,j]**2+x_ij[i,j]**2)*L_ijt[i,j,t] ) for (i,j) in 
                  branch_ij for t in T_set),name='V-2')
model.addConstrs((v_it[j,t]>=-bigM*(1-alpha_ij[i,j,t])+v_it[i,t]-2*(r_ij[i,j]*P_ijt[i,j,t]
                +x_ij[i,j]*Q_ijt[i,j,t]+(r_ij[i,j]**2+x_ij[i,j]**2)*L_ijt[i,j,t] ) for (i,j) in 
                  branch_ij for t in T_set),name='V-3')
model.addConstrs((v_it[0,t]==1 for t in T_set),name='balancenode')
# 电流约束
model.addConstrs((L_ijt[i,j,t]*v_it[i,t]>=(P_ijt[i,j,t]**2+Q_ijt[i,j,t]**2) for (i,j) in branch_ij
                  for t in T_set),name='SOC')
model.addConstrs((L_ijt[i,j,t]<=alpha_ij[i,j,t]*I_ijmax for (i,j) in branch_ij for t in T_set),name='Iconstrs')
# 辐射网约束
model.addConstrs((quicksum(alpha_ij[i,j,t] for (i,j) in branch_ij) ==B_num-1 for t in T_set),name='radical-1')
model.addConstrs((beta_ij[i,j,t]+beta_ji[j,i,t]==alpha_ij[i,j,t] for (i,j) in branch_ij for t in T_set),name='radical-2')
model.addConstrs((quicksum(beta_ij[j,i,t] for j in Nout_set[i])==1 for i in B_set if i not in [0] for t in T_set),name='radical-3')
# model.addConstrs((beta_ij[0,j,t]==0 for j in Ninsert_set[0] for t in T_set),name='redical-4')

#%% 目标函数
obj = quicksum(L_ijt[i,j,t]*r_ij[i,j] for (i,j) in branch_ij for t in T_set)
model.update()
model.setObjective(obj,GRB.MINIMIZE)
# model.Params.MIPGap = 0.01
model.update()
model.optimize()
# # model.write('abf.lp')
# model.computeIIS()
# model.write('abc.ilp')
#%% 输出数据
o = t
if model.status == GRB.Status.OPTIMAL:
    # dictalpha = {'line_index': branch_ij}
    dictalpha = {}
    dictv = {'bus_index': B_set}
    dictpij = {'line_index': branch_ij}
    dictbeta_ij = {'line_index': branch_ij}
    dictbeta_ji = {'line_index': branch_ji}
    dictL_ij = {'line_index': branch_ij}
    for t in T_set:
        dictalpha['t={}'.format(t)] = [alpha_ij[L+(t,) ].x for L in branch_ij]
        dictv['t={}'.format(t)] = [v_it[i,t].x for i in B_set]
        dictpij['t={}'.format(t)] = [P_ijt[L+(t,)].x for L in branch_ij]
        dictbeta_ij['t={}'.format(t)] = [beta_ij[L+(t,) ].x for L in branch_ij]
        dictbeta_ji['t={}'.format(t)] = [beta_ji[L+(t,) ].x for L in branch_ji]
        dictL_ij['t={}'.format(t)] = [L_ijt[L+(t,) ].x for L in branch_ij]
    dfalpha = pd.DataFrame(dictalpha)
    dL_ij = pd.DataFrame(dictL_ij)
    dfalpha1 = dfalpha
    dfalpha.index = branch_ij
    dfalpha1.to_excel('alpha.xlsx')
    dfalpha.iloc[:,0] = f
    dfalpha.iloc[:,1] = o
    flag = 0
    for i in T_set[3:]:
        frm = dfalpha[dfalpha.iloc[:,i]==1].iloc[:,0].values.tolist()
        to = dfalpha[dfalpha.iloc[:,i]==1].iloc[:,1].values.tolist()
        df = pd.DataFrame({'Source': frm, 'Target': to})
        G = nx.Graph()
        G.add_edges_from(df.values.tolist())
        # pos = nx.spring_layout(G)
        # nx.draw_networkx(G, pos)
        if not nx.is_directed_acyclic_graph(G): # 判断是否有环网
            flag += 1
    if flag:
        print("重构后的电网为辐射网")
        dfalpha1.to_excel('电网重构结果.xlsx')
    else:
        print("重构错误，重构后的电网存在环网")
    # pos = nx.spring_layout(G)
    # nx.draw_networkx(G, pos)
    # nx.draw(G)