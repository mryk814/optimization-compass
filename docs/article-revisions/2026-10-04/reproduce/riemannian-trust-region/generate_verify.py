from pathlib import Path
import json
import numpy as np
from scipy.linalg import null_space
from scipy.optimize import minimize
from example import A,solve,subproblem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent;MEDIA=ROOT/'site/public/media';MEDIA.mkdir(parents=True,exist_ok=True)
x,history=solve();assert abs(x@A@x-1)<1e-12
assert history[0]['accepted']==False and history[1]['accepted']==True
assert max(r['kkt'] for r in history)<1e-10
for row in history:
    xr=np.array(row['x']);Qr=null_space(xr[None,:]);fr=xr@A@xr
    gr=2*Qr.T@A@xr;Hr=2*Qr.T@(A-fr*np.eye(3))@Qr
    pr,lr=subproblem(gr,Hr,row['radius'])
    assert np.linalg.eigvalsh(Hr+lr*np.eye(2))[0]>-1e-11
    assert np.linalg.norm(pr)<=row['radius']+1e-11
    assert abs(lr*(row['radius']-np.linalg.norm(pr)))<1e-10
    assert abs(xr@(Qr@pr))<1e-12
    if row['predicted']>1e-10:
        assert abs(row['rho']-1/(1+pr@pr))<1e-6
x0=np.ones(3)/np.sqrt(3);Q=null_space(x0[None,:]);f=x0@A@x0;g=2*Q.T@A@x0;H=2*Q.T@(A-f*np.eye(3))@Q
p,lam=subproblem(g,H,4);u=p/np.linalg.norm(p)
# Independent oracle: SLSQP, many boundary initial points and zero.
oracle=[]
for a in np.linspace(0,2*np.pi,20,endpoint=False):
 r=minimize(lambda z:g@z+.5*z@H@z,4*np.array([np.cos(a),np.sin(a)]),jac=lambda z:g+H@z,method='SLSQP',constraints={'type':'ineq','fun':lambda z:16-z@z,'jac':lambda z:-2*z},options={'ftol':1e-11,'maxiter':100})
 if r.success:oracle.append(float(r.fun))
assert abs(min(oracle)-(g@p+.5*p@H@p))<1e-8
# Pullback Hessian check; normalization is a second-order retraction.
F=lambda z:(x0+Q@z)@A@(x0+Q@z)/(1+z@z)
h=1e-4;fd=(F(h*u)-2*F(np.zeros(2))+F(-h*u))/h**2
assert abs(fd-u@H@u)<1e-6
# Check the negative-curvature hard case at the maximum eigenvector.
ph,lh=subproblem(np.zeros(2),np.diag([-6.,-4.]),.5)
assert abs(np.linalg.norm(ph)-.5)<1e-12 and abs(ph@np.diag([-6.,-4.])@ph+1.5)<1e-12
s=np.linspace(0,4,300);pred=np.array([-g@(v*u)-.5*(v*u)@H@(v*u) for v in s]);actual=np.array([f-F(v*u) for v in s])
fig,ax=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
ax[0].plot(s,pred,c='#d47a1f',label='二次モデルの予測減少');ax[0].plot(s,actual,c='#128174',label='正規化後の実際の減少');ax[0].set_xlabel('最初の候補方向に沿う接ステップの長さ');ax[0].set_ylabel('減少量');ax[0].set_title('大きい接ステップの予測は外れる');ax[0].legend();ax[0].grid(alpha=.2)
k=np.arange(4);ax[1].bar(k,[r['rho'] for r in history[:4]],color=['#bf4c58','#128174','#128174','#128174']);ax[1].axhline(.1,ls='--',c='#555',label='受理閾値 0.1');ax[1].set_ylim(0,1.25);ax[1].set_xticks(k,[f"k={r['k']}\nΔ={r['radius']:g}" for r in history[:4]]);ax[1].set_ylabel('$\\rho$');ax[1].set_title('棄却 → 同じ点で半径を縮めて再提案');ax[1].legend(loc='upper left')
for i,r in enumerate(history[:4]):ax[1].text(i,r['rho']+.04,'受理' if r['accepted'] else '棄却',ha='center')
fig.suptitle('球面Rayleigh商の完全な小例：予測・実測・採否・半径更新',fontsize=15)
for ext in ('svg','png'):fig.savefig(MEDIA/f'riemannian-trust-rayleigh.{ext}',dpi=160)
(ROOT/'verified-numbers.json').write_text(json.dumps({'history':history,'final_x':x.tolist(),'final_cost':float(x@A@x),'eigenvalue_oracle':np.linalg.eigvalsh(A).tolist(),'first_subproblem_value':float(g@p+.5*p@H@p),'independent_slsqp_value':min(oracle),'hessian_finite_difference':float(fd),'hessian_quadratic_form':float(u@H@u),'negative_curvature_hard_case_checked':True},indent=2)+'\n')
