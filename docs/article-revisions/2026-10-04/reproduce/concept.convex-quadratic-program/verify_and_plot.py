"""Analytic, KKT and independent SLSQP checks of the same convex QP."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/oc-foundations-mpl')
from pathlib import Path
import json
import numpy as np
import scipy
from scipy.optimize import minimize, LinearConstraint, Bounds
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
P=Path(__file__).resolve().parent; (P/'media').mkdir(exist_ok=True)
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
t=np.array([3.,2.]);Q=2*np.eye(2);c=-2*t
K=np.block([[Q,np.ones((2,1))],[np.ones((1,2)),np.zeros((1,1))]])
sol=np.linalg.solve(K,np.r_[2*t,3.]);x=sol[:2];lam=sol[2]
assert np.allclose(x,[2,1]) and np.isclose(lam,2)
f=lambda z: float(np.sum((z-t)**2))
r=minimize(f,[.5,.5],jac=lambda z:2*(z-t),method='SLSQP',bounds=Bounds(0,np.inf),constraints=[LinearConstraint([[1.,1.]],-np.inf,3.)],options={'ftol':1e-12,'maxiter':100})
assert r.success and np.allclose(r.x,x,atol=1e-8)
stationarity=2*(x-t)+lam*np.ones(2)
assert np.linalg.norm(stationarity,np.inf)<1e-14
assert np.isclose(f(x),2) and np.isclose(.5*x@Q@x+c@x,-11)
assert np.all(np.linalg.eigvalsh(Q)>0)
vertices=[{'x':z,'objective':f(np.array(z))} for z in [[0,0],[3,0],[0,3]]]
# Perturb the budget through changes of the active constraint set.
rows=[]
for b in [0,.5,1,3,3.1,5,6]:
 if b<=1: z=np.array([b,0.]);la=6-2*b;mu=np.array([0.,2-2*b])
 elif b<5: z=np.array([(b+1)/2,(b-1)/2]);la=5-b;mu=np.zeros(2)
 else:z=t.copy();la=0.;mu=np.zeros(2)
 assert z.min()>=0 and z.sum()<=b+1e-12
 assert np.max(np.abs(2*(z-t)+la-mu))<1e-12
 assert abs(la*(z.sum()-b))<1e-12 and np.max(np.abs(mu*z))<1e-12
 rr=minimize(f,np.zeros(2),jac=lambda z:2*(z-t),method='SLSQP',bounds=Bounds(0,np.inf),constraints=[LinearConstraint([[1.,1.]],-np.inf,b)],options={'ftol':1e-12})
 assert rr.success and np.allclose(rr.x,z,atol=1e-7)
 rows.append({'budget':b,'x':z.tolist(),'objective':f(z),'lambda_budget':la,'lower_bound_multipliers':mu.tolist()})
# PSD alone is not uniqueness: x1^2 is constant along all feasible x2 when x1=0.
assert np.array_equal(np.linalg.eigvalsh(np.diag([2.,0.])),[0,2])
assert 0**2+0*0**2 == 0**2+0*1**2 == 0
fig,axs=plt.subplots(1,2,figsize=(11.5,5.6),layout='constrained')
xx,yy=np.meshgrid(np.linspace(-.25,3.55,300),np.linspace(-.25,3.1,270))
for ax,tar,ans,ttl in zip(axs,[t,np.array([1.,1.])],[x,np.array([1.,1.])],['目標 (3, 2)：辺の途中が最良','目標 (1, 1)：内部が最良']):
 ax.fill([0,3,0],[0,0,3],color='#e3eef6',zorder=0)
 cs=ax.contour(xx,yy,(xx-tar[0])**2+(yy-tar[1])**2,levels=[.25,1,2,4,8],colors='#abc2d4',linewidths=1)
 ax.clabel(cs,inline=True,fontsize=8)
 ax.plot([0,3,0,0],[0,0,3,0],color='#286994',lw=2)
 ax.scatter(*tar,s=95,marker='x',color='#ab4b29',zorder=4)
 ax.scatter(*ans,s=155,marker='*',color='#c65d2b',zorder=5)
 ax.set(xlim=(-.3,3.65),ylim=(-.35,3.25),aspect='equal',xlabel='x1',ylabel='x2',title=ttl)
 ax.grid(alpha=.12)
axs[0].plot([2,3],[1,2],ls='--',lw=1.6,color='#c65d2b')
axs[0].annotate('目標：制約の外',(3,2),xytext=(-110,22),textcoords='offset points')
axs[0].annotate('解 (2, 1)\nf = 2,  λ = 2',(2,1),xytext=(30,-5),textcoords='offset points',color='#9f401c')
axs[0].annotate('',(1.3,.3),(2,1),arrowprops={'arrowstyle':'->','lw':2,'color':'#786299'})
axs[0].text(1.12,.48,'∇f',color='#786299')
axs[0].annotate('',(2.7,1.7),(2,1),arrowprops={'arrowstyle':'->','lw':2,'color':'#328676'})
axs[0].text(2.56,1.35,'λ∇g',color='#328676')
axs[0].text(.1,2.65,'x1 + x2 ≤ 3',fontsize=10,color='#286994')
axs[1].annotate('目標 = 解\nf = 0,  λ = 0',(1,1),xytext=(18,23),textcoords='offset points',color='#9f401c')
fig.suptitle('目標から等高線を広げ、可行領域へ最初に触れる点を見る',fontsize=14)
for ext in ['svg','png']:fig.savefig(P/'media'/f'convex-qp-projection.{ext}',dpi=180)
plt.close(fig)
report={'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'analytic':{'x':x.tolist(),'objective':f(x),'lambda':float(lam),'stationarity':stationarity.tolist(),'budget_residual':float(x.sum()-3),'complementarity':float(lam*(x.sum()-3)),'Q_eigenvalues':np.linalg.eigvalsh(Q).tolist(),'standard_objective_without_constant':-11.,'constant':13.},'slsqp':{'x':r.x.tolist(),'objective':r.fun,'success':bool(r.success)},'vertices':vertices,'budget_sweep':rows,'psd_counterexample':{'Q':[[2,0],[0,0]],'two_minimizers':[[0,0],[0,1]],'objective':0},'tests':'all assertions passed'}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
