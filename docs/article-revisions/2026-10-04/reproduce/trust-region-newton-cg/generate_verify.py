"""Independent Steihaug trace, checked against SciPy 1.17.0 trust-ncg."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-curvature-mpl')
import pathlib,json,sys
import numpy as np,scipy
from scipy.optimize import minimize
from scipy.optimize._trustregion_ncg import CGSteihaugSubproblem
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
OUT=pathlib.Path(__file__).resolve().parent

def f(x):return float((1-x[0])**2+20*(x[1]-x[0]**2)**2)
def grad(x):return np.array([2*(x[0]-1)-80*x[0]*(x[1]-x[0]**2),40*(x[1]-x[0]**2)])
def hess(x):return np.array([[2-80*x[1]+240*x[0]**2,-80*x[0]],[-80*x[0],40.]])
def hp(x,v):return np.array([(2-80*x[1]+240*x[0]**2)*v[0]-80*x[0]*v[1],-80*x[0]*v[0]+40*v[1]])
def roots(z,d,D):
 a=d@d;b=z@d;c=z@z-D*D;s=np.sqrt(b*b-a*c)
 # Stable quadratic roots, sorted.
 aux=b+np.copysign(s,b); t1=-aux/a;t2=c/(-aux) if aux!=0 else s/a
 return sorted([float(t1),float(t2)])
def steihaug(g,H,D):
 z=np.zeros_like(g);r=g.copy();d=-r;tol=min(.5,np.sqrt(np.linalg.norm(g)))*np.linalg.norm(g);logs=[]
 if np.linalg.norm(g)==0:return z,'zero_gradient',logs
 for j in range(20*len(g)):
  Hd=H@d;curv=d@Hd
  logs.append({'j':j,'z':z.tolist(),'r_norm':float(np.linalg.norm(r)),'d_curvature':float(curv)})
  if curv<=0:
   t1,t2=roots(z,d,D);a=z+t1*d;b=z+t2*d;q=lambda p:g@p+.5*p@H@p
   p=a if q(a)<q(b) else b
   return p,'negative_curvature',logs
  a=(r@r)/curv;zn=z+a*d
  if np.linalg.norm(zn)>=D:
   t=roots(z,d,D)[1];return z+t*d,'boundary',logs
  rn=r+a*Hd
  if np.linalg.norm(rn)<tol:return zn,'residual',logs
  d=-rn+(rn@rn)/(r@r)*d;z,r=zn,rn
 raise RuntimeError('inner limit')
x=np.array([-1.2,1.]);D=1.;rows=[];path=[x.copy()]
for k in range(300):
 if np.linalg.norm(grad(x))<1e-8:break
 g=grad(x);H=hess(x);p,reason,inner=steihaug(g,H,D)
 # Compare every candidate against installed SciPy's internal solver.
 sub=CGSteihaugSubproblem(x,f,grad,None,hp);sp,sbound=sub.solve(D)
 assert np.allclose(p,sp,rtol=1e-9,atol=1e-10)
 pred=-(g@p+.5*p@H@p);actual=f(x)-f(x+p);rho=actual/pred;accepted=rho>.15;boundary=reason in ['boundary','negative_curvature'];Dn=D
 if rho<.25:Dn=.25*D
 elif rho>.75 and boundary:Dn=min(2*D,1000.)
 xn=x+p if accepted else x.copy()
 rows.append({'k':k,'x':x.tolist(),'f':f(x),'g_norm':float(np.linalg.norm(g)),'delta':D,'p':p.tolist(),'p_norm':float(np.linalg.norm(p)),'trial_x':(x+p).tolist(),'predicted_reduction':float(pred),'actual_reduction':float(actual),'rho':float(rho),'accepted':bool(accepted),'delta_next':Dn,'inner_reason':reason,'inner_cg_steps':len(inner),'inner_trace':inner,'next_x':xn.tolist()})
 if not accepted:assert np.array_equal(x,xn)
 assert np.linalg.norm(p)<=D+1e-10
 x,D=xn,Dn;path.append(x.copy())
count=[0];scipy_path=[np.array([-1.2,1.])]
def counted(x,v):count[0]+=1;return hp(x,v)
r=minimize(f,scipy_path[0],jac=grad,hessp=counted,method='trust-ncg',options={'gtol':1e-8,'maxiter':300,'initial_trust_radius':1.,'max_trust_radius':1000.,'eta':.15},callback=lambda xk:scipy_path.append(xk.copy()))
assert r.success and len(path)==len(scipy_path) and np.allclose(path,scipy_path,atol=1e-9,rtol=1e-8)
# All 3 interior reasons have independent deterministic branch tests.
tests=[]
for name,H,g,D in [('residual',np.eye(2),np.array([1.,0.]),2.),('boundary',np.eye(2),np.array([1.,0.]),.25),('negative_curvature',np.diag([-1.,2.]),np.array([1.,0.]),1.)]:
 p,reason,logs=steihaug(g,H,D);assert reason==name
 tests.append({'expected':name,'actual':reason,'p':p.tolist(),'residual_norm':float(np.linalg.norm(H@p+g)),'norm_p':float(np.linalg.norm(p)),'delta':D})
rng=np.random.default_rng(41);err=[]
for x in rng.normal(size=(8,2)):
 for v in rng.normal(size=(3,2)):err.append(np.linalg.norm(hp(x,v)-hess(x)@v))
assert max(err)<1e-10
fig,ax=plt.subplots(1,2,figsize=(12,5.8),layout='constrained',gridspec_kw={'width_ratios':[1,1.25]})
xx,yy=np.meshgrid(np.linspace(-1.5,-.4,300),np.linspace(-.1,1.5,300));zz=(1-xx)**2+20*(yy-xx**2)**2
ax[0].contour(xx,yy,zz,levels=[2.5,3,4,6,10,20,40,80],colors='#cbd5e1',linewidths=.8)
pts=np.array(path[:6]);ax[0].plot(pts[:,0],pts[:,1],'o-',c='#0f766e',lw=2,label='採用された点')
row=rows[2];trial=np.array(row['trial_x']);base=np.array(row['x']);ax[0].plot([base[0],trial[0]],[base[1],trial[1]],'--',c='#c2410c',label='k=2 棄却された候補');ax[0].plot(*trial,'x',ms=10,c='#c2410c',mew=2)
ax[0].annotate('同じ点から再試行',base,xytext=(-100,38),textcoords='offset points',arrowprops={'arrowstyle':'->','color':'#64748b'},fontsize=10)
ax[0].set(xlabel='x',ylabel='y',title='棄却では現在点を動かさない');ax[0].legend(loc='lower left',fontsize=9)
# First five attempts, reduced data shared with table.
inds=np.arange(5);pred=[s['predicted_reduction'] for s in rows[:5]];actual=[s['actual_reduction'] for s in rows[:5]]
ax[1].bar(inds-.18,pred,.34,color='#64748b',label='モデルの予測減少');ax[1].bar(inds+.18,actual,.34,color=['#0f766e' if s['accepted'] else '#c2410c' for s in rows[:5]],label='実際の減少');ax[1].axhline(0,c='#64748b',lw=.8)
ax[1].set(xticks=inds,xticklabels=[f'k={s["k"]}\nΔ={s["delta"]:g}\nρ={s["rho"]:.2f}' for s in rows[:5]],ylabel='目的値の減少（負なら増加）',title='予測と実際を照合して 半径を直す',ylim=(-.7,5.1));ax[1].legend(loc='upper right',fontsize=9)
fig.suptitle('trust-ncg  CGの打切りと 一歩の採否は別の判断',fontsize=16);fig.savefig(OUT/'main.png',dpi=160);fig.savefig(OUT/'main.svg');plt.close(fig)
result={'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'trace':rows,'branch_tests':tests,'hvp_matrix_max_error':float(max(err)),'scipy_trust_ncg':{'nit':int(r.nit),'nfev':int(r.nfev),'njev':int(r.njev),'nhev_reported':int(r.nhev),'actual_hvp_calls':count[0],'success':bool(r.success),'x':r.x.tolist(),'fun':float(r.fun),'gradient_2':float(np.linalg.norm(grad(r.x))),'path_max_error':float(np.max(np.abs(np.array(path)-np.array(scipy_path))))},'distinction':'Independent teaching Steihaug trace, candidates checked against SciPy private subproblem and path checked against public minimize API.'}
(OUT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'first_five':rows[:5],'branch_tests':tests,'scipy':result['scipy_trust_ncg']},ensure_ascii=False,indent=2))
