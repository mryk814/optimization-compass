from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np, scipy, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})
f=lambda x:float((x[0]-1)**2+(x[1]-2)**2)
c=lambda x:float(1-np.dot(x,x))
h=lambda x:float(x[0]+x[1]-.5)
center=np.array([.2,.8]);points=np.array([center,center+[.2,0],center+[0,.2]])
A=np.c_[np.ones(3),points-center]
fc=np.linalg.solve(A,np.array([f(x) for x in points]));cc=np.linalg.solve(A,np.array([c(x) for x in points]))
normal=-cc[1:];radius=.5
sp=cc[0]*normal/(normal@normal);perp=np.array([normal[1],-normal[0]])/np.linalg.norm(normal)
s=sp+np.sqrt(radius**2-sp@sp)*perp
candidate=center+s
assert np.allclose(fc,[2.08,-1.4,-2.2]);assert np.allclose(cc,[.32,-.6,-1.8])
assert abs(cc[0]+cc[1:]@s)<1e-12 and c(candidate)<-.14
from scipy.optimize import minimize
# Independent constrained solve checks the geometry used above, not COBYLA internals.
sub=minimize(lambda z:fc[0]+fc[1:]@z,[0,0],method='SLSQP',constraints=[{'type':'ineq','fun':lambda z:cc[0]+cc[1:]@z},{'type':'ineq','fun':lambda z:radius**2-z@z}],options={'ftol':1e-12})
assert np.linalg.norm(s-sub.x)<1e-6
ledger=[]
def counted(x):
 ledger.append({'x':x.tolist(),'f':f(x),'violation':max(0,-c(x),-h(x))});return f(x)
r=minimize(counted,[.2,.4],method='COBYLA',constraints=[{'type':'ineq','fun':c},{'type':'ineq','fun':h}],options={'rhobeg':.5,'tol':1e-7,'catol':1e-8,'maxiter':3000})
opt=np.array([1,2])/np.sqrt(5);opt_f=(np.sqrt(5)-1)**2
assert np.linalg.norm(r.x-opt)<1e-4;assert max(0,-c(r.x),-h(r.x))<=1e-8;assert len(ledger)==r.nfev
fig,ax=plt.subplots(1,2,figsize=(12,5.6),layout='constrained')
t=np.linspace(0,2*np.pi,500)
u=np.linspace(-.4,1.3,200);v=np.linspace(.05,1.55,200);X,Y=np.meshgrid(u,v)
ax[0].contour(X,Y,(X-1)**2+(Y-2)**2,levels=[.8,1.2,1.6,2.08,2.5,3],colors='#d7dde6')
ax[0].plot(np.cos(t),np.sin(t),color='#168879',lw=2,label='真の円境界')
ax[0].plot(center[0]+radius*np.cos(t),center[1]+radius*np.sin(t),'--',color='#2f5b95',label='教材の信頼領域')
line=(cc[0]-.6*(u-center[0]))/1.8+center[1]
ax[0].plot(u,line,color='#a45db1',label='線形モデルの境界')
ax[0].scatter(points[:,0],points[:,1],color='#18334f',s=55,zorder=5,label='補間3点')
ax[0].scatter(*candidate,color='#bf543b',marker='X',s=100,zorder=6,label='モデル上の候補')
ax[0].annotate('',xy=candidate,xytext=center,arrowprops={'arrowstyle':'->','color':'#bf543b','lw':2})
ax[0].annotate('実制約では円の外',candidate,xytext=(12,-23),textcoords='offset points',fontsize=11)
ax[0].set(xlim=(-.35,1.3),ylim=(.05,1.5),xlabel='x1',ylabel='x2',title='説明用の一手（実装の内部履歴ではない）',aspect='equal')
ax[0].legend(loc='lower left',fontsize=9)
fv=np.array([a['f'] for a in ledger]);cv=np.array([a['violation'] for a in ledger]);feas=np.where(cv<=1e-8,fv,np.inf)
ax[1].plot(np.arange(1,len(fv)+1),np.minimum.accumulate(feas),color='#168879',label='許容差内の最良値')
ax[1].scatter(np.arange(1,len(fv)+1),fv,c=np.where(cv>1e-8,'#bf543b','#8497ae'),s=15,alpha=.7,label='各評価の目的値')
ax[1].axhline(opt_f,color='#18334f',ls='--',label=f'解析解 {opt_f:.6f}')
ax[1].set(xlabel='目的関数評価回数',ylabel='目的値',title='SciPy 1.17.0 COBYLA の実評価記録',ylim=(float(fv.min())-0.07,float(fv.max())+0.1))
ax[1].legend(fontsize=10)
fig.suptitle('線形制約モデルを満たすことと、真の制約を満たすことは別',fontsize=15)
for ext in ['svg','png']:fig.savefig(MEDIA/f'cobyla-model-feasibility.{ext}',dpi=170)
report={'numpy':np.__version__,'scipy':scipy.__version__,'educational_model':{'center':center.tolist(),'points':points.tolist(),'f_coefficients':fc.tolist(),'c_coefficients':cc.tolist(),'radius':radius,'candidate':candidate.tolist(),'predicted_f':float(fc[0]+fc[1:]@s),'actual_f':f(candidate),'predicted_c':float(cc[0]+cc[1:]@s),'actual_c':c(candidate),'subproblem_oracle_error':float(np.linalg.norm(s-sub.x))},'scipy_result':{'x':r.x.tolist(),'fun':float(r.fun),'maxcv':float(r.maxcv),'success':bool(r.success),'nfev':int(r.nfev),'message':r.message},'oracle':{'x':opt.tolist(),'f':opt_f},'ledger':ledger,'tests':'passed'}
(OUT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='ledger'},ensure_ascii=False,indent=2))
