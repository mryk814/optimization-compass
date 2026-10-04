"""Analytic scalarization, scaled objectives, endpoints and SciPy checks."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/discrete-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/discrete-cache')
from pathlib import Path
from fractions import Fraction as F
import json,platform,numpy as np,scipy
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).resolve().parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':font.get_name(),'font.size':11,'svg.fonttype':'path'})
def vals(x):return np.array([(x[0]-1)**2+x[1]**2,x[0]**2+(x[1]-1)**2])
def solve(w,scale=1):
 a=scale*w;b=1-w;alpha=a/(a+b);x=np.array([alpha,1-alpha])
 def obj(z):return a*vals(z)[0]+b*vals(z)[1]
 def jac(z):return 2*(a+b)*z-2*np.array([a,b])
 r=minimize(obj,np.array([.5,.5]),jac=jac,method='BFGS',options={'gtol':1e-10})
 assert r.success and np.linalg.norm(r.x-x)<1e-9
 assert np.linalg.norm(jac(x))<1e-11
 return {'w':w,'scale_f1':scale,'effective_weight':alpha,'x':x.tolist(),'f_original':vals(x).tolist(),'scipy_x':r.x.tolist(),'scipy_success':bool(r.success),'gradient_norm':float(np.linalg.norm(jac(x)))}
rows=[solve(w) for w in [0,.2,.5,.8,1]];scaled=solve(.5,100);compensated=solve(1/101,100)
assert np.allclose(compensated['x'],[.5,.5]);assert scaled['effective_weight']==100/101
# Existing concept's concave frontier y=(t,1-t^2), t in [0,1].
# Its midpoint loses to at least one endpoint for every weight.
weights=np.linspace(0,1,1001)
assert np.all(.5*weights+.75*(1-weights)>np.minimum(weights,1-weights))
fig,(ax,ay)=plt.subplots(1,2,figsize=(11.8,5),layout='constrained');u=np.linspace(0,1,501)
ax.plot(u,1-u,c='#3b8c7c',lw=2);ay.plot(2*(1-u)**2,2*u**2,c='#3b8c7c',lw=2)
colors=['#387ca4','#c88a35','#8564a1']
for w,col in zip([.2,.5,.8],colors):
 x=[w,1-w];v=vals(x);ax.scatter(*x,c=col,s=70,zorder=4);ay.scatter(*v,c=col,s=70,zorder=4)
 ax.annotate(f'w = {w}',xy=x,xytext=(8,10),textcoords='offset points',color=col)
 ay.annotate(f'w = {w}',xy=v,xytext=(8,9),textcoords='offset points',color=col)
 t=np.linspace(0,2,150);level=w*v[0]+(1-w)*v[1];line=(level-w*t)/(1-w);ay.plot(t,line,c=col,ls=':',alpha=.55)
xs=scaled['x'];vs=scaled['f_original'];ax.scatter(*xs,marker='D',c='#cc6948',s=70,zorder=4);ay.scatter(*vs,marker='D',c='#cc6948',s=70,zorder=4)
ax.annotate('f1を100倍、w=0.5\n(100/101, 1/101)',xy=xs,xytext=(.20,.10),arrowprops={'arrowstyle':'->','color':'#ad6047'},fontsize=10,color='#98513c')
ay.annotate('f1を100倍、w=0.5',xy=vs,xytext=(.55,1.9),arrowprops={'arrowstyle':'->','color':'#ad6047'},fontsize=10,color='#98513c')
ax.scatter([1,0],[0,1],marker='s',facecolors='none',edgecolors='#4a6977',s=50)
ax.set(xlim=(-.07,1.15),ylim=(-.06,1.1),xlabel='x1',ylabel='x2',title='決定空間：解は (w, 1−w)')
ay.set(xlim=(-.08,2.1),ylim=(-.08,2.1),xlabel='f1（元の単位）',ylabel='f2（元の単位）',title='目的空間：点と重み付き和の等値線')
for a in (ax,ay):a.grid(alpha=.15);a.set_axisbelow(True)
for ext in ['svg','png']:fig.savefig(P/f'weighted-sum-scale-and-solution.{ext}',dpi=180)
report={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'unscaled_runs':rows,'scale_100_weight_half':scaled,'scale_100_compensated_weight':compensated,'exact_scaled':{'x':['100/101','1/101'],'f1':'2/10201','f2':'20000/10201'},'existing_concave_frontier_counterexample':{'midpoint':[.5,.75],'weight_half_score':.625,'endpoint_best_score':.5,'1001_weight_grid_check':True,'analytical_reason':'Weighted objective is concave in t, with all strictly interior t worse than an endpoint for 0<=w<=1.'},'all_scalar_subproblems_are_strictly_convex':True}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'weights':[r['w'] for r in rows],'scaled':scaled,'compensated':compensated},ensure_ascii=False))
