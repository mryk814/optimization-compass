from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp,quad
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent;MEDIA=ROOT/'site/public/media';MEDIA.mkdir(parents=True,exist_ok=True)
rows=[]
for n in (2,4,10):
 h=1/n;k=np.arange(n);B=np.vstack([h*h*(n-1-k),np.full(n,h)]);target=np.array([1.,0.])
 u=B.T@np.linalg.solve(B@B.T,target)
 closed=6*n*(n-1-2*k)/(n*n-1)
 assert np.max(abs(u-closed))<1e-12
 res=minimize(lambda z:h*(z@z),np.zeros(n),jac=lambda z:2*h*z,method='SLSQP',constraints={'type':'eq','fun':lambda z:B@z-target,'jac':lambda z:B},options={'ftol':1e-12,'maxiter':200})
 assert res.success and np.max(abs(res.x-u))<1e-9
 qe=[0.];qx=[0.];v=[0.];ivp=[0.,0.]
 for value in u:
  qe.append(qe[-1]+h*v[-1]);qx.append(qx[-1]+h*v[-1]+.5*h*h*value);v.append(v[-1]+h*value)
  # Integrate each constant-input segment separately at the discontinuities.
  sol=solve_ivp(lambda t,z:[z[1],value],[0,h],ivp,rtol=1e-11,atol=1e-13);ivp=sol.y[:,-1]
  assert abs(ivp[0]-qx[-1])<1e-11
 row=dict(N=n,u=u.tolist(),cost=float(h*u@u),closed_form_cost=12*n*n/(n*n-1),euler_q=qe,exact_q=qx,v=v,terminal_residual=float(np.linalg.norm(B@u-target)),max_position_error=float(np.max(abs(np.array(qe)-qx))))
 rows.append(row)
assert abs(quad(lambda t:(6-12*t)**2,0,1)[0]-12)<1e-12
# Continuous endpoint and lower-bound kernel norm.
assert abs(quad(lambda t:(.5-t)**2,0,1)[0]-1/12)<1e-14
r=rows[1];u=np.array(r['u']);h=.25;tt=np.linspace(0,1,401);qd=3*tt**2-2*tt**3;vd=6*tt-6*tt**2
qfine=[];vfine=[]
for t in tt:
 k=min(int(t/h),3);s=t-k*h;qfine.append(r['exact_q'][k]+r['v'][k]*s+.5*u[k]*s*s);vfine.append(r['v'][k]+u[k]*s)
fig,ax=plt.subplots(2,2,figsize=(11,7),layout='constrained');tn=np.linspace(0,1,5)
ax[0,0].plot(tt,6-12*tt,c='#22354b',label='連続最適解');ax[0,0].stairs(u,tn,color='#d47a1f',label='N=4 の区分一定入力');ax[0,0].set_ylabel('入力 u');ax[0,0].legend(fontsize=9)
ax[0,1].plot(tt,vd,c='#22354b',label='連続最適解');ax[0,1].plot(tt,vfine,c='#d47a1f',label='N=4 の再積分');ax[0,1].set_ylabel('速度 v');ax[0,1].legend(fontsize=9)
ax[1,0].plot(tt,qd,c='#22354b',label='連続最適解');ax[1,0].plot(tt,qfine,c='#128174',label='N=4 の区間内厳密解');ax[1,0].plot(tn,r['euler_q'],'o--',c='#bf4c58',label='Euler節点');ax[1,0].set_ylabel('位置 q');ax[1,0].legend(fontsize=9)
for a in ax.flat:a.grid(alpha=.2)
for a in [ax[0,0],ax[0,1],ax[1,0]]:a.set_xlabel('時刻 t [s]')
ax[1,1].plot([r['N'] for r in rows],[r['cost'] for r in rows],'o-',c='#128174',label='離散問題の最小費用');ax[1,1].axhline(12,c='#22354b',ls='--',label='連続最適値 12');ax[1,1].set_xlabel('区間数 N');ax[1,1].set_ylabel('費用');ax[1,1].set_xticks([2,4,10]);ax[1,1].legend(fontsize=9)
fig.suptitle('台車を1秒で静止0 → 静止1：入力・速度・位置・費用',fontsize=16)
for ext in ('svg','png'):fig.savefig(MEDIA/f'optimal-control-double-integrator.{ext}',dpi=160)
(ROOT/'verified-numbers.json').write_text(json.dumps({'continuous_cost':12,'rows':rows,'independent_checks':['linear minimum-norm solution','closed-form discrete solution','SLSQP','solve_ivp per segment','quad continuous cost and lower bound']},indent=2)+'\n')
print([(r['N'],r['cost'],r['max_position_error']) for r in rows])
