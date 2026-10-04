"""Educational projected Krylov subproblems and separate SciPy GLTR run."""
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
# Explicit orthonormal basis for span{g,Hg}, built with counted products.
hvp_count=0
def counted_hvp(v):
 global hvp_count
 hvp_count+=1;return H@v
q1=g/np.linalg.norm(g);h1=counted_hvp(q1);u=h1-q1*(q1@h1);q2=u/np.linalg.norm(u);h2=counted_hvp(q2)
Q=np.column_stack([q1,q2]);HQ=np.column_stack([h1,h2]);T=Q.T@HQ
assert np.linalg.norm(Q.T@Q-np.eye(2))<1e-12 and np.linalg.norm(T-Q.T@H@Q)<1e-12
rows=[]
for D in [1.,4.]:
 for j in [1,2]:
  B=Q[:,:j];A=T[:j,:j];b=B.T@g;z,lam=solve_tr(A,b,D);p=B@z;res=H@p+g+lam*p
  row={'delta':D,'dimension':j,'basis_hvp_calls':j,'lambda':float(lam),'p':p.tolist(),'model_change':float(g@p+.5*p@H@p),'trial_f':f(x0+p),'norm_p':float(np.linalg.norm(p)),'reduced_kkt_residual':float(np.linalg.norm(B.T@res)),'full_kkt_residual':float(np.linalg.norm(res)),'Q':B.tolist(),'T':A.tolist()}
  assert row['norm_p']<=D+1e-10 and row['reduced_kkt_residual']<1e-10
  if j==2:assert row['full_kkt_residual']<1e-10
  rows.append(row)
assert rows[1]['model_change']<=rows[0]['model_change'] and rows[3]['model_change']<=rows[2]['model_change']
# Invariant 1-D space can miss a negative eigenvector: this is a toy space,
# NOT a claim that trlib never augments invariant subspaces.
HH=np.diag([2.,-1.]);gg=np.array([1.,0.]);pp,ll=solve_tr(HH,gg,1.);restricted=np.array([-.5,0.])
blind={'H_diagonal':[2.,-1.],'g':[1.,0.],'restricted_p':restricted.tolist(),'restricted_model':float(gg@restricted+.5*restricted@HH@restricted),'global_p':pp.tolist(),'global_model':float(gg@pp+.5*pp@HH@pp),'lambda':float(ll)}
assert blind['global_model']<blind['restricted_model']
def rosen(x):return float((1-x[0])**2+100*(x[1]-x[0]**2)**2)
def rg(x):return np.array([-2*(1-x[0])-400*x[0]*(x[1]-x[0]**2),200*(x[1]-x[0]**2)])
def rhp(x,v):return np.array([(1200*x[0]**2-400*x[1]+2)*v[0]-400*x[0]*v[1],-400*x[0]*v[0]+200*v[1]])
runs={}
for name,fn,gn,hn,start in [('quadratic',f,grad,lambda x,v:H@v,x0),('rosenbrock',rosen,rg,rhp,[-1.2,1.])]:
 for inexact in [True,False]:
  count=[0]
  def hp(x,v):count[0]+=1;return hn(x,v)
  r=minimize(fn,start,jac=gn,hessp=hp,method='trust-krylov',options={'gtol':1e-8,'initial_trust_radius':1.,'max_trust_radius':1000.,'eta':.15,'inexact':inexact,'maxiter':300})
  runs[name+'_inexact_'+str(inexact)]={'x':r.x.tolist(),'fun':float(r.fun),'gradient_2':float(np.linalg.norm(gn(r.x))),'nit':int(r.nit),'nfev':int(r.nfev),'njev':int(r.njev),'nhev_reported':int(r.nhev),'actual_hvp_calls':count[0],'success':bool(r.success),'message':str(r.message)}
  assert r.success
fig,ax=plt.subplots(1,2,figsize=(12,5.8),layout='constrained')
for a,D in zip(ax,[1.,4.]):
 xx,yy=np.meshgrid(np.linspace(-1.13*D,1.13*D,300),np.linspace(-1.13*D,1.13*D,300));qq=6*xx+200*yy+xx**2+20*yy**2
 a.contour(xx,yy,qq,levels=12,colors='#d3dce7',linewidths=.6);t=np.linspace(0,2*np.pi,400);a.plot(D*np.cos(t),D*np.sin(t),c='#64748b',lw=1.4)
 line=np.array([-D*q1,D*q1]);a.plot(line[:,0],line[:,1],'--',color='#2563eb',lw=1.6,label='j=1 の探索空間 span{g}')
 subset=[r for r in rows if r['delta']==D]
 for row,col,marker in zip(subset,['#2563eb','#0f766e'],['o','s']):
  p=np.array(row['p']);a.annotate('',xy=p,xytext=(0,0),arrowprops={'arrowstyle':'->','color':col,'lw':2.5});a.plot(*p,marker,color=col,ms=8,label=f'j={row["dimension"]}   q(p)={row["model_change"]:.3f}')
 a.set(aspect='equal',xlabel='step p_x',ylabel='step p_y',title=f'半径 Δ={D:g}  残せる方向を1本から2本へ',xlim=(-1.13*D,1.13*D),ylim=(-1.13*D,1.13*D));a.legend(loc='upper left',fontsize=9)
 # An inset resolves the close endpoints without moving their true coordinates.
 ins=a.inset_axes([.59,.08,.37,.28]);p1=np.array(subset[0]['p']);p2=np.array(subset[1]['p']);marginx=.01 if D==1 else .07;marginy=.0005 if D==1 else .008
 ins.plot([p1[0],p2[0]],[p1[1],p2[1]],':',color='#94a3b8');ins.plot(*p1,'o',c='#2563eb');ins.plot(*p2,'s',c='#0f766e');ins.set_xlim(min(p1[0],p2[0])-marginx,max(p1[0],p2[0])+marginx);ins.set_ylim(min(p1[1],p2[1])-marginy,max(p1[1],p2[1])+marginy);ins.tick_params(labelsize=7);ins.set_title('候補点の拡大',fontsize=8)
fig.suptitle('trust-krylov  狭い探索空間で解くと 何を取り逃がすか',fontsize=16);fig.savefig(OUT/'main.png',dpi=160);fig.savefig(OUT/'main.svg');plt.close(fig)
result={'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'projected_subproblems':rows,'basis_construction_total_hvp':hvp_count,'orthogonality_error':float(np.linalg.norm(Q.T@Q-np.eye(2))),'invariant_subspace_counterexample':blind,'scipy_trust_krylov':runs,'distinction':'Explicit projection/eigen solver is educational, not trlib or SciPy trust-krylov.'}
(OUT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
