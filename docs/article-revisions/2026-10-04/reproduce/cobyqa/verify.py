from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np,scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.optimize import minimize,Bounds,LinearConstraint
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})
f=lambda x:float((x[0]-1)**2+2*(x[1]+.5)**2)
ledger=[]
def counted(x):ledger.append({'x':x.tolist(),'f':f(x),'violation':max(0.,-sum(x),max(-2-x),max(x-2))});return f(x)
r=minimize(counted,[.5,.5],method='COBYQA',bounds=Bounds([-2,-2],[2,2]),constraints=[LinearConstraint([[1,1]],[0],[np.inf])],options={'initial_tr_radius':1.,'final_tr_radius':1e-6,'feasibility_tol':1e-8,'maxfev':1000,'maxiter':2000,'scale':False})
p=np.array([a['x'] for a in ledger[:5]]);z=np.array([a['f'] for a in ledger[:5]]);center=np.array([.5,.5]);s=p-center
A=np.c_[np.ones(5),s[:,0],s[:,1],s[:,0]**2,s[:,1]**2]
coef=np.linalg.solve(A,z)
assert np.allclose(p,[[.5,.5],[1.5,.5],[.5,1.5],[-.5,.5],[.5,-.5]])
assert np.allclose(coef,[2.25,-1,4,1,2]);assert np.allclose(z,[2.25,2.25,8.25,4.25,.25]);assert r.fun<1e-20 and r.maxcv==0
assert len(ledger)==r.nfev and all(a['violation']==0 for a in ledger)
q=np.array([.75,-.25]);ss=q-center;prediction=coef@np.r_[1,ss,ss**2]
assert abs(prediction-f(q))<1e-12
fig,axes=plt.subplots(1,3,figsize=(14,4.8),layout='constrained')
u=np.linspace(-1.1,2,260);v=np.linspace(-1.3,2,260);X,Y=np.meshgrid(u,v);Z=(X-1)**2+2*(Y+.5)**2
ax=axes[0];ax.contour(X,Y,Z,levels=[.25,1,2.25,4,8],colors='#ccd7e3');ax.plot(u,-u,'--',color='#aa677e',label='x1+x2=0')
ax.scatter(p[:,0],p[:,1],color='#2f5b95',s=45,zorder=3)
for i,pt in enumerate(p):ax.annotate(f'{i+1}: {z[i]:.2f}',pt,xytext=(7,6),textcoords='offset points',fontsize=10)
ax.scatter(1,-.5,marker='*',s=150,color='#168879',label='解析的な最小点')
ax.set(xlim=(-1,2),ylim=(-1.2,2),xlabel='x1',ylabel='x2',title='実評価の最初の5点',aspect='equal');ax.legend(loc='upper left',fontsize=9)
ax=axes[1];t=np.linspace(-1,1,250);ax.plot(t,2.25-t+t*t,color='#168879',lw=2,label='二次モデル＝真の断面')
ax.plot(t,2.25-t,'--',color='#bf543b',label='線形部分だけ')
ax.scatter([-1,0,1],[4.25,2.25,2.25],color='#2f5b95',s=50,zorder=4)
ax.set(xlabel='s1 = x1 − 0.5（x2 = 0.5）',ylabel='目的値',title='両側を測ると曲率が分かる');ax.legend(fontsize=9)
ax=axes[2];fv=np.array([a['f'] for a in ledger]);ax.plot(np.arange(1,len(fv)+1),fv,'o',ms=4,color='#94a5ba',label='各評価の値')
ax.step(np.arange(1,len(fv)+1),np.minimum.accumulate(fv),where='post',color='#168879',label='それまでの最良値')
ax.set(xlabel='目的関数評価回数',ylabel='目的値',title='改善しない評価もモデル材料');ax.legend(fontsize=9)
fig.suptitle('COBYQA  |  評価履歴から二次モデルが持つ情報を読む',fontsize=15)
for ext in ['svg','png']:fig.savefig(MEDIA/f'cobyqa-interpolation.{ext}',dpi=170)
report={'numpy':np.__version__,'scipy':scipy.__version__,'scipy_result':{'x':r.x.tolist(),'fun':float(r.fun),'nfev':r.nfev,'nit':r.nit,'maxcv':float(r.maxcv),'success':bool(r.success),'message':r.message},'educational_model':{'basis':['1','s1','s2','s1^2','s2^2'],'coefficients':coef.tolist(),'rank':int(np.linalg.matrix_rank(A)),'cross_term_identified':False,'test_point':q.tolist(),'predicted_f':float(prediction),'true_f':f(q),'full_quadratic_counterexample':'add alpha*s1*s2: same five interpolation values'},'ledger':ledger,'oracle':{'x':[1,-.5],'f':0},'tests':'passed'}
(OUT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='ledger'},ensure_ascii=False,indent=2))
