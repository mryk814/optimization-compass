from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent;s=(P/'sqp.md').read_text();exec(re.search(r'```python\n(.*?)```',s,re.S).group(1))
assert result.success and abs(constraint(result.x))<1e-8
assert np.allclose(result.x,(1-1/np.sqrt(2))*np.ones(2))
x=np.array([1.5,1.5]);mu=0.;rows=[]
for k in range(5):
 p,nu=qp_step(x,mu);a=constraint_gradient(x);B=2*(1+mu)*np.eye(2)
 assert np.linalg.norm(B@p+gradient(x)+nu*a)<1e-12
 lin=constraint(x)+a@p;assert lin<1e-12 and nu>=0 and abs(nu*lin)<1e-12
 rows.append(dict(k=k,x=x.tolist(),p=p.tolist(),g=constraint(x),linearized=float(lin),multiplier=nu));x=x+p;mu=nu
merit=[]
for alpha in [0,1,.5]:
 x=np.array([1.5,1.5])+alpha*np.array([-1.5,-1.5]);f=objective(x);v=max(0.,constraint(x));merit.append(dict(alpha=alpha,f=f,violation=v,phi1=f+v,phi10=f+10*v))
assert merit[1]['phi1']<merit[0]['phi1'] and merit[1]['phi10']>merit[0]['phi10']
(P/'verified-numbers.json').write_text(json.dumps(dict(rows=rows,merit=merit),indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(1,2,figsize=(10.6,5.6),layout='constrained');fig.set_facecolor('#faf9f5')
angle=np.linspace(0,2*np.pi,500)
for i,ax in enumerate(axs):
 ax.set_facecolor('#faf9f5');ax.fill(1+np.cos(angle),1+np.sin(angle),color='#158078',alpha=.13,label='本当の円盤');ax.plot(1+np.cos(angle),1+np.sin(angle),c='#158078',lw=2)
 if i==0:
  v=np.linspace(-.3,2.5,100);ax.plot(v,3.5-v,'--',c='#d28a39',lw=2,label='線形化境界 v1+v2=3.5');x=np.array([1.5,1.5]);trial=np.array([0.,0.]);lim=(-.3,2.5)
 else:
  v=np.linspace(-.1,.8,100);ax.plot(v,.5-v,'--',c='#d28a39',lw=2,label='線形化境界 v1+v2=0.5');x=np.array([0.,0.]);trial=np.array([.25,.25]);lim=(-.1,.8)
 ax.scatter(*x,c='#365467',s=60);ax.scatter(*trial,c='#bb684c',s=60);ax.annotate('',trial,x,arrowprops={'arrowstyle':'->','color':'#365467','lw':2})
 ax.annotate('現在点',x,xytext=(x[0]+.06,x[1]-.06),fontsize=10);ax.annotate('QPの候補',trial,xytext=(trial[0]+.05,trial[1]+.06),fontsize=10)
 ax.set(xlim=lim,ylim=lim,xlabel='候補点 v1',ylabel='候補点 v2',title='最初の線形化' if i==0 else '次の線形化（原点の近くを拡大）');ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12);ax.legend(fontsize=9,loc='upper left')
fig.suptitle('SQP：近似した制約を守っても、本物の制約は破ることがある',fontsize=14)
fig.savefig(P/'media/sqp-linearization-gap.svg',bbox_inches='tight');fig.savefig(P/'media/sqp-linearization-gap.png',dpi=130,bbox_inches='tight')
print('PASS: article SLSQP, five independently checked QP KKT systems, merit acceptance comparison')
