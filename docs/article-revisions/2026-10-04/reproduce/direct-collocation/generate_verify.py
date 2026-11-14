from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from example import solve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent;MEDIA=ROOT/'site/public/media';MEDIA.mkdir(parents=True,exist_ok=True)
rows=[]
for N in [4,20,80]:
 z,initial,C,b=solve(N);h=1/N;x=z[:N+1];u=z[N+1:];oracle=np.r_[np.linspace(0,1,N+1),np.ones(N)]
 assert np.max(abs(z-oracle))<1e-8
 r=C@z-b;assert np.linalg.norm(r)<1e-12
 xx=0.;reintegrated=[xx]
 for uk in u:
  sol=solve_ivp(lambda t,y:[uk],[0,h],[xx],rtol=1e-11,atol=1e-13);xx=sol.y[0,-1];reintegrated.append(xx)
 assert np.max(abs(x-reintegrated))<1e-12
 eps=1e-6;direction=np.linspace(-1,1,len(z));fd=(C@(z+eps*direction)-C@(z-eps*direction))/(2*eps)
 assert np.max(abs(fd-C@direction))<1e-9
 rows.append(dict(N=N,cost=float(h*u@u),initial_defect_l2=float(np.linalg.norm((C@initial-b)[1:-1])),initial_scaled_defect_max=float(np.max(abs((C@initial-b)[1:-1]/h))),solved_residual=float(np.linalg.norm(r)),reintegrated_error=float(np.max(abs(x-reintegrated))),oracle_error=float(np.max(abs(z-oracle))),state=x.tolist(),control=u.tolist()))
r=rows[1];N=20;h=1/N;t=np.linspace(0,1,N+1)
fig,ax=plt.subplots(1,3,figsize=(13,4.3),layout='constrained')
ax[0].plot(t,t,'o',mfc='none',c='#bf4c58',label='初期の状態変数（直線）');ax[0].plot(t,np.zeros(N+1),'--',c='#bf4c58',label='初期入力0の再積分');ax[0].plot(t,r['state'],c='#128174',label='解の状態＝再積分');ax[0].set_title('同じ終点でも、初期候補は力学不整合');ax[0].set_ylabel('状態 x');ax[0].legend(fontsize=8,loc='upper left')
ax[1].stairs(np.zeros(N),t,color='#bf4c58',label='初期入力');ax[1].stairs(r['control'],t,color='#128174',label='解の入力');ax[1].set_ylim(-.1,1.25);ax[1].set_ylabel('入力 u');ax[1].set_title('入力を0 → 1へ変えて整合させる');ax[1].legend(fontsize=9)
ax[2].plot((t[:-1]+t[1:])/2,np.ones(N),'o-',c='#bf4c58',label='初期候補');ax[2].plot((t[:-1]+t[1:])/2,np.zeros(N),'o-',c='#128174',label='解');ax[2].set_ylabel('区間defect / h');ax[2].set_ylim(-.1,1.25);ax[2].set_title('速度の単位にそろえた残差');ax[2].legend(fontsize=9)
for a in ax:a.set_xlabel('時刻 t');a.grid(alpha=.2)
fig.suptitle('積分系の直接離散化：費用0の直線が、なぜ解ではないか',fontsize=16)
for ext in ('svg','png'):fig.savefig(MEDIA/f'collocation-integrator-defect.{ext}',dpi=160)
(ROOT/'verified-numbers.json').write_text(json.dumps({'rows':rows,'interpretation':'This integrator with piecewise constant controls has exact Euler interval dynamics; mesh refinement cannot demonstrate generic discretization convergence.'},indent=2)+'\n')
