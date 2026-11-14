"""Disk geometry, separate KKT residuals, sensitivity, and nonconvex counterexamples."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/oc-foundations-mpl')
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize, Bounds, NonlinearConstraint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
P=Path(__file__).resolve().parent; (P/'media').mkdir(exist_ok=True)
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
f=lambda z:float(np.asarray(z)@np.asarray(z));gf=lambda z:2*np.asarray(z)
g=lambda z:float(np.sum((np.asarray(z)-1)**2)-1);gg=lambda z:2*(np.asarray(z)-1)
x=np.full(2,1-1/np.sqrt(2));lam=np.sqrt(2)-1

def residual(z,la):
 return {'x':np.asarray(z).tolist(),'objective':f(z),'g':g(z),'primal_violation':float(max(0,g(z),-1-np.min(z),np.max(z)-3)),'dual_violation':float(max(0,-la)),'stationarity':float(np.max(np.abs(gf(z)+la*gg(z)))),'complementarity':float(abs(la*g(z))),'lambda':float(la)}
analytic=residual(x,lam)
assert all(analytic[k]<1e-14 for k in ['primal_violation','dual_violation','stationarity','complementarity'])
box=Bounds([-1,-1],[3,3])
r=minimize(f,[2.,2.],jac=gf,method='SLSQP',bounds=box,constraints=[{'type':'ineq','fun':lambda z:-g(z),'jac':lambda z:-gg(z)}],options={'ftol':1e-12,'maxiter':200})
rla=-gf(r.x)@gg(r.x)/(gg(r.x)@gg(r.x))
tc=minimize(f,[2.,2.],jac=gf,hess=lambda z:2*np.eye(2),method='trust-constr',bounds=box,constraints=[NonlinearConstraint(g,-np.inf,0,jac=gg,hess=lambda z,v:2*v[0]*np.eye(2))],options={'gtol':1e-11,'xtol':1e-12,'barrier_tol':1e-12,'maxiter':500,'initial_barrier_parameter':1e-8,'initial_barrier_tolerance':1e-8})
assert r.success and tc.success and np.allclose(r.x,x,atol=1e-7) and np.allclose(tc.x,x,atol=1e-6)
assert residual(r.x,rla)['stationarity']<1e-8
assert residual(tc.x,tc.v[0][0])['stationarity']<1e-6
ss=[.5,1,1.1,2,2.2];sens=[]
for s in ss:
 z=np.full(2,max(0,1-np.sqrt(s/2)))
 v=max(np.sqrt(2)-np.sqrt(s),0)**2
 la=max(np.sqrt(2/s)-1,0)
 assert np.isclose(f(z),v) and np.sum((z-1)**2)<=s+1e-14
 assert np.linalg.norm(gf(z)+la*gg(z),np.inf)<1e-14
 sens.append({'radius_squared':s,'x':z.tolist(),'objective':v,'lambda':la})
assert np.isclose((sens[1]['objective']-sens[2]['objective']),.0380522701,atol=1e-9)
wrong=minimize(f,[2.,2.],jac=gf,method='SLSQP',bounds=box,constraints=[{'type':'ineq','fun':g,'jac':gg}],options={'ftol':1e-9})
far=np.full(2,1+1/np.sqrt(2));eps=.01
near=np.ones(2)+[np.cos(np.pi/4+eps),np.sin(np.pi/4+eps)]
assert abs(g(near))<1e-14 and f(near)<f(far)
local=[]
for start in ([2.,2.],[-2.,-2.]):
 out=minimize(lambda z:z[0]+z[1],start,jac=lambda z:np.ones(2),method='SLSQP',bounds=[(-3,3),(-3,3)],constraints=[{'type':'ineq','fun':lambda z:z[0]*z[1]-1,'jac':lambda z:np.array([z[1],z[0]])}],options={'ftol':1e-9})
 assert out.success
 local.append({'start':start,'x':out.x.tolist(),'objective':float(out.fun),'constraint_violation':float(max(0,1-out.x.prod()))})
assert np.allclose(local[0]['x'],[1,1]) and np.allclose(local[1]['x'],[-3,-3])
fig,axs=plt.subplots(1,3,figsize=(14,4.8),layout='constrained',gridspec_kw={'width_ratios':[1,1,1.15]})
angle=np.linspace(0,2*np.pi,500);cx=1+np.cos(angle);cy=1+np.sin(angle)
ax=axs[0];ax.fill(cx,cy,color='#dcebf5');ax.plot(cx,cy,color='#2675a3',lw=2)
xx,yy=np.meshgrid(np.linspace(-.3,2.2,250),np.linspace(-.3,2.2,250));cs=ax.contour(xx,yy,xx**2+yy**2,levels=[f(x),.5,1,2,4],colors='#a4b8c8',linewidths=.8)
ax.plot([0,1],[0,1],ls='--',color='#758791');ax.scatter(0,0,marker='x',s=80,color='#ad393c',zorder=4);ax.scatter(1,1,s=35,color='#2675a3')
ax.scatter(*x,marker='*',s=170,color='#c65d2b',zorder=5)
ax.annotate('原点：f = 0\nでも g = 1 > 0',(0,0),xytext=(10,-35),textcoords='offset points',fontsize=10)
ax.annotate('解 ≈ (0.293, 0.293)',x,xytext=(-12,24),textcoords='offset points',fontsize=10,color='#9c3d1a')
ax.annotate('中心 (1, 1)',(1,1),xytext=(8,8),textcoords='offset points',fontsize=10)
ax.set(xlim=(-.3,2.2),ylim=(-.35,2.2),aspect='equal',xlabel='x',ylabel='y',title='① 目的より先に可行性')
ax=axs[1];ax.fill(cx,cy,color='#e6f0f6');ax.plot(cx,cy,color='#2675a3',lw=2);ax.scatter(*x,marker='*',s=170,color='#c65d2b',zorder=5)
for vec,color,label,offset in [(gf(x),'#756298','∇f',(4,5)),(lam*gg(x),'#368577','λ∇g',(-4,-15))]:
 end=x+.65*vec;ax.annotate('',end,x,arrowprops={'arrowstyle':'->','color':color,'lw':2.5});ax.annotate(label,end,xytext=offset,textcoords='offset points',color=color)
ax.set(xlim=(-.23,.9),ylim=(-.23,.9),aspect='equal',xlabel='x',ylabel='y',title='② 勾配は反対向きに釣り合う');ax.grid(alpha=.12)
ax=axs[2];s=np.linspace(.6,1.6,300);val=np.maximum(np.sqrt(2)-np.sqrt(s),0)**2
ax.plot(s,val,color='#2675a3',lw=2,label='最適値 v(s)');ax.plot(s,f(x)-lam*(s-1),ls='--',color='#b16738',label='s = 1での接線')
ax.scatter([1,1.1],[f(x),sens[2]['objective']],color='#c65d2b',zorder=4)
ax.annotate('s=1\n0.1716',(1,f(x)),xytext=(-58,-18),textcoords='offset points',fontsize=10)
ax.annotate('s=1.1\n0.1335',(1.1,sens[2]['objective']),xytext=(13,20),textcoords='offset points',fontsize=10)
ax.axhline(0,lw=.7,color='#999');ax.set(xlabel='半径の二乗 s',ylabel='最適な目的値',title='③ 乗数は局所的な感度');ax.legend(frameon=False,fontsize=10);ax.grid(alpha=.12)
fig.suptitle('円板内で原点に近づく：同じ例で可行性・KKT・感度を読む',fontsize=15)
for ext in ['svg','png']:fig.savefig(P/'media'/f'constrained-nlp-disk.{ext}',dpi=180)
plt.close(fig)
report={'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'analytic':analytic,'slsqp':{**residual(r.x,rla),'success':bool(r.success),'message':r.message},'trust_constr':{**residual(tc.x,tc.v[0][0]),'success':bool(tc.success),'message':tc.message,'bound_multipliers':tc.v[1].tolist()},'sensitivity':sens,'wrong_sign':{'x':wrong.x.tolist(),'objective':wrong.fun,'success':bool(wrong.success),'g':g(wrong.x),'nearby_boundary_point':near.tolist(),'nearby_objective':f(near),'far_exact_objective':f(far),'curvature_counterexample':float(f(near)-f(far))},'nonconvex_two_components':local,'tests':'all assertions passed'}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
