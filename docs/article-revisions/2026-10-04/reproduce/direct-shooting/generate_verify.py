from pathlib import Path
import json
import numpy as np
from scipy.optimize import minimize,brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent
n=20;a=.92;b=.1;r=.002;w=b*a**(n-1-np.arange(n))
roll=lambda u:np.array([0.]+[sum(b*a**(k-1-j)*u[j] for j in range(k)) for k in range(1,n+1)])
cost=lambda u:(w@u-1)**2+r*(u@u)
grad=lambda u:2*(w@u-1)*w+2*r*u
u=np.zeros(n);history=[]
for k in range(81):
 history.append([k,float(cost(u)),float(w@u)])
 if k<80:u=np.clip(u-4*grad(u),-1,1)
x=roll(u);dyn=x[1:]-a*x[:-1]-b*u
assert np.max(abs(dyn))<1e-15
finite=[];eps=1e-6
for j in range(n):
 e=np.eye(n)[j]*eps;finite.append((cost(u+e)-cost(u-e))/(2*eps))
assert np.max(abs(finite-grad(u)))<1e-9
res=minimize(cost,np.zeros(n),jac=grad,bounds=[(-1,1)]*n,method='L-BFGS-B',options={'gtol':1e-12,'ftol':1e-15,'maxiter':2000})
assert res.success
# Independent analytic active-set oracle: terminal residual e fixes each free u.
e=brentq(lambda e:w@np.minimum(1,e*w/r)+e-1,0,1)
uopt=np.minimum(1,e*w/r)
assert abs(cost(uopt)-res.fun)<1e-11
lam=brentq(lambda z:w@np.minimum(1,z*w)-1,0,1e5);ueq=np.minimum(1,lam*w)
assert abs(w@ueq-1)<1e-12
mapping=lambda z:(z-np.clip(z-4*grad(z),-1,1))/4
hessian_norm=2*(w@w+r)
fig,axs=plt.subplots(2,1,figsize=(9,6),layout='constrained')
axs[0].step(np.arange(n),u,where='mid',c='#128174',label='80更新の入力');axs[0].plot(np.arange(n),ueq,'--',c='#d47a1f',label='終端等式つき最小入力費用');axs[0].axhline(1,c='#999',ls=':');axs[0].legend();axs[0].set_ylabel('入力')
axs[1].plot(np.arange(n+1),x,'o-',c='#128174',label='80更新の状態');axs[1].plot(np.arange(n+1),roll(ueq),'--',c='#d47a1f',label='終端等式の状態');axs[1].axhline(1,c='#999',ls=':');axs[1].set_xlabel('段');axs[1].set_ylabel('状態');axs[1].legend()
fig.suptitle('検算用：終端罰則と終端等式は違う問題',fontsize=15)
fig.savefig(ROOT/'verification-rollout.png',dpi=160)
result=dict(history=history,controls_80=u.tolist(),states_80=x.tolist(),active_upper_count=int(np.sum(u>=1-1e-12)),finite_difference_max_error=float(np.max(abs(finite-grad(u)))),dynamics_max_residual=float(np.max(abs(dyn))),projected_gradient_mapping_80=float(np.linalg.norm(mapping(u))),raw_gradient_80=float(np.linalg.norm(grad(u))),true_optimal_controls=uopt.tolist(),true_optimal_cost=float(cost(uopt)),true_optimal_terminal=float(w@uopt),cost_gap_80=float(cost(u)-cost(uopt)),equality_controls=ueq.tolist(),equality_terminal=float(w@ueq),equality_control_cost=float(r*ueq@ueq),maximum_reachable_terminal=float(w.sum()),hessian_spectral_norm=float(hessian_norm),learning_rate=4.)
(ROOT/'verified-numbers.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)},indent=2))
