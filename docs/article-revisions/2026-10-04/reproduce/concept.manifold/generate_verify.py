from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent
MEDIA=ROOT/'site/public/media'; MEDIA.mkdir(parents=True,exist_ok=True)
x=np.array([1.,0.]); g=np.array([.2,-1.]); eta=.5
tangent=g-x*(x@g); xi=-eta*tangent
y=x-eta*g; z=x+xi; r=z/np.linalg.norm(z); projected=y/np.linalg.norm(y)
assert abs(x@tangent)<1e-15
assert abs(np.linalg.norm(r)-1)<1e-15
exp=np.cos(np.linalg.norm(xi))*x+np.sin(np.linalg.norm(xi))*xi/np.linalg.norm(xi)
errors=[]
for h in [1e-2,1e-3,1e-4]:
 r_h=(x+h*xi)/np.linalg.norm(x+h*xi)
 errors.append(float(np.linalg.norm((r_h-x)/h-xi)))
assert all(errors[i+1]<.11*errors[i] for i in range(2))
theta=np.linspace(-np.pi,np.pi,400001); circle=np.c_[np.cos(theta),np.sin(theta)]
# Independent grid oracle for nearest point to y, with resolution error allowance.
assert np.min(np.linalg.norm(circle-y,axis=1)) >= np.linalg.norm(projected-y)-1e-10
fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
for ax in axes:
 ax.plot(np.cos(theta[::300]),np.sin(theta[::300]),color='#8aa8b4',lw=2)
 ax.axhline(0,color='#cbd5df',lw=.7);ax.axvline(0,color='#cbd5df',lw=.7)
 ax.set_aspect('equal');ax.set_xlim(-.25,1.5);ax.set_ylim(-.35,1.15);ax.set_xlabel('$x_1$');ax.set_ylabel('$x_2$')
 ax.scatter(*x,c='#22354b',s=45,zorder=5);ax.annotate('$x=(1,0)$',x,xytext=(8,-20),textcoords='offset points')
axes[0].plot([1,1],[-.2,1],ls='--',c='#87949e',label='接線 $x_1=1$')
axes[0].annotate('',z,x,arrowprops=dict(arrowstyle='->',color='#d47a1f',lw=2))
axes[0].scatter(*z,color='#d47a1f',s=50);axes[0].annotate('$x+\\xi=(1,0.5)$',z,xytext=(9,6),textcoords='offset points')
axes[0].plot([0,z[0]],[0,z[1]],ls=':',c='#658e86');axes[0].scatter(*r,c='#128174',s=55,zorder=6)
axes[0].annotate('$R_x(\\xi)$',r,xytext=(-78,20),textcoords='offset points',arrowprops=dict(arrowstyle='-',color='#128174'))
axes[0].set_title('① 接方向へ動き、正規化で円へ戻す',pad=15);axes[0].legend(loc='upper left')
axes[1].scatter(*y,c='#d47a1f',s=50,label='周囲の勾配の候補 $y$')
axes[1].scatter(*projected,c='#bf4c58',s=50,label='$y$ の最近点')
axes[1].scatter(*r,c='#128174',s=55,label='接方向からのレトラクション')
axes[1].annotate('',y,x,arrowprops=dict(arrowstyle='->',color='#d47a1f',lw=2))
axes[1].plot([0,y[0]],[0,y[1]],ls=':',c='#bf4c58')
axes[1].set_title('② 同じ正規化でも、入力候補が違う',pad=15);axes[1].legend(loc='upper left',fontsize=9)
fig.suptitle('単位円の一歩：接空間への射影と、円への写像を分ける',fontsize=16)
for ext in ('svg','png'):fig.savefig(MEDIA/f'manifold-circle-step.{ext}',dpi=160)
result={'point':x.tolist(),'ambient_gradient':g.tolist(),'tangent_gradient':tangent.tolist(),'tangent_step':xi.tolist(),'ambient_candidate':y.tolist(),'ambient_candidate_norm':float(np.linalg.norm(y)),'tangent_candidate_norm':float(np.linalg.norm(z)),'retracted':r.tolist(),'projected_ambient_candidate':projected.tolist(),'exponential':exp.tolist(),'cost_before':float(g@x),'cost_after':float(g@r),'local_derivative_errors':errors,'unit_residual':float(abs(np.linalg.norm(r)-1)),'tangent_residual':float(abs(x@tangent))}
(ROOT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,indent=2))
