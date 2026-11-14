"""Reproduce article numbers and original figures. SciPy 1.17.0, NumPy 2.3.5."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-curvature-mpl')
import json, pathlib, sys
import numpy as np
import scipy
from scipy.optimize import minimize, line_search
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
OUT=pathlib.Path(__file__).resolve().parent
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'path'})
H=np.diag([2.,40.]); target=np.array([1.,-2.]); x0=np.array([4.,3.])
def f(x): return float((x[0]-1)**2+20*(x[1]+2)**2)
def grad(x): return H@(x-target)
def fr_exact():
 x=x0.copy(); g=grad(x); p=-g; rows=[]; pts=[x.copy()]
 for k in range(2):
  a=-(g@p)/(p@H@p); xn=x+a*p; gn=grad(xn); b=(gn@gn)/(g@g)
  rows.append(dict(k=k,x=x.tolist(),g=g.tolist(),p=p.tolist(),alpha=float(a),step_norm=float(np.linalg.norm(a*p)),f=f(x),f_next=f(xn),beta_next=float(b)))
  pts.append(xn.copy()); x,g,p=xn,gn,-gn+b*p
 return rows,np.array(pts)
rows,pts=fr_exact(); g0=np.array(rows[0]['g']); g1=np.array(rows[1]['g']); p0=np.array(rows[0]['p']); p1=np.array(rows[1]['p']); beta=rows[0]['beta_next']
assert np.linalg.norm(pts[-1]-target)<1e-12
assert abs(g0@g1)<1e-9 and abs(p0@H@p1)<1e-9
# Same quadratic, exact-line-search steepest descent, for comparison only.
x=x0.copy(); gd=[x.copy()]
for i in range(12):
 g=grad(x); x=x-(g@g)/(g@H@g)*g; gd.append(x.copy())
gd=np.array(gd)
def rosen(x): return float((1-x[0])**2+100*(x[1]-x[0]**2)**2)
def rg(x): return np.array([-2*(1-x[0])-400*x[0]*(x[1]-x[0]**2),200*(x[1]-x[0]**2)])
# Independent nonlinear PR+ teaching algorithm, NOT scipy.optimize.minimize(CG).
# Strong Wolfe search, descent safeguard, periodic restart every two steps.
x=np.array([-1.2,1.]); g=rg(x); p=-g; restarts=[]; descent=[]
for k in range(200):
 if np.linalg.norm(g,np.inf)<1e-5: break
 if g@p>=-1e-3*(g@g): p=-g; restarts.append({'iteration':k,'reason':'descent safeguard'})
 descent.append(float(g@p)); a=line_search(rosen,rg,x,p,g,c1=1e-4,c2=.1,maxiter=30)[0]
 if a is None: raise RuntimeError('Wolfe search failed')
 xn=x+a*p; gn=rg(xn); b=max(0,float(gn@(gn-g)/(g@g)))
 pn=-gn+b*p
 if (k+1)%2==0: pn=-gn; restarts.append({'iteration':k+1,'reason':'periodic restart'})
 x,g,p=xn,gn,pn
assert max(descent)<0 and len(restarts)>0 and np.linalg.norm(g,np.inf)<1e-5
runs={}
for label,fun,jac,start in [('quadratic',f,grad,x0),('rosenbrock',rosen,rg,[-1.2,1.])]:
 r=minimize(fun,start,jac=jac,method='CG',options={'gtol':1e-5,'norm':np.inf,'c1':1e-4,'c2':.4,'maxiter':400})
 runs[label]={'x':r.x.tolist(),'fun':float(r.fun),'grad_inf':float(np.linalg.norm(jac(r.x),np.inf)),'grad_2':float(np.linalg.norm(jac(r.x))),'nit':int(r.nit),'nfev':int(r.nfev),'njev':int(r.njev),'success':bool(r.success),'message':str(r.message)}
 assert r.success and np.linalg.norm(jac(r.x),np.inf)<1e-5
fig,ax=plt.subplots(1,2,figsize=(12,5.8),gridspec_kw={'width_ratios':[1.1,1]},layout='constrained')
xx,yy=np.meshgrid(np.linspace(.4,4.4,320),np.linspace(-2.65,3.4,320)); zz=(xx-1)**2+20*(yy+2)**2
ax[0].contour(xx,yy,zz,levels=[.05,.5,2,8,25,80,200,509],colors='#cbd5e1',linewidths=.8)
ax[0].plot(gd[:,0],gd[:,1],'o--',color='#94a3b8',lw=1.5,ms=3,label='最急降下＋厳密直線探索（12更新）')
ax[0].plot(pts[:,0],pts[:,1],'o-',color='#0f766e',lw=2.5,ms=6,label='FR＋厳密直線探索（2更新）')
for i,z in enumerate(pts):ax[0].annotate(f'$x_{i}$',z,xytext=(7,8),textcoords='offset points')
ax[0].plot(*target,'*',color='#c2410c',ms=12)
ax[0].set(xlabel='x',ylabel='y',title='同じ谷で 前の向きを持ち越す',xlim=(.4,4.4),ylim=(-2.65,3.4)); ax[0].legend(loc='upper left',fontsize=9)
vals=np.array([-g1[1],beta*p0[1],p1[1]])
ax[1].barh([2,1,0],vals,color=['#2563eb','#d97706','#0f766e'],height=.53)
ax[1].axvline(0,color='#64748b',lw=.8);ax[1].set_yticks([2,1,0],['今の下り方向 −g1','引き継ぐ β1 p0','合成した p1'])
for i,val in zip([2,1,0],vals):ax[1].text(val+(0.004 if val>=0 else -.004),i,f'{val:+.6f}',ha='left' if val>=0 else 'right',va='center',fontsize=10)
ax[1].set(xlim=(-.245,.265),ylim=(-.9,2.75),xlabel='各方向の y 成分（同じ尺度）',title='2更新目の y 成分だけを拡大して読む')
ax[1].text(.5,.03,'0.171 − 0.162 ≈ 0.009\nx 成分は −5.700 → −5.705',transform=ax[1].transAxes,ha='center',va='bottom',fontsize=11,color='#334155')
fig.suptitle('非線形共役勾配法の仕組みを 二次関数で確かめる',fontsize=16)
fig.savefig(OUT/'main.png',dpi=160);fig.savefig(OUT/'main.svg');plt.close(fig)
result={'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'quadratic_FR_exact':rows,'checks':{'gradient_orthogonality_dot':float(g0@g1),'H_conjugacy_dot':float(p0@H@p1),'solution_error':float(np.linalg.norm(pts[-1]-target))},'nonlinear_teaching_PRplus':{'iterations':len(descent),'final_x':x.tolist(),'final_grad_inf':float(np.linalg.norm(g,np.inf)),'restart_events':restarts,'all_directions_descent':bool(max(descent)<0),'warning':'Independent educational implementation, not SciPy CG'},'scipy_CG':runs}
(OUT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
