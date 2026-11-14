"""Exact 2-D educational secular-equation solver and separate SciPy run."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-curvature-mpl')
import json,pathlib,sys
import numpy as np, scipy
from scipy.optimize import minimize,brentq
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
OUT=pathlib.Path(__file__).resolve().parent
H=np.diag([2.,40.]);g=np.array([6.,200.]);x0=np.array([4.,3.])
def f(x):return float((x[0]-1)**2+20*(x[1]+2)**2)
def grad(x):return H@(x-np.array([1.,-2.]))
def solve_tr(H,g,delta):
 """Small symmetric educational solver via eigendecomposition, including hard case."""
 d,U=np.linalg.eigh(H);b=U.T@g;lo=max(0.,-d[0]);den=d+lo;zero=abs(den)<1e-12
 if not np.any(zero):
  q=-b/den
  if np.linalg.norm(q)<=delta:return U@q,lo
 elif np.all(abs(b[zero])<1e-12):
  q=np.zeros_like(b);q[~zero]=-b[~zero]/den[~zero]
  if np.linalg.norm(q)<=delta:
   if lo>0:q[np.flatnonzero(zero)[0]]=np.sqrt(max(0,delta**2-q@q))
   return U@q,lo
 def eq(lam):return np.linalg.norm(b/(d+lam))-delta
 left=lo+max(1e-13,1e-13*abs(lo));right=max(1.,2*left)
 while eq(right)>0:right*=2
 lam=brentq(eq,left,right,xtol=1e-13,rtol=1e-14)
 return U@(-b/(d+lam)),lam
def record(H,g,D):
 p,lam=solve_tr(H,g,D);res=np.linalg.norm((H+lam*np.eye(len(g)))@p+g)
 assert np.linalg.norm(p)<=D+1e-10 and res<1e-9
 assert np.linalg.eigvalsh(H+lam*np.eye(len(g)))[0]>=-1e-10
 assert abs(lam*(np.linalg.norm(p)-D))<1e-8
 return {'delta':float(D),'lambda':float(lam),'p':p.tolist(),'norm_p':float(np.linalg.norm(p)),'model_change':float(g@p+.5*p@H@p),'kkt_residual':float(res),'shifted_min_eigenvalue':float(np.linalg.eigvalsh(H+lam*np.eye(len(g)))[0])}
rows=[]
for D in [1.,2.,4.,np.sqrt(34)]:
 r=record(H,g,D);r['f_trial']=f(x0+np.array(r['p']));r['rho']=(f(x0)-r['f_trial'])/(-r['model_change']);assert abs(r['rho']-1)<1e-12;rows.append(r)
neg=record(np.diag([-2.,4.]),np.array([1.,2.]),1.)
hard=record(np.diag([-2.,4.]),np.array([0.,1.]),1.)
# Outer educational exact solve: quadratic model = objective exactly.
x=x0.copy();D=1.;outer=[]
for k in range(10):
 if np.linalg.norm(grad(x))<1e-8:break
 gg=grad(x);p,lam=solve_tr(H,gg,D);rho=(f(x)-f(x+p))/(-(gg@p+.5*p@H@p));boundary=abs(np.linalg.norm(p)-D)<1e-8
 outer.append({'k':k,'x':x.tolist(),'delta':D,'lambda':float(lam),'p':p.tolist(),'rho':float(rho)});x+=p
 if rho>.75 and boundary:D=min(2*D,1000.)
assert k==3 and np.linalg.norm(x-[1,-2])<1e-12
runs={}
for name,fn,gn,hn,start in [('quadratic',f,grad,lambda x:H,x0),('rosenbrock',lambda x:float((1-x[0])**2+100*(x[1]-x[0]**2)**2),lambda x:np.array([-2*(1-x[0])-400*x[0]*(x[1]-x[0]**2),200*(x[1]-x[0]**2)]),lambda x:np.array([[1200*x[0]**2-400*x[1]+2,-400*x[0]],[-400*x[0],200]]),[-1.2,1.])]:
 counter=[0]
 def hc(x):counter[0]+=1;return hn(x)
 r=minimize(fn,start,jac=gn,hess=hc,method='trust-exact',options={'gtol':1e-8,'initial_trust_radius':1.,'max_trust_radius':1000.,'eta':.15,'maxiter':300,'subproblem_maxiter':25})
 runs[name]={'x':r.x.tolist(),'fun':float(r.fun),'gradient_2':float(np.linalg.norm(gn(r.x))),'nit':int(r.nit),'nfev':int(r.nfev),'njev':int(r.njev),'nhev':int(r.nhev),'actual_hessian_calls':counter[0],'success':bool(r.success)}
 assert r.success
# Four steps from ONE fixed point (not an outer optimization path).
fig,ax=plt.subplots(1,2,figsize=(12,5.8),layout='constrained',gridspec_kw={'width_ratios':[1.25,1]})
xx,yy=np.meshgrid(np.linspace(-6.1,6.1,300),np.linspace(-6.1,6.1,300));qq=6*xx+200*yy+xx**2+20*yy**2
ax[0].contour(xx,yy,qq,levels=[-508,-495,-450,-350,-180,0,200,700],colors='#d5dde6',linewidths=.7)
cols=['#2563eb','#d97706','#0f766e','#9333ea'];angles=np.linspace(0,2*np.pi,400)
for row,col in zip(rows,cols):
 D=row['delta'];p=np.array(row['p']);ax[0].plot(D*np.cos(angles),D*np.sin(angles),c=col,lw=1,alpha=.5);ax[0].annotate('',xy=p,xytext=(0,0),arrowprops={'arrowstyle':'->','color':col,'lw':2.5});ax[0].plot(*p,'o',color=col,ms=5,label=f'Δ={D:.3g}, λ={row["lambda"]:.3g}')
ax[0].plot(-3,-5,'*',c='#9333ea',ms=14);ax[0].set(aspect='equal',xlabel='step p_x',ylabel='step p_y',title='同じ点から 半径だけを変えた一歩',xlim=(-6.1,6.1),ylim=(-6.1,6.1));ax[0].legend(loc='upper right',fontsize=9)
Ds=np.linspace(.5,6.1,160);ps=np.array([solve_tr(H,g,D)[0] for D in Ds]);ax[1].plot(Ds,ps[:,0],color='#2563eb',label='p_x = −6/(2+λ)');ax[1].plot(Ds,ps[:,1],color='#0f766e',label='p_y = −200/(40+λ)');ax[1].axvline(np.sqrt(34),ls='--',color='#9333ea',label='Newton方向が収まる √34');ax[1].set(xlabel='信頼半径 Δ',ylabel='一歩の各成分',title='成分ごとの縮め方が異なる');ax[1].legend(loc='lower left',fontsize=10)
fig.suptitle('trust-exact  半径を変えると 一歩の向きも変わる',fontsize=16);fig.savefig(OUT/'main.png',dpi=160);fig.savefig(OUT/'main.svg');plt.close(fig)
result={'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'fixed_point_exact_subproblems':rows,'negative_curvature_not_eigenvector':neg,'hard_case':hard,'educational_outer_trace':outer,'scipy_trust_exact':runs,'distinction':'Educational eigen/secular solver is not SciPy trust-exact; SciPy uses shifted Cholesky iterations and approximate stopping.'}
(OUT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
