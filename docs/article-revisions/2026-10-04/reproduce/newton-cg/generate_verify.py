"""Instrumented Newton-CG teaching example. Not a replacement for SciPy."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-curvature-mpl')
import pathlib,json,sys
import numpy as np, scipy
from scipy.optimize import minimize
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
OUT=pathlib.Path(__file__).resolve().parent
H=np.diag([2.,40.]);target=np.array([1.,-2.]);x0=np.array([4.,3.])
def f(x):return float((x[0]-1)**2+20*(x[1]+2)**2)
def grad(x):return H@(x-target)
def hp(x,v):return np.array([2*v[0],40*v[1]])
def inner(g,action):
 p=np.zeros_like(g);r=g.copy();d=-r;rr=r@r;tol=min(.5,np.sqrt(np.linalg.norm(g,1)))*np.linalg.norm(g,1); rows=[{'j':0,'p':p.tolist(),'residual_l1':float(np.linalg.norm(r,1))}]
 for j in range(20*len(g)):
  if np.linalg.norm(r,1)<=tol:return p,rows,tol,'residual'
  Hd=action(d);curv=float(d@Hd)
  if 0<=curv<=3*np.finfo(float).eps:return p,rows,tol,'near_zero_curvature'
  if curv<0:
   if j==0:p=rr/(-curv)*(-g)
   return p,rows,tol,'negative_curvature'
  direction_used=d.copy();a=rr/curv;p+=a*d;r+=a*Hd;rrn=r@r;d=-r+rrn/rr*d;rr=rrn
  rows.append({'j':j+1,'p':p.tolist(),'residual_l1':float(np.linalg.norm(r,1)),'direction_used':direction_used.tolist(),'direction_next':d.tolist(),'curvature_used':curv})
 raise RuntimeError('inner limit')
x=x0.copy();trace=[];pts=[x.copy()]
for k in range(2):
 g=grad(x);p,rows,tol,reason=inner(g,lambda v:hp(x,v));xn=x+p
 trace.append({'k':k,'x':x.tolist(),'g':g.tolist(),'gradient_l1':float(np.linalg.norm(g,1)),'gradient_2':float(np.linalg.norm(g)),'threshold_l1':float(tol),'p':p.tolist(),'linear_residual_l1':float(np.linalg.norm(H@p+g,1)),'inner_steps':len(rows)-1,'reason':reason,'inner_trace':rows,'alpha_outer':1.,'next_x':xn.tolist(),'next_f':f(xn)})
 x=xn;pts.append(x.copy())
assert np.linalg.norm(x-target)<1e-12
rng=np.random.default_rng(123); errors=[np.linalg.norm(hp(x0,v)-H@v) for v in rng.normal(size=(8,2))]
assert max(errors)<1e-12
neg=inner(np.array([1.,0.]),lambda v:np.diag([-2.,3.])@v)
assert neg[3]=='negative_curvature' and np.allclose(neg[0],[-.5,0.])
def rosen(x):return float((1-x[0])**2+100*(x[1]-x[0]**2)**2)
def rg(x):return np.array([-2*(1-x[0])-400*x[0]*(x[1]-x[0]**2),200*(x[1]-x[0]**2)])
def rhp(x,v):return np.array([(1200*x[0]**2-400*x[1]+2)*v[0]-400*x[0]*v[1],-400*x[0]*v[0]+200*v[1]])
runs={}
for name,fn,gn,hn,start in [('quadratic',f,grad,hp,x0),('rosenbrock',rosen,rg,rhp,[-1.2,1.])]:
 counter=[0];calls=[]; path=[np.array(start,dtype=float).copy()]
 def counted(x,v):counter[0]+=1;calls.append(x.copy());return hn(x,v)
 r=minimize(fn,start,jac=gn,hessp=counted,method='Newton-CG',callback=lambda xk:path.append(xk.copy()),options={'xtol':1e-5,'maxiter':400,'c1':1e-4,'c2':.9,'return_all':True})
 runs[name]={'x':r.x.tolist(),'fun':float(r.fun),'grad_2':float(np.linalg.norm(gn(r.x))),'grad_inf':float(np.linalg.norm(gn(r.x),np.inf)),'nit':int(r.nit),'nfev':int(r.nfev),'njev':int(r.njev),'nhev':int(r.nhev),'actual_hvp_calls':counter[0],'success':bool(r.success),'path':[p.tolist() for p in path]}
 assert r.success and r.nhev==counter[0]
 if name=='quadratic':assert np.allclose(np.array(path)[:3],pts,atol=1e-12)
pts=np.array(pts)
fig,ax=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
xx,yy=np.meshgrid(np.linspace(.4,4.4,300),np.linspace(-2.6,3.5,300));ax[0].contour(xx,yy,(xx-1)**2+20*(yy+2)**2,levels=[.5,2,8,25,80,200,509],colors='#cbd5e1')
ax[0].plot(pts[:,0],pts[:,1],'o-',c='#0f766e',lw=2.5)
for k,z in enumerate(pts):ax[0].annotate(f'外側 k={k}',z,xytext=(-65 if k==0 else 8,10),textcoords='offset points')
ax[0].set(xlabel='x',ylabel='y',title='外側 実際に目的関数上を進む');ax[0].plot(*target,'*',ms=13,c='#c2410c')
for k,col in [(0,'#0f766e'),(1,'#2563eb')]:
 tr=trace[k];rs=[max(r['residual_l1'],1e-15) for r in tr['inner_trace']]
 ax[1].semilogy(range(len(rs)),rs,'o-',color=col,label=f'外側 k={k} の線形残差')
 ax[1].axhline(tr['threshold_l1'],color=col,ls='--',alpha=.65,label=f'内側の閾値 {tr["threshold_l1"]:.4f}')
ax[1].set(xticks=[0,1,2],xlabel='内側 CG の更新回数 j',ylabel=r'$\|H p^{(j)}+g_k\|_1$',title='内側 現在点を固定して方向を作る',ylim=(1e-15,1e3));ax[1].legend(loc='lower left',fontsize=9)
fig.suptitle('Newton-CG  内側の残差と 外側の勾配を分けて読む',fontsize=16)
fig.savefig(OUT/'main.png',dpi=160);fig.savefig(OUT/'main.svg');plt.close(fig)
result={'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'teaching_trace':trace,'hvp_max_error':float(max(errors)),'negative_curvature_test':{'g':[1.,0.],'H_diagonal':[-2.,3.],'p':neg[0].tolist(),'reason':neg[3]},'scipy_Newton_CG':runs}
(OUT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='scipy_Newton_CG'},ensure_ascii=False,indent=2));print({k:{a:b for a,b in v.items() if a!='path'} for k,v in runs.items()})
